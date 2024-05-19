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
from typing import Any, Optional
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
    session = {"user": {"sub": user.sub, "name": user.name, "email": user.email}}
    # mirrors what starlette.middleware.sessions.SessionMiddleware does:
    session_data = base64.b64encode(json.dumps(session).encode())
    signer = itsdangerous.TimestampSigner(settings.secret_key)
    cookie_data = signer.sign(session_data).decode()
    client.cookies.set("session", cookie_data)


def logout_user(client: TestClient):
    client.cookies.clear()


def make_user(
    session: Session, email: str = "testuser@vu.nl", name: str = "Jane van Doe"
) -> User:
    sub = f"auth0|{str(hash(email))}"
    user = User(email=email, name=name, sub=sub)
    session.add(user)
    session.commit()
    return user


def enroll_as(session: Session, user: User, course: Course, role: Optional[CourseRole]):
    """
    Enroll given user in course with a given role.
    Removes user access if role is None.
    """

    link = (
        session.query(CourseUserLink)
        .filter_by(user_id=user.id, course_id=course.id)
        .first()
    )
    if link and not role:
        session.delete(link)
        session.commit()
        return

    if link is None:
        link = CourseUserLink(user_id=user.id, course_id=course.id, role=role)
        session.add(link)
        session.commit()
        return

    assert role is not None  # helps mypy
    link.role = role
    session.commit()


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


def make_file(
    session: Session,
    user_id: UUID,
    filename: str = "dummyfile.txt",
    ext: str = ".txt",
    content: bytes = b"dummy file :)",
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
    return file
