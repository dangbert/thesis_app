#!/usr/bin/env python3
"""
Utilities for exporting data from the pilot study to an xlsx.
"""

import os
import app.database as database
import app.models as models
from app.settings import get_settings
from sqlalchemy.orm import close_all_sessions
from typing import Tuple
from uuid import UUID
import pandas as pd
from app.hardcoded import SMARTData, FeedbackData, EvalMetrics
import random
from collections import defaultdict

from pydantic import EmailStr
from config import get_logger

settings = get_settings()
logger = get_logger(__name__)

# assignment IDs from the pilot study
P1_ID = UUID("22b3f6fe-d844-4caa-9b80-12ed523d9cf6")
S1_ID = UUID("4762034e-1a41-47d1-ad8d-65faa1771d57")


def main():
    # this script is meant to be run on a copy of the production database
    assert settings.db_name == "thesis_prod_copy"

    PILOT_EMAILS_PATH = "pilot_emails.txt"
    ALLOWED_EMAILS = _read_emails(PILOT_EMAILS_PATH)

    with database.SessionFactory() as session:
        users = (
            session.query(models.User)
            .filter(models.User.email.in_(ALLOWED_EMAILS))
            .all()
        )
        assert len(users) == len(ALLOWED_EMAILS)
        print(f"found {len(users)=}")

        USER_IDS = [u.id for u in users]

        # get 2 assignments
        A1 = session.query(models.Assignment).filter_by(id=P1_ID).first()
        A2 = session.query(models.Assignment).filter_by(id=S1_ID).first()

        assert None not in [A1, A2]

        # get all attempts (of opted in users)
        attempts = (
            session.query(models.Attempt)
            .filter(models.Attempt.user_id.in_(USER_IDS))
            .all()
        )

        a1_attempts = [x for x in attempts if x.assignment_id == A1.id]
        a2_attempts = [x for x in attempts if x.assignment_id == A2.id]

        a1_df = pd.DataFrame([attempt_to_dict(x) for x in a1_attempts])
        a2_df = pd.DataFrame([attempt_to_dict(x) for x in a2_attempts])

        all_df = get_anon_df(session)

        fname = "pilot.xlsx"
        with pd.ExcelWriter(fname) as writer:
            a1_df.to_excel(writer, sheet_name="P1", index=False)
            a2_df.to_excel(writer, sheet_name="S1", index=False)
            all_df.to_excel(writer, sheet_name="anon", index=False)

        print(f"wrote '{fname}'")


## for each assignment:
def attempt_to_dict(att: models.Attempt):
    human_feedbacks, ai_feedbacks = _split_feedbacks(att)

    if len(human_feedbacks) > 1:
        logger.warning(
            f"{len(human_feedbacks)} human feedbacks found for attempt {att.id}"
        )

    # get latest human feedback and ai feedback
    hf = human_feedbacks[-1] if len(human_feedbacks) > 0 else None
    af = ai_feedbacks[-1] if len(ai_feedbacks) > 0 else None
    assert hf is not None

    smart_data = SMARTData(**att.data)
    hf_data = FeedbackData(**hf.data)
    af_data = FeedbackData(**af.data) if af is not None else None

    # review_secs was stored wrong so we look twice
    review_secs = None
    if hf_data and hf_data.review_secs:
        review_secs = hf_data.review_secs
    else:
        review_secs = hf.data.get("review_secs", None)

    review_problems = None
    if (
        hf_data is not None
        and hf_data.eval_metrics is not None
        and hf_data.eval_metrics.problems is not None
    ):
        review_problems = ";".join(hf_data.eval_metrics.problems)
    obj = {
        "attempt_id": att.id,
        "attempt_goal": smart_data.goal,
        "attempt_plan": smart_data.plan,
        "ai_feedback": af_data.feedback if af_data is not None else None,
        "human_feedback": hf_data.feedback,
        "approved": hf_data.approved,
        "review_rating": hf_data.eval_metrics.rating if hf_data.eval_metrics else None,
        "review_problems": review_problems,
        "review_secs": review_secs,
    }
    return obj


def get_anon_df(session):
    """Get df of anonymous data for pilot study."""
    logger.info("constructing anonymous data df")
    attempts = (
        session.query(models.Attempt)
        .filter(models.Attempt.assignment_id.in_({P1_ID, S1_ID}))
        .all()
    )
    a1 = session.query(models.Assignment).filter(models.Assignment.id == P1_ID).first()
    a2 = session.query(models.Assignment).filter(models.Assignment.id == S1_ID).first()
    assert a1 and a2

    # optional list of test student account emails to skip
    SKIP_EMAILS_PATH = "pilot_skip_emails.txt"
    skip_emails = []
    if not os.path.isfile(SKIP_EMAILS_PATH):
        logger.warning(
            f"file '{SKIP_EMAILS_PATH}' not found, continuing without skip list"
        )
    else:
        skip_emails = _read_emails(SKIP_EMAILS_PATH)

    anon_data = []
    keep_cols = {"review_rating", "review_problems"}
    skipped = defaultdict(int)
    for att in attempts:
        is_teacher = True in [
            att.user.can_view(session, x, edit=True) for x in [a1, a2]
        ]
        if is_teacher:
            skipped["teacher_attempt"] += 1
            continue
        if att.user.email in skip_emails:
            skipped["skip_email"] += 1
            continue
        human_feedbacks, ai_feedbacks = _split_feedbacks(att)
        if len(human_feedbacks) == 0:
            skipped["no_human_feedback"] += 1
            continue  # only interested in attempts a human reviewed
        if len(ai_feedbacks) == 0:
            skipped["no_ai_feedback"] += 1
            continue  # e.g. student was in pilot_emails and AI feedback was not generated
        cur = attempt_to_dict(att)
        cur = {k: v for k, v in cur.items() if k in keep_cols}
        anon_data.append(cur)

    random.Random(42).shuffle(anon_data)  # shuffle into arbitrary order
    logger.info(
        f"attempt skip stats (note {len(attempts)} total attempts): {str(skipped)}"
    )
    logger.info(f"collected anonymous data with {len(anon_data)} attempts")
    return pd.DataFrame(anon_data)


def _split_feedbacks(att: models.Attempt) -> Tuple[list, list]:
    """Split feedbacks list into (human_feedbacks, ai_feedbacks)."""
    feedbacks = sorted(att.feedbacks, key=lambda x: x.created_at)
    human_feedbacks = [x for x in feedbacks if not x.is_ai]
    ai_feedbacks = [x for x in feedbacks if x.is_ai]
    return human_feedbacks, ai_feedbacks


def _read_emails(fname: str):
    with open(fname, "r") as f:
        emails = [line.strip() for line in f.readlines()]
        emails = [x for x in emails if not x.startswith("#")]
        for email in emails:
            # sanity check (throws exception if invalid)
            EmailStr._validate(email)  # type: ignore
    return emails


if __name__ == "__main__":
    main()
