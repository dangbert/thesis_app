from uuid import UUID
from pydantic import BaseModel


class CourseCreate(BaseModel):
    name: str
    about: str


class CoursePublic(CourseCreate):
    """Public representation of a course to return via API."""

    id: UUID


class AssignmentCreate(BaseModel):
    name: str
    about: str


class AssignmentPublic(AssignmentCreate):
    id: UUID
