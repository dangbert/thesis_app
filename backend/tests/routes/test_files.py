from fastapi.testclient import TestClient
from tests.dummy import make_user, make_course, make_assignment
from app.models.course import File
from app.models.course_partials import FilePublic
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

    res = client.put(
        f"{settings.api_v1_str}/file",
        files=data,  # type: ignore [arg-type]
    )

    assert res.status_code == 201, f"Expected status code 201, got {res.status_code}"
    res_file = FilePublic(**res.json())
    file = session.query(File).get(res_file.id)
    assert file is not None, "The file record was not saved in the database."
    file_path = f"{settings.file_dir}/{file.id}.{file_name.split('.')[-1]}"
    assert os.path.isfile(file_path), "File not found in expected directory"

    with open(file_path, "rb") as f:
        stored_file_content = f.read()
        assert (
            stored_file_content == file_content
        ), "The content of the stored file does not match the uploaded content."
