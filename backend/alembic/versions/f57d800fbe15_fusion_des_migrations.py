"""Fusion des migrations

Revision ID: f57d800fbe15
Revises: 20250422_130030, 5a169e59a4fe
Create Date: 2025-04-22 13:09:30.448445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f57d800fbe15'
down_revision: Union[str, None] = ('20250422_130030', '5a169e59a4fe')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
