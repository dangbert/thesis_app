from fastapi import APIRouter, HTTPException
from app.deps import SessionDep, AuthUserDep
from app.models import User
from app.models.course import (
    Course,
    CourseUserLink,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
from uuid import UUID

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
    return [a.to_public() for a in course.assignments if user.can_view(session, a)]


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
    assignment = Assignment(name=body.name, about=body.about, course_id=course_id)
    session.add(assignment)
    session.commit()
    return assignment.to_public()
