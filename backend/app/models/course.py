from app.models.base import Base
from app.models.user import User
from app.models.course_partials import (
    CourseCreate,
    CoursePublic,
    AssignmentCreate,
    AssignmentPublic,
)
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PUUID
from typing import Optional
import secrets


class Course(Base):
    __tablename__ = "course"
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, nullable=False, default="")
    invite_key: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, default=lambda: secrets.token_urlsafe(16)
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
    course_id: Mapped[PUUID] = mapped_column(
        PUUID(as_uuid=True), ForeignKey("course.id"), nullable=False
    )
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, nullable=False, default="")

    course: Mapped["Course"] = relationship("Course", back_populates="assignments")

    def to_public(self) -> AssignmentPublic:
        return AssignmentPublic(id=self.id, name=self.name, about=self.about)
