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
from app.models.schemas import AssignmentAttemptStatus, AssignmentStudentStatus
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

    for role, group_num in [(CourseRole.STUDENT, None), (CourseRole.STUDENT, 7)]:
        user.enroll(session, course1, role, group_num=group_num)
        res = client.get(f"{settings.api_v1_str}/course/")
        assert res.status_code == 200
        res_list = res.json()
        res_course = CoursePublic(**res_list[0])
        assert (
            res_course
            == course1.to_public(your_role=CourseRole.STUDENT, your_group=group_num)
            and len(res_list) == 1
        )

    user.enroll(session, course2, CourseRole.TEACHER)
    res = client.get(f"{settings.api_v1_str}/course/")
    assert res.status_code == 200
    assert [CoursePublic(**item) for item in res.json()] == [
        course1.to_public(your_role=CourseRole.STUDENT, your_group=7),
        course2.to_public(your_role=CourseRole.TEACHER),
    ]

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

    prof = dummy.make_user(session, email="prof@example.com")
    for user, role, group_num in [
        (user1, CourseRole.STUDENT, None),
        (user1, CourseRole.STUDENT, None),
        (prof, CourseRole.TEACHER, None),
    ]:
        user.enroll(session, course1, role, group_num=group_num)
        dummy.login_user(client, user)
        res = client.get(f"{settings.api_v1_str}/course/{course1.id}")
        assert res.status_code == 200 and CoursePublic(
            **res.json()
        ) == course1.to_public(your_role=role, your_group=group_num)


def test_get_enroll_details(client, settings, session):
    course = dummy.make_course(session)
    user = dummy.make_user(session)

    dummy.login_user(client, user)
    assert not user.can_view(session, course)
    res = client.get(
        f"{settings.api_v1_str}/course/enroll_details", params={"invite_key": "fake"}
    )
    assert res.status_code == 400 and res.json()["detail"] == "invalid invite link"
    res = client.get(
        f"{settings.api_v1_str}/course/enroll_details",
        params={"invite_key": course.invite_key},
    )
    assert res.status_code == 200
    assert CoursePublic(**res.json()) == course.to_public(
        invite_role=CourseRole.STUDENT
    )

    # existing user should see their role
    user.enroll(session, course, CourseRole.TEACHER)
    res = client.get(
        f"{settings.api_v1_str}/course/enroll_details",
        params={"invite_key": course.invite_key},
    )
    assert res.status_code == 200
    assert CoursePublic(**res.json()) == course.to_public(
        invite_role=CourseRole.STUDENT, your_role=CourseRole.TEACHER
    )


def test_set_enroll_details(client, settings, session):
    course = dummy.make_course(session)
    user = dummy.make_user(session)
    dummy.assert_not_authenticated(
        client.post(
            f"{settings.api_v1_str}/course/{course.id}/enroll_details",
            params={"group_num": 4},
        ),
    )

    dummy.login_user(client, user)
    res = client.post(
        f"{settings.api_v1_str}/course/{course.id}/enroll_details",
        params={"group_num": 4},
    )
    # non-enrolled user can't access
    assert res.status_code == 404 and res.json()["detail"] == COURSE_NOT_FOUND

    # enrolled user can change their group number
    user.enroll(session, course, CourseRole.STUDENT)
    res = client.post(
        f"{settings.api_v1_str}/course/{course.id}/enroll_details",
        params={"group_num": 4},
    )
    assert res.status_code == 200
    assert user.get_course_link(session, course.id).group_num == 4


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


def test_get_assignment_status(client, settings, session):
    course, as1, prof, student1 = dummy.init_simple_course(session)
    student2 = dummy.make_user(session, email="student2@example.com")
    student2.enroll(session, course, CourseRole.STUDENT)

    # NOTE: would be better to just put assignments under {settings.api_v1_str}/assignment/ but not that important
    def get_status_url(assignment: Assignment):
        return f"{settings.api_v1_str}/course/{assignment.course_id}/assignment/{assignment.id}/status"

    dummy.login_user(client, student1)
    res = client.get(get_status_url(as1))
    assert res.status_code == 403

    dummy.login_user(client, prof)
    res = client.get(get_status_url(as1))
    assert res.status_code == 200

    initial_args = {
        "attempt_count": 0,
        "latests_attempt_date": None,
        "status": AssignmentAttemptStatus.NOT_STARTED,
    }
    expected = [
        # prof will also show up as they can complete their own assignment for testing
        AssignmentStudentStatus(
            student=prof.to_public(),
            **initial_args,
            role=CourseRole.TEACHER,
        ),
        AssignmentStudentStatus(
            student=student1.to_public(), role=CourseRole.STUDENT, **initial_args
        ),
        AssignmentStudentStatus(
            student=student2.to_public(), role=CourseRole.STUDENT, **initial_args
        ),
    ]
    res_list = [AssignmentStudentStatus(**item) for item in res.json()]
    assert res_list == expected

    # now have user 2 make some attempts
    dummy.make_attempt(session, as1.id, student1.id)
    last_attempt = dummy.make_attempt(session, as1.id, student1.id)
    expected[1].last_attempt_date = last_attempt.created_at
    expected[1].attempt_count = 2
    expected[1].status = AssignmentAttemptStatus.AWAITING_AI_FEEDBACK
    res = client.get(get_status_url(as1))
    assert res.status_code == 200
    assert [AssignmentStudentStatus(**item) for item in res.json()] == expected

    # create AI feedback
    dummy.make_feedback(session, last_attempt.id, user_id=None)
    res = client.get(get_status_url(as1))
    assert res.status_code == 200
    expected[1].status = AssignmentAttemptStatus.AWAITING_TEACHER_FEEDBACK
    assert [AssignmentStudentStatus(**item) for item in res.json()] == expected

    # lastly create teacher feedback
    teacher_feedback = dummy.make_feedback(
        session, last_attempt.id, user_id=prof.id, approved=False
    )
    res = client.get(get_status_url(as1))
    assert res.status_code == 200
    expected[1].status = AssignmentAttemptStatus.RESUBMISSION_REQUESTED
    assert [AssignmentStudentStatus(**item) for item in res.json()] == expected

    teacher_feedback.data = dummy.EXAMPLE_APPROVED_FEEDBACK.model_dump()
    session.commit()
    res = client.get(get_status_url(as1))
    assert res.status_code == 200
    expected[1].status = AssignmentAttemptStatus.COMPLETE
    assert [AssignmentStudentStatus(**item) for item in res.json()] == expected
