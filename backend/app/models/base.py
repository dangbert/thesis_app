from datetime import datetime
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import MetaData, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PUUID
from uuid import UUID
from typing import Optional


# https://stackoverflow.com/q/71451982
# https://alembic.sqlalchemy.org/en/latest/naming.html
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
_Base = declarative_base(metadata=MetaData(naming_convention=convention))


class Base(_Base):  # type:ignore
    """Base class for all DB models to inherit from."""

    __abstract__ = True
    # https://docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#orm-declarative-models
    # https://www.postgresql.org/docs/current/functions-uuid.html
    id: Mapped[UUID] = mapped_column(
        #  as_uuid=True -> automatically convert postgres UUIDs to python native uuid.UUID type
        PUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.current_timestamp()
    )
