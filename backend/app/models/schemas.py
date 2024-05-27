"""
Pydantic models (and enums) for partial representations of SQLAlchemy models.
Must match frontend/apps/frontend/models.ts
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Any, Optional
import enum


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


class CourseRole(enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"


class CourseCreate(BaseModel):
    name: str
    about: str


class CoursePublic(CourseCreate, DateFields):
    """Public representation of a course to return via API."""

    id: UUID
    your_role: Optional[CourseRole] = None


class AssignmentCreate(BaseModel):
    name: str
    about: str
    scorable: bool


class AssignmentPublic(AssignmentCreate, DateFields):
    id: UUID
    course_id: UUID


class AttemptCreate(BaseModel):
    assignment_id: UUID
    data: dict[str, Any]
    file_ids: list[UUID]


class AttemptPublic(DateFields):
    id: UUID
    assignment_id: UUID
    user_id: UUID
    data: dict[str, Any]
    feedbacks: list["FeedbackPublic"]
    files: list["FilePublic"]


class AssignmentAttemptStatus(enum.Enum):
    """Enum for the status of a student's attempt(s) on an assignment."""

    NOT_STARTED = "not started"
    AWAITING_FEEDBACK = "awaiting feedback"
    AWAITING_RESUBMISSION = "awaiting resubmission"
    COMPLETE = "complete"


class AssignmentStudentStatus(BaseModel):
    """Represents a single student's status on completing a particular assignment."""

    student: UserPublic
    role: CourseRole
    attempt_count: int = 0
    last_attempt_date: Optional[datetime] = None
    status: AssignmentAttemptStatus = AssignmentAttemptStatus.NOT_STARTED


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
