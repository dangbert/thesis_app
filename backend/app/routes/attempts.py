from fastapi import APIRouter, HTTPException
from app.deps import SessionDep
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
)
from app.hardcoded import SMARTData
from uuid import UUID
from pydantic import ValidationError

router = APIRouter()


def get_assignment_or_fail(assignment_id: UUID, session: SessionDep) -> Assignment:
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.get("/")
async def list_attempts(
    assignment_id: UUID, session: SessionDep
) -> list[AttemptPublic]:
    get_assignment_or_fail(assignment_id, session)
    attempts = (
        session.query(Attempt)
        .filter_by(assignment_id=assignment_id)
        .order_by(Attempt.created_at.desc())
        .all()
    )
    return [attempt.to_public() for attempt in attempts]


@router.get("/{attempt_id}")
async def get_attempt(attempt_id: UUID, session: SessionDep) -> AttemptPublic:
    attempt = session.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt.to_public()


@router.put("/", status_code=201)
async def create_attempt(
    assignment_id: UUID, body: AttemptCreate, session: SessionDep
) -> AttemptPublic:
    get_assignment_or_fail(assignment_id, session)
    try:
        smart_data = SMARTData(**body.data)  # verify this format
    except ValidationError:
        raise HTTPException(
            status_code=400, detail="Data format not in SMARTData format"
        )

    attempt = Attempt(
        assignment_id=assignment_id, user_id=body.user_id, data=smart_data.model_dump()
    )
    session.add(attempt)
    session.commit()
    return attempt.to_public()
