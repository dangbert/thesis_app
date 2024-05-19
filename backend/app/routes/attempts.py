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
    AttemptFeedbackLink,
    FeedbackPublic,
    Feedback,
)
from app.routes.courses import get_assignment_or_fail
from app.hardcoded import SMARTData, FeedbackData
from uuid import UUID
from pydantic import ValidationError

router = APIRouter()

ATTEMPT_NOT_FOUND = "Attempt not found or unauthorized"


def get_attempt_or_fail(session: SessionDep, attempt_id: UUID, user: User) -> Attempt:
    attempt = session.get(Attempt, attempt_id)
    if not attempt or (attempt and not user.can_view(session, attempt)):
        raise HTTPException(status_code=404, detail=ATTEMPT_NOT_FOUND)
    return attempt


@router.get("/")
async def list_attempts(
    user: AuthUserDep, assignment_id: UUID, session: SessionDep
) -> list[AttemptPublic]:
    get_assignment_or_fail(session, assignment_id, user)
    attempts = (
        session.query(Attempt)
        .filter_by(assignment_id=assignment_id)
        .order_by(Attempt.created_at.desc())
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

    attempt = Attempt(
        assignment_id=assignment_id, user_id=user.id, data=smart_data.model_dump()
    )
    session.add(attempt)
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
