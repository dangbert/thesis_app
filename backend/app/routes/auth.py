import urllib.parse
from fastapi import APIRouter, Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from authlib.oauth2 import OAuth2Error
from authlib.integrations.base_client import OAuthError
from starlette.datastructures import URL
from starlette.responses import RedirectResponse
from typing import Optional

from app.settings import get_settings
from config import get_logger
from app.models.user import Auth0UserInfo
import app.hardcoded as hardcoded

logger = get_logger(__name__)


settings = get_settings()

oauth = OAuth()
oauth.register(
    name="auth0",
    client_id=settings.auth0_client_id,
    client_secret=settings.auth0_client_secret,
    # https://auth0.com/docs/get-started/apis/scopes/openid-connect-scopes#standard-claims
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"https://{settings.auth0_domain}/.well-known/openid-configuration",
)


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


# https://docs.authlib.org/en/latest/client/fastapi.html
@router.get("/login", status_code=302)
async def login(
    request: Request, destination: Optional[str] = None
) -> RedirectResponse:
    """Redirects user to Auth0 login page. destination is the (optional) URL to redirect to after login."""
    if not destination:
        destination = "/"
    if not is_relative_url(URL(destination)):
        raise HTTPException(
            status_code=400, detail="destination must be a relative path"
        )
    request.session["destination"] = destination  # remember for later

    # after login, have Auth0 redirect to the /callback endpoint
    settings = get_settings()
    redirect_uri = f"{settings.site_url}{settings.api_v1_str}/auth/callback"
    return await oauth.auth0.authorize_redirect(request, redirect_uri)


@router.api_route("/callback", methods=["GET", "POST"], response_class=RedirectResponse)
async def callback(request: Request):
    """
    After Auth0 authenticates a user, it redirects here so the user's information can be stored in the session cookie.
    """

    try:
        token = await oauth.auth0.authorize_access_token(request)
    except (OAuth2Error, OAuthError) as exc:
        logger.warning(f"Invalid authentication request: {exc}")
        return RedirectResponse(url=request.url_for("login"))

    # Validate the received user information and store it in the session cookie
    user_info = Auth0UserInfo.model_validate(token["userinfo"])
    logger.info(f"Received authenticated user: {user_info.email}")

    if not hardcoded.email_can_signup(user_info.email):
        logger.warning(f"Rejecting unauthorized email: '{user_info.email}'")
        raise HTTPException(
            status_code=403, detail="Only VU emails are permitted at present."
        )
    # TODO: check if user exists in database and handle appropriately

    destination = request.session.get("destination") or "/"
    if not is_relative_url(URL(destination)):
        logger.warning(f"Overrding invalid destination: '{destination}'")
        destination = "/"

    # request.session["user"] = user.model_dump()
    return destination
    # referer = request.headers.get("Referer")
    # if referer is not None:
    #     return referer
