from app.models.base import Base
from app.models.user import User
from app.settings import get_settings
from app.models.schemas import (
    CourseRole,
    CourseCreate,
    CoursePublic,
    AssignmentCreate,
    AssignmentPublic,
    AttemptCreate,
    AttemptPublic,
    FilePublic,
    FeedbackPublic,
    AssignmentStudentStatus,
    AssignmentAttemptStatus,
)
from app.hardcoded import FeedbackData
from sqlalchemy import String, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PUUID
from uuid import UUID
import os
from typing import Optional, Any
import secrets
import enum


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
    files: Mapped[list["File"]] = relationship(
        "File",
        secondary="course_file",
        back_populates="courses",
        cascade="all, delete",
    )

    def to_public(
        self,
        your_role: Optional[CourseRole] = None,
        invite_role: Optional[CourseRole] = None,
        your_group: Optional[int] = None,
    ) -> CoursePublic:
        """
        Return a public representation of the course, including the user's role in it (if provided).
        Or including the potential role of a user who is invited to the course.
        """
        return CoursePublic(
            id=self.id,
            name=self.name,
            about=self.about,
            **super().to_public().model_dump(),
            your_role=your_role,
            invite_role=invite_role,
            your_group=your_group,
        )


class CourseUserLink(Base):
    __tablename__ = "course_user_link"
    course_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("course.id"),
    )
    user_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("user.id"),
    )
    role: Mapped[CourseRole]
    # group number of user within course
    group_num: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )

    course: Mapped["Course"] = relationship("Course")
    user: Mapped["User"] = relationship("User")


class Assignment(Base):
    __tablename__ = "assignment"
    course_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("course.id"),
    )
    name: Mapped[str]
    about: Mapped[str] = mapped_column(String, default="")
    scorable: Mapped[bool] = mapped_column(
        Boolean
    )  # whether assignment attempts should be assigned a score

    course: Mapped["Course"] = relationship("Course", back_populates="assignments")

    files: Mapped[list["File"]] = relationship(
        "File",
        secondary="assignment_file",
        back_populates="assignments",
        cascade="all, delete",
    )

    def to_public(self) -> AssignmentPublic:
        return AssignmentPublic(
            id=self.id,
            name=self.name,
            about=self.about,
            scorable=self.scorable,
            course_id=self.course_id,
            **super().to_public().model_dump(),
        )


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

    # for now, an attempt can only have one file
    file_id: Mapped[Optional[UUID]] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("file.id"),
    )

    files: Mapped[list["File"]] = relationship(
        "File", secondary="attempt_file", back_populates="attempts"
    )

    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        secondary="attempt_feedback",
        cascade="all, delete",
    )

    def to_public(self) -> AttemptPublic:
        feed_objs = [feed.to_public() for feed in self.feedbacks]
        feed_objs = sorted(feed_objs, key=lambda x: x.created_at)

        return AttemptPublic(
            id=self.id,
            assignment_id=self.assignment_id,
            user_id=self.user_id,
            data=self.data,
            feedbacks=feed_objs,
            files=[file.to_public() for file in self.files],
            status=self.describe_status(),
            **super().to_public().model_dump(),
        )

    def describe_status(self) -> AssignmentAttemptStatus:
        """
        Get the status of this attempt.
        Note: this is most relevant when called on the student's latest attempt.
        (Otherwise AWAITING_RESUBMISSION might be misleading)
        """
        teacher_feedbacks = sorted(
            [f for f in self.feedbacks if not f.is_ai], key=lambda x: x.created_at
        )
        ai_feedbacks = sorted(
            [f for f in self.feedbacks if f.is_ai], key=lambda x: x.created_at
        )

        if teacher_feedbacks:
            feedback = teacher_feedbacks[-1]
            feedback_data = FeedbackData(**feedback.data)
            if feedback_data.approved:
                return AssignmentAttemptStatus.COMPLETE
            else:
                return AssignmentAttemptStatus.RESUBMISSION_REQUESTED

        elif ai_feedbacks:
            return AssignmentAttemptStatus.AWAITING_TEACHER_FEEDBACK
        else:
            return AssignmentAttemptStatus.AWAITING_AI_FEEDBACK


class File(Base):
    __tablename__ = "file"
    filename: Mapped[str]
    user_id: Mapped[UUID] = mapped_column(PUUID(as_uuid=True), ForeignKey("user.id"))
    ext: Mapped[str]  # file extension

    user: Mapped["User"] = relationship("User")
    courses: Mapped[list["Course"]] = relationship(
        "Course",
        secondary="course_file",
        back_populates="files",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        secondary="assignment_file",
        back_populates="files",
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        "Attempt", secondary="attempt_file", back_populates="files"
    )

    def to_public(self) -> FilePublic:
        settings = get_settings()
        # read URL is the API endpoint to GET the file  e.g. "/api/v1/file/c773cf48-cf50-4a21-a8e0-863cca1c8e3b"
        # see backend/app/routes/files.py
        read_url = f"{settings.api_v1_str}/file/{self.id}"
        return FilePublic(
            id=self.id,
            filename=self.filename,
            read_url=read_url,
            **super().to_public().model_dump(),
        )

    @property
    def disk_path(self) -> str:
        settings = get_settings()
        return os.path.join(settings.file_dir, f"{self.id}.{self.ext}")


class AttemptFileLink(Base):
    __tablename__ = "attempt_file"
    attempt_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("attempt.id"),
    )
    file_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("file.id"),
    )


class AssignmentFileLink(Base):
    __tablename__ = "assignment_file"
    assignment_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("assignment.id"),
    )
    file_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("file.id"),
    )


class CourseFileLink(Base):
    __tablename__ = "course_file"
    course_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("course.id"),
    )
    file_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("file.id"),
    )


class Feedback(Base):
    __tablename__ = "feedback"
    attempt_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("attempt.id"),
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("user.id"),
    )
    is_ai: Mapped[bool]
    data: Mapped[dict[str, Any]] = mapped_column(JSON)

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="feedbacks")

    def to_public(self) -> FeedbackPublic:
        return FeedbackPublic(
            id=self.id,
            attempt_id=self.attempt_id,
            user_id=self.user_id,
            is_ai=self.is_ai,
            # TODO: note that we're returning the full FeedbackData object here (including eval metrics etc)
            data=self.data,
            **super().to_public().model_dump(),
        )


# TODO: I don't think this was necessary, Feedback.attempt_id should be sufficient by itself!
class AttemptFeedbackLink(Base):
    __tablename__ = "attempt_feedback"
    attempt_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("attempt.id"),
    )
    feedback_id: Mapped[UUID] = mapped_column(
        PUUID(as_uuid=True),
        ForeignKey("feedback.id"),
    )
