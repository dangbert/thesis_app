from fastapi import Header, HTTPException, Request, Depends
from typing_extensions import Annotated
from collections.abc import Generator
from .database import SessionFactory, engine
from sqlalchemy import select
from sqlalchemy.orm import Session
import app.models as models
from config import get_logger

logger = get_logger(__name__)

# async def get_token_header(x_token: Annotated[str, Header()]):
#     if x_token != "fake-super-secret-token":
#         raise HTTPException(status_code=400, detail="X-Token header invalid")


def get_db() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def cur_user(request: Request, session: SessionDep) -> models.User:
    """Get the current authenticated user, or raise an HTTPException."""

    user_info = request.session.get("user")
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
        # return RedirectResponse(url=LOGIN_URL)

    statement = select(models.User).where(models.User.email == user_info["email"])
    user = session.execute(statement).scalars().first()
    if not user:
        logger.error(
            f"User in session but not found in database '{user_info['email']}'"
        )
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not authenticated")

    # TODO: check session expiration time ETA
    # refresh the user's session here so it doesn't expire
    # request.session["user"] = user.to_public().model_dump(mode="json")

    return user


AuthUserDep = Annotated[models.User, Depends(cur_user)]
