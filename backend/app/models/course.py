from app.models.base import Base
from app.models.user import User
from app.models.course_partials import (
    CourseCreate,
    CoursePublic,
    AssignmentCreate,
    AssignmentPublic,
    AttemptCreate,
    AttemptPublic,
)
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PUUID
from uuid import UUID
from typing import Optional, Any
import secrets


class Course(Base):
    __tablename__ = "course"
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, default="")
    invite_key: Mapped[str] = mapped_column(
        String, unique=True, default=lambda: secrets.token_urlsafe(16)
    )

    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="course",
        # if this course is deleted, automatically delete all its assignments
        cascade="all, delete-orphan",
    )

    def to_public(self) -> CoursePublic:
        return CoursePublic(id=self.id, name=self.name, about=self.about)


# class RoleEnum()


class Assignment(Base):
    __tablename__ = "assignment"
    course_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("course.id"),
    )
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, default="")

    course: Mapped["Course"] = relationship("Course", back_populates="assignments")

    def to_public(self) -> AssignmentPublic:
        return AssignmentPublic(id=self.id, name=self.name, about=self.about)


class Attempt(Base):
    __tablename__ = "attempt"
    assignment_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True), ForeignKey("assignment.id")
    )
    user_id: Mapped[UUID] = mapped_column(PUUID(as_uuid=True), ForeignKey("user.id"))
    # attempt data
    data: Mapped[dict[str, Any]] = mapped_column(JSON)

    assignment: Mapped["Assignment"] = relationship("Assignment")
    user: Mapped["User"] = relationship("User")

    def to_public(self) -> AttemptPublic:
        return AttemptPublic(
            id=self.id,
            assignment_id=self.assignment_id,
            user_id=self.user_id,
            data=self.data,
        )
