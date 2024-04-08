# all models must be imported here for their respective tables to be created
from . import User, Course

# importing Base here (after all models are imported) for alembic
from . import Base
