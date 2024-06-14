#!/usr/bin/env python3
"""
Utilities for exporting data from the pilot study to an xlsx.
"""

import app.database as database
import app.models as models
from app.settings import get_settings
from sqlalchemy.orm import close_all_sessions
from typing import Tuple
from uuid import UUID
import pandas as pd
from app.hardcoded import SMARTData, FeedbackData, EvalMetrics

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
    with open(PILOT_EMAILS_PATH, "r") as f:
        ALLOWED_EMAILS = [line.strip() for line in f.readlines()]

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

        # get all attempts
        attempts = (
            session.query(models.Attempt)
            .filter(models.Attempt.user_id.in_(USER_IDS))
            .all()
        )

        a1_attempts = [x for x in attempts if x.assignment_id == A1.id]
        a2_attempts = [x for x in attempts if x.assignment_id == A2.id]

        a1_df = pd.DataFrame([attempt_to_dict(x) for x in a1_attempts])
        a2_df = pd.DataFrame([attempt_to_dict(x) for x in a2_attempts])

        fname = "pilot.xlsx"
        with pd.ExcelWriter(fname) as writer:
            a1_df.to_excel(writer, sheet_name="P1")
            a2_df.to_excel(writer, sheet_name="S1")

        print(f"wrote '{fname}'")


## for each assignment:
def attempt_to_dict(att: models.Attempt):
    feedbacks = sorted(att.feedbacks, key=lambda x: x.created_at)
    human_feedbacks = [x for x in feedbacks if not x.is_ai]
    ai_feedbacks = [x for x in feedbacks if x.is_ai]

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
    if hf_data.review_secs:
        review_secs = hf_data.review_secs
    else:
        review_secs = hf.data.get("review_secs", None)

    obj = {
        "attempt_id": att.id,
        "attempt_goal": smart_data.goal,
        "attempt_plan": smart_data.plan,
        "ai_feedback": af_data.feedback if af_data is not None else None,
        "human_feedback": hf_data.feedback,
        "approved": hf_data.approved,
        "review_rating": hf_data.eval_metrics.rating if hf_data.eval_metrics else None,
        "review_problems": hf_data.eval_metrics.problems
        if hf_data.eval_metrics
        else None,
        "review_secs": review_secs,
    }
    return obj


if __name__ == "__main__":
    main()
