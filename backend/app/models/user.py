from app.models.base import Base
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import secrets
from pydantic import BaseModel, EmailStr


class User(Base):
    __tablename__ = "user"
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # TODO: deprecate email_verified, the social loging with Auth0 handles this implicitly
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_token: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True, default=lambda: secrets.token_urlsafe(16)
    )


class Auth0UserInfo(BaseModel):
    """
    Schema for user info returned by Auth0 upon login.
    https://auth0.com/docs/api/authentication#user-profile
    """

    sub: str
    name: str
    email: EmailStr
