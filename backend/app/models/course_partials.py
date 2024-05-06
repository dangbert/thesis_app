"""
Pydantic models for partial representations of course-related SQLAlchemy models.
Must match frontend/apps/frontend/models.ts
"""

from uuid import UUID
from pydantic import BaseModel
from typing import Any


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


class AttemptCreate(BaseModel):
    assignment_id: UUID
    user_id: UUID
    data: dict[str, Any]


class AttemptPublic(AttemptCreate):
    id: UUID


class FilePublic(BaseModel):
    id: UUID
    name: str
    read_url: str
