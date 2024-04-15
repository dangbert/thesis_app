from app.models.Base import Base
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PUUID
from typing import Optional


class Course(Base):
    __tablename__ = "course"
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, nullable=False, default="")
    invite_key: Mapped[Optional[str]]


# class RoleEnum()


class Assignment(Base):
    __tablename__ = "assignment"
    course_id: Mapped[PUUID] = mapped_column(
        PUUID(as_uuid=True), ForeignKey("course.id"), nullable=False
    )
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, nullable=False, default="")
