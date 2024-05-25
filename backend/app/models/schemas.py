"""
Pydantic models for partial representations of SQLAlchemy models.
Must match frontend/apps/frontend/models.ts
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Any, Optional


class DateFields(BaseModel):
    """Date columns common to all models (see base.py)."""

    created_at: datetime
    updated_at: Optional[datetime]


class Auth0UserInfo(BaseModel):
    """
    Schema for user info returned by Auth0 upon login.
    https://auth0.com/docs/api/authentication#user-profile
    """

    sub: str
    name: str
    email: EmailStr


class UserPublic(Auth0UserInfo, DateFields):
    id: UUID


class CourseCreate(BaseModel):
    name: str
    about: str


class CoursePublic(CourseCreate, DateFields):
    """Public representation of a course to return via API."""

    id: UUID


class AssignmentCreate(BaseModel):
    name: str
    about: str
    scorable: bool


class AssignmentPublic(AssignmentCreate, DateFields):
    id: UUID


class AttemptCreate(BaseModel):
    assignment_id: UUID
    data: dict[str, Any]


class AttemptPublic(AttemptCreate, DateFields):
    id: UUID
    user_id: UUID
    feedback: list["FeedbackPublic"]
    files: list["FilePublic"]


class FilePublic(DateFields):
    id: UUID
    filename: str
    read_url: str


class FeedbackCreate(BaseModel):
    attempt_id: UUID
    data: dict[str, Any]


class FeedbackPublic(DateFields):
    id: UUID
    attempt_id: UUID
    user_id: Optional[UUID]
    is_ai: bool
    data: dict[str, Any]
