from fastapi import APIRouter, Request, HTTPException
import urllib.parse
from app.settings import get_settings
from config import get_logger
from authlib.integrations.starlette_client import OAuth  # type: ignore
from starlette.datastructures import URL
from starlette.responses import RedirectResponse
from typing import Optional

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
async def login(request: Request, redirect_uri: str = "") -> RedirectResponse:
    if not is_relative_url(URL(redirect_uri)):
        raise HTTPException(
            status_code=400, detail="redirect_uri must be a relative path"
        )

    request.session["redirect_uri"] = redirect_uri
    return await oauth.auth0.authorize_redirect(redirect_uri)
