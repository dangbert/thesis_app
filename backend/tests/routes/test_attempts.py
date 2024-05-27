from app.models.course import (
    Assignment,
    Attempt,
    AttemptCreate,
    AttemptPublic,
    Feedback,
    FeedbackPublic,
    CourseRole,
)
from app.models.job import Job, AI_FEEDBACK_JOB_DATA, JobStatus, JobType
import app.models.schemas as schemas
from app.routes.courses import ASSIGNMENT_NOT_FOUND
from app.routes.attempts import ATTEMPT_NOT_FOUND
from app.hardcoded import SMARTData, FeedbackData
from tests.dummy import (
    DUMMY_ID,
    make_user,
    make_course,
    make_assignment,
    make_attempt,
    EXAMPLE_SMART_DATA,
)
import tests.dummy as dummy
import json
from app.routes.files import FILE_NOT_FOUND


def test_list_attempts(client, settings, session):
    c1, as1, teacher, student1 = dummy.init_simple_course(session)
    student2 = dummy.make_user(session, email="random@example.com")
    dummy.assert_not_authenticated(
        client.get(f"{settings.api_v1_str}/attempt/", params={"assignment_id": as1.id})
    )

    # student2 (not part of the course has no access)
    dummy.login_user(client, student2)
    res = client.get(
        f"{settings.api_v1_str}/attempt/", params={"assignment_id": as1.id}
    )
    assert res.status_code == 404 and res.json()["detail"] == ASSIGNMENT_NOT_FOUND

    student2.enroll(session, c1, CourseRole.STUDENT)
    at_2a = make_attempt(session, as1.id, student2.id)
    at_2b = make_attempt(session, as1.id, student2.id)

    # student1 should only see their own attempts
    dummy.login_user(client, student1)
    at_1a = make_attempt(session, as1.id, student1.id)
    for extra in [{}, {"user_id": student1.id}]:
        res = client.get(
            f"{settings.api_v1_str}/attempt/", params={"assignment_id": as1.id, **extra}
        )
        assert res.status_code == 200 and len(res.json()) == 1
        assert AttemptPublic(**res.json()[0]) == at_1a.to_public()

    # test teacher can view specific student's attempts
    dummy.login_user(client, teacher)
    for extra, expected in [
        ({}, []),
        ({"user_id": student1.id}, [at_1a.to_public()]),
        ({"user_id": student2.id}, [at_2a.to_public(), at_2b.to_public()]),
    ]:
        res = client.get(
            f"{settings.api_v1_str}/attempt/", params={"assignment_id": as1.id, **extra}
        )
        assert res.status_code == 200 and len(res.json()) == len(expected)
        assert [AttemptPublic(**x) for x in res.json()] == expected


def test_get_attempt(client, settings, session):
    user1 = make_user(session)
    c1 = make_course(session)
    as1 = make_assignment(session, c1.id)
    at1 = make_attempt(session, as1.id, user1.id)
    dummy.assert_not_authenticated(
        client.get(f"{settings.api_v1_str}/attempt/{DUMMY_ID}")
    )

    dummy.login_user(client, user1)
    res = client.get(f"{settings.api_v1_str}/attempt/{at1.id}")
    assert res.status_code == 404 and res.json()["detail"] == ATTEMPT_NOT_FOUND

    user1.enroll(session, c1, CourseRole.STUDENT)
    res = client.get(f"{settings.api_v1_str}/attempt/{at1.id}")
    assert res.status_code == 200


def test_create_attempt(client, settings, session):
    user1 = make_user(session)
    user2 = make_user(session, email="user2@example.com")
    c1 = make_course(session)
    as1 = make_assignment(session, c1.id)
    dummy.assert_not_authenticated(client.put(f"{settings.api_v1_str}/attempt/"))

    dummy.login_user(client, user1)
    obj = AttemptCreate(assignment_id=as1.id, data={"hello": "world"}, file_ids=[])
    res = client.put(
        f"{settings.api_v1_str}/attempt/",
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": as1.id},
    )
    assert res.status_code == 404 and res.json()["detail"] == ASSIGNMENT_NOT_FOUND

    # ensure only SMARTData format is accepted
    user1.enroll(session, c1, CourseRole.STUDENT)
    res = client.put(
        f"{settings.api_v1_str}/attempt/",
        # this is a hack to get obj as a dict where UUID is serialized to str
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": as1.id},
    )
    assert (
        res.status_code == 400
        and res.json()["detail"] == "Data format not in SMARTData format"
    )

    obj = AttemptCreate(
        assignment_id=as1.id, data=EXAMPLE_SMART_DATA.model_dump(), file_ids=[]
    )
    res = client.put(
        f"{settings.api_v1_str}/attempt/",
        # this is a hack to get obj as a dict where UUID is serialized to str
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": as1.id},
    )
    assert res.status_code == 201
    created = session.get(Attempt, res.json()["id"])
    assert (
        AttemptPublic(**res.json()) == created.to_public()
        and created.user_id == user1.id
    )

    # verify job was created
    jobs = session.query(Job).all()
    assert len(jobs) == 1
    expect_job_data = AI_FEEDBACK_JOB_DATA(attempt_id=created.id)
    job = jobs[0]
    assert AI_FEEDBACK_JOB_DATA(**job.data) == expect_job_data
    assert job.status == JobStatus.PENDING and job.job_type == JobType.AI_FEEDBACK

    # user can't create attempt with other's files
    file1 = dummy.make_file(session, user1.id)
    file2 = dummy.make_file(session, user2.id)
    file3 = dummy.make_file(session, user1.id)
    obj = AttemptCreate(
        assignment_id=as1.id,
        data=EXAMPLE_SMART_DATA.model_dump(),
        file_ids=[file1.id, file2.id],
    )
    res = client.put(
        f"{settings.api_v1_str}/attempt/",
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": as1.id},
    )
    assert res.status_code == 400 and res.json()["detail"] == FILE_NOT_FOUND

    # user can create attempt with their own files
    obj = AttemptCreate(
        assignment_id=as1.id,
        data=EXAMPLE_SMART_DATA.model_dump(),
        file_ids=[file1.id, file3.id],
    )
    res = client.put(
        f"{settings.api_v1_str}/attempt/",
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": as1.id},
    )
    assert res.status_code == 201
    ret_obj = AttemptPublic(**res.json())
    assert ret_obj.files == [file1.to_public(), file3.to_public()]


def test_create_feedback(client, settings, session):
    course, as1, _, user = dummy.init_simple_course(session)
    at1 = make_attempt(session, as1.id, user.id)
    dummy.assert_not_authenticated(
        client.put(f"{settings.api_v1_str}/attempt/{at1.id}/feedback")
    )

    dummy.login_user(client, user)
    obj = schemas.FeedbackCreate(
        attempt_id=at1.id,
        data=dummy.EXAMPLE_UNAPPROVED_FEEDBACK.model_dump(),
    )

    res = client.put(
        f"{settings.api_v1_str}/attempt/{at1.id}/feedback",
        json=json.loads(obj.model_dump_json()),
    )
    assert res.status_code == 201
    session.refresh(at1)
    assert (
        len(at1.feedbacks) == 1
        and FeedbackData(**at1.feedbacks[0].data) == dummy.EXAMPLE_UNAPPROVED_FEEDBACK
    )

    created = session.get(Feedback, res.json()["id"])
    assert (
        created.to_public() == FeedbackPublic(**res.json())
        and created.user_id == user.id
    )
