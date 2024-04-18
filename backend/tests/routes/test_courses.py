from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
from tests.dummy import DUMMY_ID, make_course, make_assignment


### courses
def test_list_courses(client, settings, session):
    res = client.get(f"{settings.api_v1_str}/course")
    assert res.status_code == 200
    assert res.json() == []

    course = make_course(session)
    res = client.get(f"{settings.api_v1_str}/course")
    assert res.status_code == 200
    res_list = res.json()
    assert len(res_list) == 1
    res_course = CoursePublic(**res_list[0])
    assert res_course == course.to_public()

    _ = make_course(session, name="test2")
    res = client.get(f"{settings.api_v1_str}/course")
    assert len(res.json()) == 2


def test_get_assignment(client, settings, session):
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
    res = client.get(
        f"{settings.api_v1_str}/course/{c1.id}/assignment/{a1.id}",
    )
    assert res.status_code == 200
    assert AssignmentPublic(**res.json()) == a1.to_public()

    # try to get assignment from different course
    c2 = make_course(session, name="test2")
    res = client.get(
        f"{settings.api_v1_str}/course/{c2.id}/assignment/{a1.id}",
    )
    assert res.status_code == 404 and res.json()["detail"] == "Assignment not found"


def test_create_assignment(client, settings, session):
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
    a1 = session.query(Assignment).get(res.json()["id"])
    assert AssignmentPublic(**res.json()) == a1.to_public()
