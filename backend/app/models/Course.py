from app.models.Base import Base
from app.models.User import User
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


# class RoleEnum()


class Assignment(Base):
    __tablename__ = "assignment"
    course_id: Mapped[PUUID] = mapped_column(
        PUUID(as_uuid=True), ForeignKey("course.id"), nullable=False
    )
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, nullable=False, default="")

    course: Mapped["Course"] = relationship("Course", back_populates="assignments")
