from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional


class Base(DeclarativeBase):
    """Base class for all DB models to inherit from."""

    __abstract__ = True
    # https://docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#orm-declarative-models
    # https://www.postgresql.org/docs/current/functions-uuid.html
    id = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        # default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.current_timestamp()
    )
