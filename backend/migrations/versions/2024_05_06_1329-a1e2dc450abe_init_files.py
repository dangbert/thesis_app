"""init files

Revision ID: a1e2dc450abe
Revises: b5d6d7937f3b
Create Date: 2024-05-06 13:29:04.115045+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1e2dc450abe"
down_revision: Union[str, None] = "b5d6d7937f3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "file",
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("ext", sa.String(), nullable=False),
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_file_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file")),
    )
    op.create_table(
        "assignment_file",
        sa.Column("assignment_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignment.id"],
            name=op.f("fk_assignment_file_assignment_id_assignment"),
        ),
        sa.ForeignKeyConstraint(
            ["file_id"], ["file.id"], name=op.f("fk_assignment_file_file_id_file")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assignment_file")),
    )
    op.create_table(
        "course_file",
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["course_id"], ["course.id"], name=op.f("fk_course_file_course_id_course")
        ),
        sa.ForeignKeyConstraint(
            ["file_id"], ["file.id"], name=op.f("fk_course_file_file_id_file")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_course_file")),
    )
    op.add_column("attempt", sa.Column("file_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_attempt_file_id_file"), "attempt", "file", ["file_id"], ["id"]
    )
    op.drop_constraint("course_invite_key_key", "course", type_="unique")
    op.create_unique_constraint(op.f("uq_course_invite_key"), "course", ["invite_key"])
    op.drop_constraint("user_email_key", "user", type_="unique")
    op.drop_constraint("user_email_token_key", "user", type_="unique")
    op.create_unique_constraint(op.f("uq_user_email"), "user", ["email"])
    op.create_unique_constraint(op.f("uq_user_email_token"), "user", ["email_token"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f("uq_user_email_token"), "user", type_="unique")
    op.drop_constraint(op.f("uq_user_email"), "user", type_="unique")
    op.create_unique_constraint("user_email_token_key", "user", ["email_token"])
    op.create_unique_constraint("user_email_key", "user", ["email"])
    op.drop_constraint(op.f("uq_course_invite_key"), "course", type_="unique")
    op.create_unique_constraint("course_invite_key_key", "course", ["invite_key"])
    op.drop_constraint(op.f("fk_attempt_file_id_file"), "attempt", type_="foreignkey")
    op.drop_column("attempt", "file_id")
    op.drop_table("course_file")
    op.drop_table("assignment_file")
    op.drop_table("file")
    # ### end Alembic commands ###
