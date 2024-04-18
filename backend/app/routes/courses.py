from fastapi import APIRouter, Depends, HTTPException
from app.deps import SessionDep
from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
from pydantic import BaseModel
from app.models.base import PUUID
from uuid import UUID

router = APIRouter()


### courses
@router.get("/")
async def list_courses(session: SessionDep) -> list[CoursePublic]:
    courses = session.query(Course).all()
    return [course.to_public() for course in courses]


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
    course = session.query(Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    assignments = course.assignments
    return [a.to_public() for a in assignments]


@router.put("/{course_id}/assignment", status_code=201)
async def create_assignment(
    course_id: UUID, body: AssignmentCreate, session: SessionDep
) -> AssignmentPublic:
    course = session.query(Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    assignment = Assignment(name=body.name, about=body.about, course_id=course_id)
    session.add(assignment)
    session.commit()
    return assignment.to_public()
