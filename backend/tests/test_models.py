from app.models import User, Course, Assignment
import app.models as models
from uuid import UUID
from sqlalchemy.orm import Session
from tests.dummy import make_user, make_course, make_assignment, example_feedback_data
import tests.dummy as dummy


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


def test_attempt_feedback(session):
    course = make_course(session)
    as1 = make_assignment(session, course.id)
    user = make_user(session)

    at1 = dummy.make_attempt(session, as1.id, user.id)
    assert at1.feedback == []

    feedback = models.Feedback(
        attempt_id=at1.id,
        user_id=user.id,
        is_ai=False,
        data=example_feedback_data.model_dump(),
    )
    session.add(feedback)
    session.commit()
    session.add(models.AttemptFeedback(attempt_id=at1.id, feedback_id=feedback.id))
    session.commit()

    assert len(at1.feedback) == 1 and at1.feedback[0].id == feedback.id


def test_user_can_view(session):
    """Sanity checks for user.can_view method to ensure proper access control."""
    course = make_course(session)
    as1 = make_assignment(session, course.id)
    student1 = make_user(session)
    user2 = make_user(session, email="fake@example.com")
    prof = make_user(session, email="professor@example.com")
    dummy.enroll_as(session, prof, course, models.CourseRole.TEACHER)

    attempt = dummy.make_attempt(session, as1.id, user2.id)
    assert user2.can_view(
        session, attempt, edit=True
    ), "user2 should view/edit their own attempt"
    assert user2.can_view(
        session, attempt, edit=False
    ), "user2 should view/edit their own attempt"

    def assert_0_access(user):
        for obj in [course, as1, attempt]:
            assert not user.can_view(session, obj)
            assert not user.can_view(session, obj, edit=True)

    assert_0_access(student1)  # user1 should have 0 access

    # now we make user1 a course student
    dummy.enroll_as(session, student1, course, models.CourseRole.STUDENT)

    # user1 should have view only access to course and assignment
    for prof_access in [True, False]:
        assert student1.can_view(session, course, edit=prof_access) != prof_access
        assert student1.can_view(session, as1, edit=prof_access) != prof_access
        # should not be able to access user2's attempt still
        assert not student1.can_view(session, attempt, edit=prof_access)

    # prof should have full access
    for edit in [True, False]:
        assert prof.can_view(session, course, edit=edit)
        assert prof.can_view(session, as1, edit=edit)
        assert prof.can_view(session, attempt, edit=edit)

    # revoke student1
    dummy.enroll_as(session, student1, course, role=None)
    assert_0_access(student1)

    # TODO: test feedback access
