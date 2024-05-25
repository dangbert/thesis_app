from sqlalchemy import select
from app.models.course import (
    Course,
    CourseCreate,
    CourseRole,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
from app.routes.courses import COURSE_NOT_FOUND, ASSIGNMENT_NOT_FOUND
from tests.dummy import DUMMY_ID, make_course, make_assignment
import tests.dummy as dummy


### courses
def test_list_courses(client, settings, session):
    user = dummy.make_user(session)
    # auth sanity checks
    dummy.assert_not_authenticated(client.get(f"{settings.api_v1_str}/course/"))
    # here we do an extra check to test that the login/logout helpers work as intended
    dummy.login_user(client, user)
    dummy.logout_user(client)
    dummy.assert_not_authenticated(client.get(f"{settings.api_v1_str}/course/"))

    dummy.login_user(client, user)

    def assert_empty_course_list():
        res = client.get(f"{settings.api_v1_str}/course/")
        assert res.status_code == 200 and res.json() == []

    assert_empty_course_list()
    course1, course2 = make_course(session), make_course(session, name="test course2")
    res = client.get(f"{settings.api_v1_str}/course/")
    assert res.status_code == 200
    assert len(res.json()) == 0

    user.enroll(session, course1, CourseRole.STUDENT)
    res = client.get(f"{settings.api_v1_str}/course/")
    assert res.status_code == 200
    res_list = res.json()
    res_course = CoursePublic(**res_list[0])
    assert res_course == course1.to_public() and len(res_list) == 1

    user.enroll(session, course2, CourseRole.TEACHER)
    res = client.get(f"{settings.api_v1_str}/course/")
    assert res.status_code == 200 and len(res.json()) == 2

    user.enroll(session, course1, role=None)
    user.enroll(session, course2, role=None)
    assert_empty_course_list()


def test_get_course(client, settings, session):
    user1 = dummy.make_user(session)
    course1, course2 = make_course(session), make_course(session, name="test course2")
    dummy.assert_not_authenticated(
        client.get(f"{settings.api_v1_str}/course/{DUMMY_ID}")
    )

    # non-course member can't access
    dummy.login_user(client, user1)
    for course_id in [DUMMY_ID, course1.id, course2.id]:
        res = client.get(f"{settings.api_v1_str}/course/{course_id}")
        assert res.status_code == 404 and res.json()["detail"] == COURSE_NOT_FOUND

    user1.enroll(session, course1, CourseRole.STUDENT)
    res = client.get(f"{settings.api_v1_str}/course/{course1.id}")
    assert res.status_code == 200 and CoursePublic(**res.json()) == course1.to_public()


def test_list_assignments(client, settings, session):
    user = dummy.make_user(session)
    course = make_course(session)
    dummy.assert_not_authenticated(
        client.get(f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment")
    )

    dummy.login_user(client, user)
    res = client.get(f"{settings.api_v1_str}/course/{course.id}/assignment")
    assert res.status_code == 404 and res.json()["detail"] == COURSE_NOT_FOUND

    def assert_empty_assignment_list():
        res = client.get(f"{settings.api_v1_str}/course/{course.id}/assignment")
        assert res.status_code == 200 and res.json() == []

    user.enroll(session, course, CourseRole.STUDENT)
    assert_empty_assignment_list()

    as1 = make_assignment(session, course.id)
    as2 = make_assignment(session, course.id, name="test assignment2")
    res = client.get(f"{settings.api_v1_str}/course/{course.id}/assignment")
    assert res.status_code == 200 and len(res.json()) == 2
    assert (
        AssignmentPublic(**res.json()[0]) == as1.to_public()
        and AssignmentPublic(**res.json()[1]) == as2.to_public()
    )


def test_get_assignment(client, settings, session):
    user = dummy.make_user(session)
    dummy.assert_not_authenticated(
        client.get(f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment/{DUMMY_ID}")
    )

    dummy.login_user(client, user)
    res = client.get(
        f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment/{DUMMY_ID}",
    )
    assert res.status_code == 404 and res.json()["detail"] == ASSIGNMENT_NOT_FOUND

    c1 = make_course(session)
    a1 = make_assignment(session, c1.id)
    a2 = make_assignment(session, c1.id, name="test2")
    res = client.get(
        f"{settings.api_v1_str}/course/{c1.id}/assignment/{a2.id}",
    )
    assert res.status_code == 404 and res.json()["detail"] == ASSIGNMENT_NOT_FOUND

    user.enroll(session, c1, CourseRole.STUDENT)
    res = client.get(
        f"{settings.api_v1_str}/course/{c1.id}/assignment/{a2.id}",
    )
    assert res.status_code == 200
    assert AssignmentPublic(**res.json()) == a2.to_public()

    # try to get assignment from different course
    c2 = make_course(session, name="test2")
    res = client.get(
        f"{settings.api_v1_str}/course/{c2.id}/assignment/{a1.id}",
    )
    assert res.status_code == 404 and res.json()["detail"] == ASSIGNMENT_NOT_FOUND


def test_create_assignment(client, settings, session):
    user = dummy.make_user(session)
    course = make_course(session)
    dummy.assert_not_authenticated(
        client.put(f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment")
    )

    dummy.login_user(client, user)
    obj = AssignmentCreate(
        name="Test Assignment", about="This is a test assignment.", scorable=True
    )
    res = client.put(
        f"{settings.api_v1_str}/course/{course.id}/assignment",
        json=obj.model_dump(),
    )
    assert res.status_code == 404 and res.json()["detail"] == COURSE_NOT_FOUND

    user.enroll(session, course, CourseRole.STUDENT)
    res = client.put(
        f"{settings.api_v1_str}/course/{course.id}/assignment",
        json=obj.model_dump(),
    )
    assert res.status_code == 403, "student can't create assignment"

    user.enroll(session, course, CourseRole.TEACHER)
    res = client.put(
        f"{settings.api_v1_str}/course/{course.id}/assignment",
        json=obj.model_dump(),
    )
    assert res.status_code == 201
    a1 = session.get(Assignment, res.json()["id"])
    assert AssignmentPublic(**res.json()) == a1.to_public()
