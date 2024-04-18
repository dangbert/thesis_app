from app.models.course import (
    Assignment,
    Attempt,
    AttemptCreate,
    AttemptPublic,
)
from app.hardcoded import SMARTData
from tests.dummy import (
    DUMMY_ID,
    make_user,
    make_course,
    make_assignment,
    make_attempt,
    example_smart_data,
)
import json


def test_list_attempts(client, settings, session):
    user = make_user(session)
    c1 = make_course(session)
    as1 = make_assignment(session, c1.id)

    res = client.get(
        f"{settings.api_v1_str}/attempt", params={"assignment_id": DUMMY_ID}
    )
    assert res.status_code == 404 and res.json()["detail"] == "Assignment not found"

    at1 = make_attempt(session, as1.id, user.id)
    res = client.get(f"{settings.api_v1_str}/attempt", params={"assignment_id": as1.id})
    assert res.status_code == 200 and len(res.json()) == 1
    assert AttemptPublic(**res.json()[0]) == at1.to_public()


def test_get_attempt(client, settings, session):
    user = make_user(session)
    c1 = make_course(session)
    as1 = make_assignment(session, c1.id)
    at1 = make_attempt(session, as1.id, user.id)

    res = client.get(f"{settings.api_v1_str}/attempt/{DUMMY_ID}")
    assert res.status_code == 404 and res.json()["detail"] == "Attempt not found"
    res = client.get(f"{settings.api_v1_str}/attempt/{at1.id}")
    assert res.status_code == 200


def test_create_attempt(client, settings, session):
    user = make_user(session)
    c1 = make_course(session)
    as1 = make_assignment(session, c1.id)

    obj = AttemptCreate(user_id=user.id, assignment_id=as1.id, data={"hello": "world"})
    res = client.put(
        f"{settings.api_v1_str}/attempt",
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": DUMMY_ID},
    )
    assert res.status_code == 404 and res.json()["detail"] == "Assignment not found"

    # ensure only SMARTData format is accepted
    res = client.put(
        f"{settings.api_v1_str}/attempt",
        # this is a hack to get obj as a dict where UUID is serialized to str
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": as1.id},
    )
    assert (
        res.status_code == 400
        and res.json()["detail"] == "Data format not in SMARTData format"
    )

    obj = AttemptCreate(
        user_id=user.id, assignment_id=as1.id, data=example_smart_data.model_dump()
    )
    res = client.put(
        f"{settings.api_v1_str}/attempt",
        # this is a hack to get obj as a dict where UUID is serialized to str
        json=json.loads(obj.model_dump_json()),
        params={"assignment_id": as1.id},
    )
    assert res.status_code == 201
    created = session.get(Attempt, res.json()["id"])
    assert AttemptPublic(**res.json()) == created.to_public()
