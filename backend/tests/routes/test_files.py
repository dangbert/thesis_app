from fastapi.testclient import TestClient
from tests.dummy import make_user, make_file
from app.models.course import File
from app.models.schemas import FilePublic
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
    user = make_user(session)
    content = b"blah blah blah!"
    file = make_file(session, user.id, content=content)

    read_url = file.to_public().read_url
    # Test the download endpoint
    res = client.get(read_url)

    assert res.status_code == 200, f"Expected status code 200, got {res.status_code}"
    assert (
        res.content == content
    ), "The downloaded file content does not match the expected content."

    #
