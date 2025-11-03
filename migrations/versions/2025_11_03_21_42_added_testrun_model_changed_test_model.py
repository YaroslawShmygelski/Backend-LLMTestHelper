"""Added TestRun model changed Test model

Revision ID: f86ce9b63f97
Revises: 185d39738816
Create Date: 2025-11-03 21:42:37.697699

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "f86ce9b63f97"
down_revision: Union[str, Sequence[str], None] = "185d39738816"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("llm_model", sa.String(), nullable=True),
        sa.Column("llm_prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("llm_completion_tokens", sa.Integer(), nullable=True),
        sa.Column("llm_answering_time", sa.Float(), nullable=True),
        sa.Column("run_content", JSONB(), nullable=False),
        sa.Column("submitted_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_runs_id"), "test_runs", ["id"], unique=False)
    op.create_index(
        op.f("ix_test_runs_test_id"), "test_runs", ["test_id"], unique=False
    )
    op.create_index(
        op.f("ix_test_runs_user_id"), "test_runs", ["user_id"], unique=False
    )
    op.add_column("tests", sa.Column("is_submitted", sa.Boolean(), nullable=False))
    op.alter_column(
        "tests",
        "content",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=JSONB(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "tests",
        "content",
        existing_type=JSONB(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
    )
    op.drop_column("tests", "is_submitted")
    op.drop_index(op.f("ix_test_runs_user_id"), table_name="test_runs")
    op.drop_index(op.f("ix_test_runs_test_id"), table_name="test_runs")
    op.drop_index(op.f("ix_test_runs_id"), table_name="test_runs")
    op.drop_table("test_runs")
