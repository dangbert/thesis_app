from app.models.base import Base
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import secrets


class User(Base):
    __tablename__ = "user"
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_token: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True, default=lambda: secrets.token_urlsafe(16)
    )
