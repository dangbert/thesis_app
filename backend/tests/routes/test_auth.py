from sqlalchemy import select
from app.settings import get_settings
from tests.dummy import DUMMY_ID, make_course, make_assignment
from fastapi.testclient import TestClient
from starlette.responses import RedirectResponse
import app.models as models
import app.models.schemas as schemas
import tests.dummy as dummy
import pytest_mock
from app.routes.auth import oauth, LOGIN_URL

settings = get_settings()


def test_login(client: TestClient, mocker: pytest_mock.MockerFixture):
    # user = dummy.make_user(session)
    mock = mocker.patch.object(oauth.auth0, "authorize_redirect")
    mock.return_value = RedirectResponse(f"https://{settings.auth0_domain}/login/", 302)

    res = client.get(f"{settings.api_v1_str}/auth/login")
    mock.assert_called_once_with(
        mocker.ANY,
        "http://localhost:2222/api/v1/auth/callback",
        connection="google-oauth2",
    )
    assert res.is_redirect


def test_logout(client: TestClient, session):
    user = dummy.make_user(session)
    dummy.login_user(client, user)
    res = client.get(f"{settings.api_v1_str}/auth/logout")
    assert res.is_redirect
    assert (
        res.headers["location"]
        == f"https://{settings.auth0_domain}/v2/logout?returnTo=http%3A%2F%2Flocalhost%3A2222%2F&client_id={settings.auth0_client_id}"
        # == f"https://{settings.auth0_domain}/v2/logout?returnTo=http%3A%2F%2Ftestserver%2F&client_id={settings.auth0_client_id}"
    )
    assert res.headers["set-cookie"].startswith("session=null;")
    # assert res.json() == {"detail": "Logged out"}


def test_callback(
    client: TestClient,
    session,
    mocker: pytest_mock.MockerFixture,
):
    # test callback flow for an existing user
    user = dummy.make_user(session)
    mock = mocker.patch.object(oauth.auth0, "authorize_access_token")
    mock.return_value = {
        "userinfo": {
            "sub": user.sub,
            "name": user.name,
            "email": user.email,
            "extra": "extra",
        }
    }

    # note default TestClientbase_url is "http://testserver"
    client.cookies.clear()  # User is not logged in
    client.headers = {"Referer": "http://testserver/"}  # type: ignore [assignment]
    res = client.get(f"{settings.api_v1_str}/auth/callback")
    mock.assert_called_once()

    def check_res(res):
        # Check redirect to / and session cookie is set correctly
        assert res.is_redirect
        assert res.headers["location"] == "/"
        cookie = res.headers["set-cookie"]
        assert cookie.startswith("session=")
        assert "httponly" in cookie
        assert "path=/" in cookie
        assert "samesite=lax" in cookie

    check_res(res)

    # check user has access
    res = client.get(f"{settings.api_v1_str}/auth/me")
    assert res.status_code == 200
    assert schemas.UserPublic(**res.json()) == user.to_public()

    # test callback flow for a new user
    client.cookies.clear()  # logout
    new_user_info = {
        "sub": "auth0|1234",
        "name": "John van Doe",
        "email": "hi@student.vu.nl",
        "extra": "extra",
    }
    mock.return_value = {"userinfo": new_user_info}
    res = client.get(f"{settings.api_v1_str}/auth/callback")
    statement = select(models.User).where(models.User.email == new_user_info["email"])
    new_user = session.execute(statement).scalars().first()
    assert new_user
    check_res(res)
    res = client.get(f"{settings.api_v1_str}/auth/me")
    assert res.status_code == 200
    assert schemas.UserPublic(**res.json()) == new_user.to_public()


def test_me(client: TestClient, session):
    user = dummy.make_user(session)
    res = client.get(f"{settings.api_v1_str}/auth/me")
    assert res.is_redirect
    assert res.headers["location"] == LOGIN_URL

    dummy.login_user(client, user)
    res = client.get(f"{settings.api_v1_str}/auth/me")
    assert res.status_code == 200
    assert schemas.UserPublic(**res.json()) == user.to_public()

    session.delete(user)
    session.commit()
    res = client.get(f"{settings.api_v1_str}/auth/me")
    assert res.is_redirect
    assert res.headers["location"] == LOGIN_URL
