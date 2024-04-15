# all models must be imported here for their respective tables to be created
from .User import User
from .Course import Course, Assignment

# importing Base here (after all models are imported) for alembic
from . import Base
