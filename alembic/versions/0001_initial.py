"""Initial schema: tutors and lessons

Revision ID: 0001
Revises:
Create Date: 2026-07-16

"""
import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tutors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tutors_email", "tutors", ["email"], unique=True)

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tutor_id",
            sa.Integer(),
            sa.ForeignKey("tutors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("student_name", sa.String(length=120), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lessons_tutor_id", "lessons", ["tutor_id"])
    op.create_index("ix_lessons_starts_at", "lessons", ["starts_at"])


def downgrade() -> None:
    op.drop_table("lessons")
    op.drop_table("tutors")
