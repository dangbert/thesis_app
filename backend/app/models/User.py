from app.models.Base import Base
from sqlalchemy import Column, String, Boolean


class User(Base):
    __tablename__ = "user"
    email = Column(String, unique=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_token = Column(String, unique=True, nullable=True)
