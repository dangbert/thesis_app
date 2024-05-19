from fastapi.testclient import TestClient
from tests.dummy import make_user, make_file
import tests.dummy as dummy
import app.models as models
from app.models.course import File, CourseRole
from app.models.schemas import FilePublic
from app.routes.files import FILE_NOT_FOUND
from io import BytesIO
import os


def test_file_upload(client: TestClient, settings, session):
    user = make_user(session)
    file_content = b"Hello, World!"
    file_name = "testfile.txt"
    # Prepare data for sending as multipart including file and form fields
    data = {
        "file": (file_name, BytesIO(file_content), "text/plain"),
        "user_id": (
            None,
            str(user.id),
        ),  # Passing user_id as part of the form data for now
    }
    dummy.assert_not_authenticated(client.put(f"{settings.api_v1_str}/file/"))

    dummy.login_user(client, user)
    res = client.put(
        f"{settings.api_v1_str}/file/",
        files=data,  # type: ignore [arg-type]
    )
    assert res.status_code == 201, f"Expected status code 201, got {res.status_code}"
    res_file = FilePublic(**res.json())
    file = session.get(File, res_file.id)
    assert file is not None, "The file record was not saved in the database."
    file_path = f"{settings.file_dir}/{file.id}.{file_name.split('.')[-1]}"
    assert os.path.isfile(file_path), "File not found in expected directory"

    with open(file_path, "rb") as f:
        stored_file_content = f.read()
        assert (
            stored_file_content == file_content
        ), "The content of the stored file does not match the uploaded content."


def test_file_download(client: TestClient, session):
    user1 = make_user(session)
    user2 = make_user(session, email="user2@example.com")
    course = dummy.make_course(session)
    as1 = dummy.make_assignment(session, course.id)
    attempt = dummy.make_attempt(session, as1.id, user2.id)

    # create file, attach to attempt
    content = b"blah blah blah!"
    file = make_file(session, user2.id, content=content, attempt_id=attempt.id)
    read_url = file.to_public().read_url
    dummy.assert_not_authenticated(client.get(read_url))

    # user1 and (future) prof can't view the file
    prof = make_user(session, email="prof@example.com")
    for bad_user in [user1, prof]:
        dummy.login_user(client, bad_user)
        res = client.get(read_url)
        assert res.status_code == 404 and res.json() == {"detail": FILE_NOT_FOUND}

    # user2 can view own file, as well as the prof
    prof.enroll(session, course, role=CourseRole.TEACHER)
    for allowed_user in [user2, prof]:
        dummy.login_user(client, allowed_user)
        res = client.get(read_url)
        assert res.status_code == 200
        assert (
            res.content == content
        ), "The downloaded file content does not match the expected content."
