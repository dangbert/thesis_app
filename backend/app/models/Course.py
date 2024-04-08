from app.models.Base import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class Course(Base):
    __tablename__ = "course"
    name: Mapped[str] = mapped_column(String, nullable=False)
    about: Mapped[str] = mapped_column(String, nullable=False)
    invite_key: Mapped[str] = mapped_column(String, nullable=False)


# class RoleEnum()


class Assignment(Base):
    __tablename__ = "assignment"
    course_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    about: Mapped[str] = mapped_column(String, nullable=False)
