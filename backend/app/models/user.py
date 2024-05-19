from app.models.base import Base
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, Session
from typing import Optional
import secrets
from uuid import UUID
from app.models.schemas import UserPublic, Auth0UserInfo
from config import get_logger
from typing import Union

logger = get_logger(__name__)


class User(Base):
    __tablename__ = "user"
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str]
    sub: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # from Auth0
    # TODO: deprecate email_verified, the social loging with Auth0 handles this implicitly
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_token: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True, default=lambda: secrets.token_urlsafe(16)
    )

    def to_public(self) -> "UserPublic":
        return UserPublic(
            id=self.id,
            sub=self.sub,
            name=self.name,
            email=self.email,
            **super().to_public().model_dump(),
        )

    def can_view(
        self,
        session: Session,
        obj: Union["Course", "Assignment", "Attempt", "Feedback", "File"],
        edit: bool = False,
    ) -> bool:
        """Entry point for checking User acesss management."""
        if isinstance(obj, Course):
            return self._can_view_course(session, obj, edit)
        elif isinstance(obj, Assignment):
            return self._can_view_assignment(session, obj, edit)
        elif isinstance(obj, Attempt):
            return self._can_view_attempt(session, obj, edit)
        elif isinstance(obj, Feedback):
            return self._can_view_feedback(session, obj, edit)
        elif isinstance(obj, File):
            return self._can_view_file(session, obj, edit)
        else:
            raise ValueError(f"Unexpected object type: {type(obj)}")

    def _can_view_course(
        self, session: Session, course: "Course", edit: bool = False
    ) -> bool:
        link = (
            session.query(CourseUserLink)
            .filter_by(user_id=self.id, course_id=course.id)
            .first()
        )
        if not link:
            return False
        if edit:
            return link.role == CourseRole.TEACHER
        return link.role in {CourseRole.STUDENT, CourseRole.TEACHER}

    def _can_view_assignment(
        self, session: Session, assignment: "Assignment", edit: bool = False
    ) -> bool:
        return self._can_view_course(session, assignment.course, edit)

    def _can_view_attempt(
        self, session: Session, attempt: "Attempt", edit: bool = False
    ) -> bool:
        # attempt owners and course teachers can view
        if self.id == attempt.user_id:
            logger.debug(
                f"User {self.email} can view attempt {attempt}: due to ownership ({edit=})"
            )
            return True
        if self._can_view_assignment(session, attempt.assignment, edit=True):
            logger.debug(
                f"User {self.email} can view attempt {attempt}: due to assignment EDIT access ({edit=})"
            )
            return True
        return False

    def _can_view_feedback(
        self, session: Session, feedback: "Feedback", edit: bool = False
    ) -> bool:
        # attempt access implies feedback access
        if self._can_view_attempt(session, feedback.attempt, edit=edit):
            logger.debug(
                f"User {self.email} can view feedback {feedback}: due to attempt access ({edit=})"
            )
            return True
        return False

    def _can_view_file(
        self, session: Session, file: "File", edit: bool = False
    ) -> bool:
        if self.id == file.user_id:
            logger.debug(
                f"User {self.email} can view file {file}: due to ownership ({edit=})"
            )
            return True
        # these aren't necessarily efficient queries but sufficient for this project
        if True in [
            self._can_view_course(session, course, edit) for course in file.courses
        ]:
            logger.debug(
                f"User {self.email} can view file {file}: due to course access ({edit=})"
            )
        if True in [
            self._can_view_assignment(session, assignment, edit)
            for assignment in file.assignments
        ]:
            logger.debug(
                f"User {self.email} can view file {file}: due to assignment access ({edit=})"
            )

        if True in [
            self._can_view_attempt(session, attempt, edit) for attempt in file.attempts
        ]:
            logger.debug(
                f"User {self.email} can view file {file}: due to attempt access ({edit=})"
            )

        return False


# TODO: just combine all models into one file?
from app.models.course import (  # noqa: E402
    Course,
    CourseUserLink,
    CourseRole,
    Assignment,
    Attempt,
    Feedback,
    File,
)
