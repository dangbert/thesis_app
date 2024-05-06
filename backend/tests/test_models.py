from app.models import User, Course, Assignment
from uuid import UUID
from sqlalchemy.orm import Session
from tests.dummy import make_user, make_course


def test_user(session: Session):
    email = "hello@example.com"
    user = make_user(session, email=email)

    print("created user: ", user.id)
    assert user.email_verified == False
    # sqlalchemy automatically converts postgres UUIDs to native uuid.UUID type
    assert isinstance(user.id, UUID)
    # assert user.email_token != None
    assert user.email == email
    assert user.email_token is not None


def test_integration__user_course_assignment(session: Session):
    _ = make_user(session)
    course = make_course(session)

    a1 = Assignment(name="Assignment 1", course_id=course.id)
    a2 = Assignment(name="Assignment 2", course_id=course.id)
    session.add(a1)
    session.add(a2)
    session.commit()

    # testing relationships
    assert a1.course_id == course.id
    assert {a.id for a in course.assignments} == {a1.id, a2.id}

    session.delete(a1)
    session.commit()
    assert len(course.assignments) == 1

    assert len(course.files) == 0
    assert len(a1.files) == 0

    # delete course then check if assignments are deleted
    session.delete(course)
    session.commit()
    assert session.query(Assignment).count() == 0, "cascade delete failed"
