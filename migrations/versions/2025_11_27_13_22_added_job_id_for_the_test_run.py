"""Added job id for the test run

Revision ID: 09937d9792f6
Revises: f86ce9b63f97
Create Date: 2025-11-27 13:22:08.366107

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "09937d9792f6"
down_revision: Union[str, Sequence[str], None] = "f86ce9b63f97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("test_runs", sa.Column("job_id", sa.String(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("test_runs", "job_id")
