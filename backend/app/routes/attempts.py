from fastapi import APIRouter, HTTPException
from app.deps import SessionDep, AuthUserDep
from app.models.schemas import FeedbackCreate
from app.models import User
from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
    Attempt,
    AttemptCreate,
    AttemptPublic,
    AttemptFileLink,
    AttemptFeedbackLink,
    FeedbackPublic,
    Feedback,
)
import json
from app.models.job import Job, AI_FEEDBACK_JOB_DATA, JobStatus, JobType
from app.routes.courses import get_assignment_or_fail
from app.routes.files import get_files_or_fail
from app.hardcoded import SMARTData, FeedbackData
from uuid import UUID
from pydantic import ValidationError
from typing import Optional

router = APIRouter()

ATTEMPT_NOT_FOUND = "Attempt not found or unauthorized"


def get_attempt_or_fail(session: SessionDep, attempt_id: UUID, user: User) -> Attempt:
    attempt = session.get(Attempt, attempt_id)
    if not attempt or (attempt and not user.can_view(session, attempt)):
        raise HTTPException(status_code=404, detail=ATTEMPT_NOT_FOUND)
    return attempt


@router.get("/")
async def list_attempts(
    session: SessionDep,
    user: AuthUserDep,
    assignment_id: UUID,
    user_id: Optional[UUID] = None,
) -> list[AttemptPublic]:
    """
    List assignment attempts made by current user (or a provided user if requested by the teacher).
    Attempts are ordered from oldest to newest.
    """
    as1 = get_assignment_or_fail(session, assignment_id, user)
    if (
        user_id is not None
        and user_id != user.id
        and not user.can_view(session, as1, edit=True)
    ):
        raise HTTPException(
            status_code=403, detail="You are not allowed to view other users' attempts"
        )

    user_id = user_id or user.id
    attempts = (
        session.query(Attempt)
        .filter(Attempt.assignment_id == assignment_id, Attempt.user_id == user_id)
        .order_by(Attempt.created_at.asc())
        .all()
    )
    return [
        attempt.to_public() for attempt in attempts if user.can_view(session, attempt)
    ]


@router.get("/{attempt_id}")
async def get_attempt(
    user: AuthUserDep, attempt_id: UUID, session: SessionDep
) -> AttemptPublic:
    attempt = get_attempt_or_fail(session, attempt_id, user)
    return attempt.to_public()


@router.put("/", status_code=201)
async def create_attempt(
    user: AuthUserDep, assignment_id: UUID, body: AttemptCreate, session: SessionDep
) -> AttemptPublic:
    get_assignment_or_fail(session, assignment_id, user)
    try:
        smart_data = SMARTData(**body.data)
    except ValidationError:
        raise HTTPException(
            status_code=400, detail="Data format not in SMARTData format"
        )

    files = get_files_or_fail(session, body.file_ids, user, error_code=400)
    attempt = Attempt(
        assignment_id=assignment_id, user_id=user.id, data=smart_data.model_dump()
    )
    session.add(attempt)
    session.flush()  # to get ID

    # add files to attempt
    for file in files:
        session.add(AttemptFileLink(attempt_id=attempt.id, file_id=file.id))

    # create AI feedback job
    job = build_feedback_job_for_attempt(attempt.id)
    session.add(job)
    session.commit()
    return attempt.to_public()


@router.put("/{attempt_id}/feedback", status_code=201)
async def create_feedback(
    user: AuthUserDep, attempt_id: UUID, body: FeedbackCreate, session: SessionDep
) -> FeedbackPublic:
    attempt = session.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    try:
        FeedbackData(**body.data)
    except ValidationError:
        raise HTTPException(
            status_code=400, detail="Feedback data provided in incorrect format"
        )

    feedback = Feedback(
        attempt_id=attempt_id, user_id=user.id, is_ai=False, data=body.data
    )
    session.add(feedback)
    session.flush()  # to get ID
    session.add(AttemptFeedbackLink(attempt_id=attempt.id, feedback_id=feedback.id))
    session.commit()
    return feedback.to_public()


def build_feedback_job_for_attempt(attempt_id: UUID):
    job_data = AI_FEEDBACK_JOB_DATA(attempt_id=attempt_id)
    job = Job(
        job_type=JobType.AI_FEEDBACK,
        data=job_data.custom_dump_dict(),
    )
    return job
