from app.models import User, Course
from sqlalchemy.orm import Session


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
