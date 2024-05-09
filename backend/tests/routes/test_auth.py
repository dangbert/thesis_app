from sqlalchemy import select
from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
from app.settings import get_settings
from tests.dummy import DUMMY_ID, make_course, make_assignment
from fastapi.testclient import TestClient
from starlette.responses import RedirectResponse
import base64
import itsdangerous
import json
import app.models as models
import tests.dummy as dummy
import pytest_mock
from app.routes.auth import oauth

settings = get_settings()


def set_session_cookie_on_client(client: TestClient, user: models.User):
    """Helper function to get a session cookie on the client."""
    session = {"user": {"sub": user.sub, "name": user.name, "email": user.email}}
    # mirrors what starlette.middleware.sessions.SessionMiddleware does:
    session_data = base64.b64encode(json.dumps(session).encode())
    signer = itsdangerous.TimestampSigner(settings.secret_key)
    cookie_data = signer.sign(session_data).decode()
    client.cookies.set("session", cookie_data)


def test_login(client: TestClient, session, mocker: pytest_mock.MockerFixture):
    # user = dummy.make_user(session)
    mock = mocker.patch.object(oauth.auth0, "authorize_redirect")
    mock.return_value = RedirectResponse(f"https://{settings.auth0_domain}/login/", 302)

    res = client.get(f"{settings.api_v1_str}/auth/login")
    mock.assert_called_once_with(
        mocker.ANY,
        "http://localhost:2222/api/v1/auth/callback",
        connection="google-oauth2",
        response_type="code",
    )
    assert res.is_redirect


def test_logout(client: TestClient, session):
    user = dummy.make_user(session)
    set_session_cookie_on_client(client, user)
    res = client.get(f"{settings.api_v1_str}/auth/logout")
    # note default TestClientbase_url is "http://testserver"
    assert res.is_redirect
    assert (
        res.headers["location"]
        == f"https://{settings.auth0_domain}/v2/logout?returnTo=http%3A%2F%2Ftestserver%2F&client_id={settings.auth0_client_id}"
    )
    assert res.headers["set-cookie"].startswith("session=null;")
    # assert res.json() == {"detail": "Logged out"}
