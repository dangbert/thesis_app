from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app import getConfigForEnv

class Base(DeclarativeBase):
    """Base class for all DB models to inherit from."""

    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.current_timestamp())


# configClass = getConfigForEnv()
# DB_URI = configClass().getDbUri()

# engine = create_engine(DB_URI)
# print("created engine:")
# print(engine)

# database Session factory
#   https://docs.sqlalchemy.org/en/14/orm/session_basics.html#using-a-sessionmaker
# SessionFactory = sessionmaker(bind=engine)
# TODO: look into these params:
# SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
