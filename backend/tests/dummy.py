"""Utilities for creating dummy data for testing."""

from app.models import User, Course, Assignment, Attempt
from app.hardcoded import SMARTData
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any, Optional


DUMMY_ID = UUID("cc2d7ce4-170f-4817-b4a9-76e11d5f9c56")


def make_user(
    session: Session, email: str = "testuser@example.com", name: str = "Jane van Doe"
) -> User:
    sub = f"auth0|{str(hash(email))}"
    user = User(email=email, name=name, sub=sub)
    session.add(user)
    session.commit()
    return user


def make_course(session: Session, name="Test Course"):
    course = Course(name=name)
    session.add(course)
    session.commit()
    return course


def make_assignment(session: Session, course_id: UUID, name="Test Assignment"):
    assignment = Assignment(course_id=course_id, name=name)
    session.add(assignment)
    session.commit()
    return assignment


example_smart_data = SMARTData(goal="test goal", plan="test plan")


def make_attempt(
    session: Session,
    assignment_id: UUID,
    user_id: UUID,
    data: Optional[dict[str, Any]] = None,
):
    if data is None:
        data = example_smart_data.model_dump()
    attempt = Attempt(assignment_id=assignment_id, user_id=user_id, data=data)
    session.add(attempt)
    session.commit()
    return attempt
