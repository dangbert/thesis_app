from app.models import User, Course, Assignment
import app.models as models
from uuid import UUID
from sqlalchemy.orm import Session
from tests.dummy import make_user, make_course, make_assignment, EXAMPLE_FEEDBACK_DATA
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

    a1 = Assignment(name="Assignment 1", course_id=course.id, scorable=True)
    a2 = Assignment(name="Assignment 2", course_id=course.id, scorable=False)
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
    assert at1.feedbacks == []

    feedback = models.Feedback(
        attempt_id=at1.id,
        user_id=user.id,
        is_ai=False,
        data=EXAMPLE_FEEDBACK_DATA.model_dump(),
    )
    session.add(feedback)
    session.commit()
    session.add(models.AttemptFeedbackLink(attempt_id=at1.id, feedback_id=feedback.id))
    session.commit()

    assert len(at1.feedbacks) == 1 and at1.feedbacks[0].id == feedback.id


def test_user_can_view(session):
    """
    Sanity checks for user.can_view method to ensure proper access control.
    NOTE: not testing file access here but this is done implicitly in test_files.py
    """
    course, as1, prof, student1 = dummy.init_simple_course(session)
    user2 = make_user(session, email="fake@example.com")

    attempt = dummy.make_attempt(session, as1.id, user2.id)
    ai_feedback = dummy.make_feedback(session, attempt.id)
    prof_feedback = dummy.make_feedback(session, attempt.id, user_id=prof.id)

    def assert_no_access(user):
        for obj in [course, as1, attempt, ai_feedback]:
            assert not user.can_view(session, obj)
            assert not user.can_view(session, obj, edit=True)

    assert_no_access(user2)
    for in_course in [False, True]:
        user2.enroll(session, course, models.CourseRole.STUDENT if in_course else None)
        assert in_course == user2.can_view(
            session, attempt, edit=True
        ), "user2 should view their own attempt"
        assert in_course == user2.can_view(
            session, attempt, edit=False
        ), "user2 should edit their own attempt"
        assert in_course == user2.can_view(session, ai_feedback)
        assert not user2.can_view(session, ai_feedback, edit=True)

    # student1 should have view only access to course and assignment
    for prof_access in [True, False]:
        assert student1.can_view(session, course, edit=prof_access) != prof_access
        assert student1.can_view(session, as1, edit=prof_access) != prof_access
        # should not be able to access user2's attempt still
        for protected_obj in [attempt, ai_feedback]:
            assert not student1.can_view(session, protected_obj, edit=prof_access)

    # prof should have full access
    for edit in [True, False]:
        for obj in [course, as1, attempt, prof_feedback]:
            assert prof.can_view(session, obj, edit=edit)
    assert prof.can_view(session, ai_feedback, edit=False)
    assert not prof.can_view(
        session, ai_feedback, edit=True
    ), "ai feedback isn't editable"

    # revoke student1 and prof
    student1.enroll(session, course, role=None)
    assert_no_access(student1)
    prof.enroll(session, course, role=None)
    assert_no_access(prof)
