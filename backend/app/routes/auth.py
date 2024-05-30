import urllib.parse
from fastapi import APIRouter, Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from authlib.oauth2 import OAuth2Error
from authlib.integrations.base_client import OAuthError, MismatchingStateError
from starlette.datastructures import URL
from starlette.responses import RedirectResponse
from sqlalchemy import select
from app.models.course import Course, CourseRole
from typing import Optional

from app.deps import SessionDep
from app.settings import get_settings
from config import get_logger
from app.models.user import Auth0UserInfo, User, UserPublic
import app.hardcoded as hardcoded

logger = get_logger(__name__)

IMPORTANT_LOGIN_STATE = {
    "destination",
    "invite_key",
}  # import field in session to preserve


settings = get_settings()
LOGIN_URL = (
    f"{settings.site_url}{settings.api_v1_str}/auth/login"  # request.url_for("login")
)
BASE_URL = f"{settings.site_url}/"

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=settings.auth0_client_id,
    client_secret=settings.auth0_client_secret,
    # https://auth0.com/docs/get-started/apis/scopes/openid-connect-scopes#standard-claims
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"https://{settings.auth0_domain}/.well-known/openid-configuration",
    authorize_state=settings.secret_key,
)


def _cleanup_session(request: Request):
    """
    Clears session, but preserves important fields.
    Fixes a CSRF warning when a user starts a google login and then revisits the site's login page.
    """
    keep = {
        k: request.session.get(k)
        for k in IMPORTANT_LOGIN_STATE
        if request.session.get(k) is not None
    }
    request.session.clear()
    logger.warning(
        f"Mismatching state error, clearing session, but keeping fields: {keep.keys()}"
    )
    for k, v in keep.items():
        request.session[k] = v


def is_relative_url(url: URL) -> bool:
    is_abs = url.scheme or url.hostname or not str(url).startswith("/")
    return not is_abs


def auth0_logout_url(return_to: URL) -> str:
    return f"https://{settings.auth0_domain}/v2/logout?" + urllib.parse.urlencode(
        {
            "returnTo": return_to,
            "client_id": settings.auth0_client_id,
        },
    )


router = APIRouter()


# https://auth0.com/docs/authenticate/protocols/oauth#authorization-endpoint
# https://docs.authlib.org/en/latest/client/fastapi.html
@router.get("/login", status_code=302)
async def login(
    request: Request,
    destination: Optional[str] = None,
    invite_key: Optional[str] = None,
) -> RedirectResponse:
    """
    Redirects user to Auth0 login page. destination is the (optional) URL to redirect to after login.
    """
    if not destination:
        destination = "/"
    if not is_relative_url(URL(destination)):
        raise HTTPException(
            status_code=400, detail="destination must be a relative path"
        )
    _cleanup_session(request)
    request.session["destination"] = destination  # remember for later
    if invite_key:
        request.session["invite_key"] = invite_key

    # after login, have Auth0 redirect to the /callback endpoint
    redirect_uri = f"{settings.site_url}{settings.api_v1_str}/auth/callback"
    return await oauth.auth0.authorize_redirect(
        request,
        redirect_uri,
        # adding the connection parameter sends the user directly to the Google login page (skipping an auth0 intermediary page)
        connection=settings.auth0_connection,
    )


@router.get("/callback", response_class=RedirectResponse)
async def callback(request: Request, session: SessionDep):
    """
    After Auth0 authenticates a user, it redirects here so the user's information can be stored in the session cookie.
    """

    try:
        token = await oauth.auth0.authorize_access_token(request)
    except MismatchingStateError:
        # if a user starts a google login and then revisits the site's login page, they may get a CSRF warning:
        #   Invalid authentication request: mismatching_state: CSRF Warning! State not equal in request and response.

        # clear session so user can login again, but remember important fields
        _cleanup_session(request)
        return RedirectResponse(url=LOGIN_URL)
    except (OAuth2Error, OAuthError) as exc:
        logger.warning(f"Invalid authentication request: {exc}")
        return RedirectResponse(url=LOGIN_URL)

    # note: a "Value Error Invalid JSON Web Key Set" here means the auth0 tenant needs to be configured to use RS256 instead of HS256

    # Validate the received user information and store it in the session cookie
    user_info = Auth0UserInfo.model_validate(token["userinfo"])
    logger.info(f"Received authenticated user: {user_info.email}")

    invite_key = request.session.get("invite_key")
    invite_course = None
    if invite_key:
        invite_course = session.query(Course).filter_by(invite_key=invite_key).first()

    # check if user exists in database and handle appropriately
    statement = select(User).where(User.email == user_info.email)
    user = session.execute(statement).scalars().first()

    if not user:
        if not hardcoded.email_can_signup(user_info.email):
            logger.warning(f"Rejecting unauthorized email: '{user_info.email}'")
            raise HTTPException(
                status_code=403,
                detail="Only VU emails are permitted at present, please login with your vu.nl email.",
            )
        if settings.invite_only_signup and not invite_course:
            if not invite_key:
                raise HTTPException(
                    status_code=403,
                    detail="Invite link required to sign up, please request from your teacher.",
                )
            raise HTTPException(
                status_code=403,
                detail="Invalid invite link, please request a new one from your teacher.",
            )

        logger.info(f"Creating new user not found in database: '{user_info.email}'")
        user = User(email=user_info.email, name=user_info.name, sub=user_info.sub)
        session.add(user)
        session.commit()
        session.refresh(user)

    if invite_course:
        if not user.get_course_role(session, invite_course.id):
            target_role = CourseRole.STUDENT  # TODO: could support a teacher_invite_key
            user.enroll(session, invite_course, target_role)
            logger.info(f"Enrolled user {user.email} in course {invite_course.id}")

    destination = request.session.get("destination") or "/"
    if not is_relative_url(URL(destination)):
        logger.warning(f"Overriding invalid destination: '{destination}'")
        destination = "/"

    request.session["user"] = user.to_public().model_dump(mode="json")
    return destination
    # referer = request.headers.get("Referer")
    # if referer is not None:
    #     return referer


# TODO: post would be better
@router.get("/logout", response_class=RedirectResponse)
async def logout(request: Request) -> str:
    """End the FastAPI session and redirect the user to Auth0 for OAuth logout."""

    # Clear user session, effectively logging out the user
    request.session.clear()
    # Redirect user to Auth0 logout, and return them to /
    # return auth0_logout_url(return_to=request.base_url)
    return auth0_logout_url(return_to=URL(BASE_URL))


@router.get(
    "/me",
    response_model=UserPublic,
    responses={302: {"description": "Redirect to login"}},
)
async def me(request: Request, session: SessionDep) -> UserPublic | RedirectResponse:
    """Returns information about the currently logged in user."""
    user_info = request.session.get("user")
    if not user_info:
        return RedirectResponse(url=LOGIN_URL)

    statement = select(User).where(User.email == user_info["email"])
    user = session.execute(statement).scalars().first()
    if not user:
        logger.error(
            f"User in session but not found in database '{user_info['email']}'"
        )
        return RedirectResponse(url=LOGIN_URL)

    return user.to_public()
