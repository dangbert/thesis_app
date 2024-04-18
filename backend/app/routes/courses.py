from fastapi import APIRouter, HTTPException
from app.deps import SessionDep
from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
from uuid import UUID

router = APIRouter()


def get_course_or_fail(course_id: UUID, session: SessionDep) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


### courses
@router.get("/")
async def list_courses(session: SessionDep) -> list[CoursePublic]:
    courses = session.query(Course).all()
    return [course.to_public() for course in courses]


@router.get("/{course_id}")
async def get_course(course_id: UUID, session: SessionDep) -> CoursePublic:
    return get_course_or_fail(course_id, session).to_public()


@router.put("/", status_code=201)
async def create_course(body: CourseCreate, session: SessionDep) -> CoursePublic:
    course = Course(name=body.name, about=body.about)
    session.add(course)
    session.commit()
    return course.to_public()


### assignments
@router.get("/{course_id}/assignment")
async def list_assignments(
    course_id: UUID, session: SessionDep
) -> list[AssignmentPublic]:
    course = get_course_or_fail(course_id, session)
    assignments = course.assignments
    return [a.to_public() for a in assignments]


@router.get("/{course_id}/assignment/{assignment_id}")
async def get_assignment(
    course_id: UUID, assignment_id: UUID, session: SessionDep
) -> AssignmentPublic:
    get_course_or_fail(course_id, session).to_public()
    a1 = (
        session.query(Assignment)
        .filter_by(course_id=course_id, id=assignment_id)
        .first()
    )
    if not a1:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return a1.to_public()


@router.put("/{course_id}/assignment", status_code=201)
async def create_assignment(
    course_id: UUID, body: AssignmentCreate, session: SessionDep
) -> AssignmentPublic:
    get_course_or_fail(course_id, session).to_public()
    assignment = Assignment(name=body.name, about=body.about, course_id=course_id)
    session.add(assignment)
    session.commit()
    return assignment.to_public()
