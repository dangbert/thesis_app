from sqlalchemy import select
from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
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
    res = client.get(f"{settings.api_v1_str}/course/")
    assert res.status_code == 200 and res.json() == []

    # TODO: ensure users can only access courses they belong to
    course = make_course(session)
    res = client.get(f"{settings.api_v1_str}/course/")
    assert res.status_code == 200
    res_list = res.json()
    assert len(res_list) == 1
    res_course = CoursePublic(**res_list[0])
    assert res_course == course.to_public()

    _ = make_course(session, name="test2")
    res = client.get(f"{settings.api_v1_str}/course/")
    assert len(res.json()) == 2


def test_get_assignment(client, settings, session):
    user = dummy.make_user(session)
    dummy.assert_not_authenticated(
        client.get(f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment/{DUMMY_ID}")
    )

    dummy.login_user(client, user)
    res = client.get(
        f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment/{DUMMY_ID}",
    )
    assert res.status_code == 404 and res.json()["detail"] == "Course not found"

    c1 = make_course(session)
    res = client.get(
        f"{settings.api_v1_str}/course/{c1.id}/assignment/{DUMMY_ID}",
    )
    assert res.status_code == 404 and res.json()["detail"] == "Assignment not found"

    a1 = make_assignment(session, c1.id)
    a2 = make_assignment(session, c1.id, name="test2")
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
    assert res.status_code == 404 and res.json()["detail"] == "Assignment not found"


def test_create_assignment(client, settings, session):
    user = dummy.make_user(session)
    dummy.assert_not_authenticated(
        client.put(f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment")
    )

    dummy.login_user(client, user)
    obj = AssignmentCreate(name="Test Assignment", about="This is a test assignment.")
    res = client.put(
        f"{settings.api_v1_str}/course/{DUMMY_ID}/assignment",
        json=obj.model_dump(),
    )
    assert res.status_code == 404 and res.json()["detail"] == "Course not found"

    course = make_course(session)
    res = client.put(
        f"{settings.api_v1_str}/course/{course.id}/assignment",
        json=obj.model_dump(),
    )
    assert res.status_code == 201
    a1 = session.get(Assignment, res.json()["id"])
    assert AssignmentPublic(**res.json()) == a1.to_public()
