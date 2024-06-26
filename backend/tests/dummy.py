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
    AttemptFeedbackLink,
)
from app.models.job import AI_FEEDBACK_JOB_DATA
from app.hardcoded import SMARTData, FeedbackData
from app.settings import get_settings
from sqlalchemy.orm import Session
from uuid import UUID
import base64
import json
from typing import Any, Optional, Tuple
import itsdangerous
import httpx
import pytest_mock


DUMMY_ID = UUID("cc2d7ce4-170f-4817-b4a9-76e11d5f9c56")
EXAMPLE_SMART_DATA = SMARTData(goal="test goal", plan="test plan")
EXAMPLE_UNAPPROVED_FEEDBACK = FeedbackData(
    feedback="good start, but try again", approved=False
)
EXAMPLE_APPROVED_FEEDBACK = FeedbackData(feedback="well done!", approved=True)
EXAMPLE_AI_FEEDBACK_DATA = AI_FEEDBACK_JOB_DATA(attempt_id=DUMMY_ID)


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
    """Create a single course, assignment, teacher, and student."""
    course = make_course(session)
    assignment = make_assignment(session, course.id, "assignment1")
    teacher = make_user(session, email="teacher1@example.com")
    student = make_user(session, email="student1@example.com")
    teacher.enroll(session, course, CourseRole.TEACHER)
    student.enroll(session, course, CourseRole.STUDENT)
    return course, assignment, teacher, student


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
    session: Session, course_id: UUID, name="Test Assignment", scorable: bool = False
) -> Assignment:
    assignment = Assignment(course_id=course_id, name=name, scorable=scorable)
    session.add(assignment)
    session.commit()
    return assignment


def make_attempt(
    session: Session,
    assignment_id: UUID,
    user_id: UUID,
    data: Optional[dict[str, Any]] = None,
) -> Attempt:
    if data is None:
        data = EXAMPLE_SMART_DATA.model_dump()
    attempt = Attempt(assignment_id=assignment_id, user_id=user_id, data=data)
    session.add(attempt)
    session.commit()
    return attempt


def make_feedback(
    session: Session,
    attempt_id: UUID,
    # data: Optional[dict[str, Any]] = None,
    user_id: Optional[UUID] = None,
    approved: bool = False,
) -> models.Feedback:
    feedback_obj = (
        EXAMPLE_APPROVED_FEEDBACK if approved else EXAMPLE_UNAPPROVED_FEEDBACK
    )
    feedback = models.Feedback(
        attempt_id=attempt_id,
        user_id=user_id,
        is_ai=user_id is None,
        data=feedback_obj.model_dump(),
    )
    session.add(feedback)
    session.flush()
    link = AttemptFeedbackLink(attempt_id=attempt_id, feedback_id=feedback.id)
    session.add(link)
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


def mock_gpt(
    mocker: pytest_mock.MockerFixture,
    outputs: list[str] = ["simulated output"],
    simulated_cost: float = 0.0,
):
    # mock GPT API calls
    mock = mocker.patch("app.feedback_utils.GPTModel.__call__")
    mock.return_value = (outputs, [])

    mock2 = mocker.patch("app.feedback_utils.GPTModel.compute_price")
    mock2.return_value = simulated_cost
    return mock, mock2
