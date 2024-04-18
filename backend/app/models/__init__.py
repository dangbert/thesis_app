# all models must be imported here for their respective tables to be created
from .user import User
from .course import Course, Assignment

# importing Base here (after all models are imported) for alembic
from .base import Base
