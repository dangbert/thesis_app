"""add group num

Revision ID: 9e86599b9a80
Revises: 03d7881322c8
Create Date: 2024-05-30 15:14:58.877396+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9e86599b9a80"
down_revision: Union[str, None] = "03d7881322c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "course_user_link", sa.Column("group_num", sa.Integer(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("course_user_link", "group_num")
    # ### end Alembic commands ###
