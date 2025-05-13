"""Merge multiple heads

Revision ID: 14932dff94e9
Revises: 002, cdcff53e3f7b, f57d800fbe15
Create Date: 2025-05-01 14:40:25.509234

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14932dff94e9'
down_revision: Union[str, None] = ('002', 'cdcff53e3f7b', 'f57d800fbe15')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
