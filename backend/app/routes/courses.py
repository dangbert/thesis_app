from fastapi import APIRouter, HTTPException, Request
from app.deps import SessionDep, AuthUserDep, cur_user
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
from app.hardcoded import FeedbackData
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
    if not course or not user.can_view(session, course):
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
@router.get("/enroll_details", status_code=200)
async def get_enroll_details(
    invite_key: str, session: SessionDep, request: Request
) -> CoursePublic:
    """Get info about course given a valid invite key."""
    course = session.query(Course).filter_by(invite_key=invite_key).first()
    if not course:
        raise HTTPException(status_code=400, detail="invalid invite link")

    # check if user is logged in and already enrolled
    existing_role = None
    try:
        user = cur_user(request, session)
        existing_role = user.get_course_role(session, course.id)
    except HTTPException:
        pass

    invite_role = CourseRole.STUDENT  # TODO: support teacher invite_key
    return course.to_public(invite_role=invite_role, your_role=existing_role)


@router.post("/{course_id}/enroll_details", status_code=200)
async def set_enroll_details(
    user: AuthUserDep, course_id: UUID, group_num: int, session: SessionDep
) -> None:
    """Allow student to set their group number within a given course."""
    course = session.get(Course, course_id)
    if not course or not user.can_view(session, course):
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")

    cur_role = user.get_course_role(session, course_id)
    if not cur_role:
        raise HTTPException(
            status_code=403, detail="you're not enrolled in this course"
        )
    user.enroll(session, course, cur_role, group_num=group_num)


@router.get("/")
async def list_courses(user: AuthUserDep, session: SessionDep) -> list[CoursePublic]:
    links = session.query(CourseUserLink).filter_by(user_id=user.id).all()
    return [
        link.course.to_public(your_role=link.role, your_group=link.group_num)
        for link in links
    ]


@router.get("/{course_id}")
async def get_course(
    user: AuthUserDep, course_id: UUID, session: SessionDep
) -> CoursePublic:
    course = session.get(Course, course_id)
    link = user.get_course_link(session, course_id)
    if not course or not user.can_view(session, course) or not link:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
    return course.to_public(your_role=link.role, your_group=link.group_num)


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

    user_link_map = {link.user_id: link for link in links}
    user_attempt_count_map = {
        user_id: attempt_count for user_id, attempt_count in user_attempt_counts
    }
    user_last_attempt_map = {attempt.user_id: attempt for attempt in last_attempts}

    final_status = []
    for user in users:
        # TODO: handle other statuses
        last_attempt: Attempt | None = user_last_attempt_map.get(user.id, None)
        user_link = user_link_map.get(user.id)
        if not user_link:
            # user link will always exist, but providing default for mypy
            user_link = CourseUserLink(
                user_id=user.id,
                role=CourseRole.STUDENT,
                course_id=course_id,
                group_num=None,
            )

        # get score of latest teacher feedback (if any)
        score = None
        if last_attempt:
            teacher_feedbacks, _ = last_attempt.split_feedbacks()
            if teacher_feedbacks:
                latest_feedback = teacher_feedbacks[-1]
                fd = FeedbackData(**latest_feedback.data)
                score = fd.score

        cur = AssignmentStudentStatus(
            student=user.to_public(),
            role=user_link.role,
            group_num=user_link.group_num,
            attempt_count=user_attempt_count_map.get(user.id, 0),
            last_attempt_date=last_attempt.created_at if last_attempt else None,
            score=score,
        )
        if not last_attempt:
            cur.status = AssignmentAttemptStatus.NOT_STARTED
        else:
            cur.status = last_attempt.describe_status()
        final_status.append(cur)

    logger.info(
        f"constructed assignment status for {len(final_status)} users in assignment {assignment_id}"
    )
    return final_status
