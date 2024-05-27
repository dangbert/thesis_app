from fastapi import APIRouter, HTTPException
from app.deps import SessionDep, AuthUserDep
from app.models import User
from app.models.course import (
    Course,
    CourseRole,
    CourseUserLink,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
    AssignmentStudentStatus,
    AssignmentAttemptStatus,
    Attempt,
)
from sqlalchemy import func
from config import get_logger

from uuid import UUID

logger = get_logger(__name__)
router = APIRouter()

COURSE_NOT_FOUND = "Course not found or unauthorized"
ASSIGNMENT_NOT_FOUND = "Assignment not found or unauthorized"


def get_course_or_fail(session: SessionDep, course_id: UUID, user: User) -> Course:
    """Get's a course by ID, or raises a 404 if it doesn't exist or the user doesn't have access."""
    course = session.get(Course, course_id)
    if not course or (course and not user.can_view(session, course)):
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)
    return course


def get_assignment_or_fail(
    session: SessionDep, assignment_id: UUID, user: User
) -> Assignment:
    """Get's an assignment by ID, or raises a 404 if it doesn't exist or the user doesn't have access."""
    a1 = session.query(Assignment).filter_by(id=assignment_id).first()
    if not a1 or (a1 and not user.can_view(session, a1)):
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    return a1


### courses
@router.get("/")
async def list_courses(user: AuthUserDep, session: SessionDep) -> list[CoursePublic]:
    links = session.query(CourseUserLink).filter_by(user_id=user.id).all()
    return [link.course.to_public() for link in links]


@router.get("/{course_id}")
async def get_course(
    user: AuthUserDep, course_id: UUID, session: SessionDep
) -> CoursePublic:
    course = session.get(Course, course_id)
    if not course or (course and not user.can_view(session, course)):
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
    return course.to_public()


@router.put("/", status_code=201)
async def create_course(body: CourseCreate, session: SessionDep) -> CoursePublic:
    course = Course(name=body.name, about=body.about)
    session.add(course)
    session.commit()
    return course.to_public()


### assignments
@router.get("/{course_id}/assignment")
async def list_assignments(
    user: AuthUserDep, course_id: UUID, session: SessionDep
) -> list[AssignmentPublic]:
    course = get_course_or_fail(session, course_id, user)
    # sort by oldest to newest
    assignments = sorted(course.assignments, key=lambda a: a.created_at)
    return [a.to_public() for a in assignments if user.can_view(session, a)]


@router.get("/{course_id}/assignment/{assignment_id}")
async def get_assignment(
    user: AuthUserDep, course_id: UUID, assignment_id: UUID, session: SessionDep
) -> AssignmentPublic:
    a1 = get_assignment_or_fail(session, assignment_id, user)
    if a1.course_id != course_id:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    return a1.to_public()


@router.put("/{course_id}/assignment", status_code=201)
async def create_assignment(
    user: AuthUserDep, course_id: UUID, body: AssignmentCreate, session: SessionDep
) -> AssignmentPublic:
    course = get_course_or_fail(session, course_id, user)
    if not user.can_view(session, course, edit=True):
        raise HTTPException(
            status_code=403, detail="you're unauthorized to create assignments"
        )
    assignment = Assignment(
        name=body.name, about=body.about, course_id=course_id, scorable=body.scorable
    )
    session.add(assignment)
    session.commit()
    return assignment.to_public()


@router.get("/{course_id}/assignment/{assignment_id}/status")
async def get_assignment_status(
    user: AuthUserDep, course_id: UUID, assignment_id: UUID, session: SessionDep
) -> list[AssignmentStudentStatus]:
    a1 = get_assignment_or_fail(session, assignment_id, user)
    course = get_course_or_fail(session, course_id, user)
    if not user.can_view(session, course, edit=True):
        raise HTTPException(
            status_code=403,
            detail="you're unauthorized to get this assignment's status",
        )
    if a1.course_id != course_id:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

    # get all users in course (including teachers)
    links = (
        session.query(CourseUserLink)
        .filter_by(course_id=course_id)
        .order_by(CourseUserLink.created_at.asc())
        .all()
    )
    users = [link.user for link in links]

    # res = session.query(Attempt).filter(Attempt.assignment_id == assignment_id, Attempt.user_id.in_([u.id for u in users])).group_by(Attempt.user_id).all()
    user_attempt_counts = (
        session.query(
            # results will be a tuple (UUID, int)
            Attempt.user_id,
            func.count(Attempt.id).label("attempt_count"),
        )
        .filter(
            Attempt.assignment_id == assignment_id,
            Attempt.user_id.in_([u.id for u in users]),
        )
        .group_by(Attempt.assignment_id, Attempt.user_id)
        .all()
    )

    # now we get the latest Attempt per user
    latest_attempt_subquery = (
        session.query(
            Attempt.user_id.label("user_id"),
            func.max(Attempt.created_at).label("last_attempt"),
        )
        .filter(
            Attempt.assignment_id == assignment_id,
            Attempt.user_id.in_([u.id for u in users]),
        )
        .group_by(Attempt.user_id)
        .subquery()
    )

    last_attempts = (
        session.query(Attempt)
        .join(
            latest_attempt_subquery,
            (Attempt.user_id == latest_attempt_subquery.c.user_id)
            & (Attempt.created_at == latest_attempt_subquery.c.last_attempt),
        )
        .all()
    )

    user_role_map = {link.user_id: link.role for link in links}
    user_attempt_count_map = {
        user_id: attempt_count for user_id, attempt_count in user_attempt_counts
    }
    user_last_attempt_map = {attempt.user_id: attempt for attempt in last_attempts}

    final_status = []
    for user in users:
        # TODO: handle other statuses
        cur = AssignmentStudentStatus(
            student=user.to_public(),
            # user role will always exist, but providing default for mypy
            role=user_role_map.get(user.id, CourseRole.STUDENT),
            attempt_count=user_attempt_count_map.get(user.id, 0),
            last_attempt_date=None,
        )
        status = (
            AssignmentAttemptStatus.NOT_STARTED
            if cur.attempt_count == 0
            else AssignmentAttemptStatus.AWAITING_FEEDBACK
        )
        cur.status = status
        last_attempt = user_last_attempt_map.get(user.id, None)
        if last_attempt:
            cur.last_attempt_date = last_attempt.created_at
        final_status.append(cur)

    logger.info(
        f"got assignment status for {len(final_status)} users in assignment {assignment_id}"
    )
    return final_status
