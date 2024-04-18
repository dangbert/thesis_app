"""Utilities for creating dummy data for testing."""

from app.models import User, Course, Assignment, Attempt
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any


DUMMY_ID = UUID("cc2d7ce4-170f-4817-b4a9-76e11d5f9c56")


def make_user(session: Session, email: str = "testuser@example.com") -> User:
    user = User(email=email)
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


def make_attempt(
    session: Session, assignment_id: UUID, user_id: UUID, data: dict[str, Any]
):
    attempt = Attempt(assignment_id=assignment_id, user_id=user_id, data=data)
    session.add(attempt)
    session.commit()
    return attempt
