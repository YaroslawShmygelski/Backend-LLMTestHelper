"""added url column to the Test

Revision ID: 185d39738816
Revises: 8803f516e09d
Create Date: 2025-11-03 17:35:15.068886

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "185d39738816"
down_revision: Union[str, Sequence[str], None] = "8803f516e09d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tests", sa.Column("url", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tests", "url")
