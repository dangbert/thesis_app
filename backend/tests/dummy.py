"""Utilities for creating/using dummy data for testing."""

from fastapi.testclient import TestClient
import app.models as models
from app.models import (
    User,
    Course,
    CourseRole,
    Assignment,
    Attempt,
    File,
    CourseUserLink,
)
from app.hardcoded import SMARTData, FeedbackData
from app.settings import get_settings
from sqlalchemy.orm import Session
from uuid import UUID
import base64
import json
from typing import Any, Optional, Tuple
import itsdangerous
import httpx


DUMMY_ID = UUID("cc2d7ce4-170f-4817-b4a9-76e11d5f9c56")

settings = get_settings()


def assert_not_authenticated(res: httpx.Response):
    assert isinstance(res, httpx.Response)
    assert res.status_code == 401
    assert res.json()["detail"] == "Not authenticated"


def login_user(client: TestClient, user: models.User):
    """Helper function to get a session cookie on the client."""
    logout_user(client)  # clear any existing session
    session = {"user": {"sub": user.sub, "name": user.name, "email": user.email}}
    # mirrors what starlette.middleware.sessions.SessionMiddleware does:
    session_data = base64.b64encode(json.dumps(session).encode())
    signer = itsdangerous.TimestampSigner(settings.secret_key)
    cookie_data = signer.sign(session_data).decode()
    client.cookies.set("session", cookie_data)


def logout_user(client: TestClient):
    client.cookies.clear()


def init_simple_course(session) -> Tuple[Course, Assignment, User, User]:
    """Create a single course, assignment, student, and teacher."""
    course = make_course(session)
    assignment = make_assignment(session, course.id, "assignment1")
    student = make_user(session, email="student1@example.com")
    teacher = make_user(session, email="teacher1@example.com")
    student.enroll(session, course, CourseRole.STUDENT)
    teacher.enroll(session, course, CourseRole.TEACHER)
    return course, assignment, student, teacher


def make_user(
    session: Session, email: str = "testuser@vu.nl", name: str = "Jane van Doe"
) -> User:
    sub = f"auth0|{str(hash(email))}"
    user = User(email=email, name=name, sub=sub)
    session.add(user)
    session.commit()
    return user


def make_course(session: Session, name="Test Course") -> Course:
    course = Course(name=name)
    session.add(course)
    session.commit()
    return course


def make_assignment(
    session: Session, course_id: UUID, name="Test Assignment"
) -> Assignment:
    assignment = Assignment(course_id=course_id, name=name)
    session.add(assignment)
    session.commit()
    return assignment


example_smart_data = SMARTData(goal="test goal", plan="test plan")
example_feedback_data = FeedbackData(
    feedback="good start, but try again", approved=False
)


def make_attempt(
    session: Session,
    assignment_id: UUID,
    user_id: UUID,
    data: Optional[dict[str, Any]] = None,
) -> Attempt:
    if data is None:
        data = example_smart_data.model_dump()
    attempt = Attempt(assignment_id=assignment_id, user_id=user_id, data=data)
    session.add(attempt)
    session.commit()
    return attempt


def make_feedback(
    session: Session,
    attempt_id: UUID,
    data: Optional[dict[str, Any]] = None,
    user_id: Optional[UUID] = None,
) -> models.Feedback:
    if data is None:
        data = example_feedback_data.model_dump()
    feedback = models.Feedback(
        attempt_id=attempt_id,
        user_id=user_id,
        is_ai=user_id is None,
        data=data,
    )
    session.add(feedback)
    session.commit()
    return feedback


def make_file(
    session: Session,
    user_id: UUID,
    filename: str = "dummyfile.txt",
    ext: str = ".txt",
    content: bytes = b"dummy file :)",
    attempt_id: Optional[UUID] = None,
) -> File:
    file = File(
        filename=filename,
        ext=ext,
        user_id=user_id,
    )
    session.add(file)
    session.commit()
    with open(file.disk_path, "wb") as f:
        f.write(content)

    if attempt_id is not None:
        file_link = models.AttemptFileLink(attempt_id=attempt_id, file_id=file.id)
        session.add(file_link)
        session.commit()
    return file
