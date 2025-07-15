"""add_instantly_campaign_id_to_campaigns

Revision ID: 0687e706059c
Revises: f0b86d36b83f
Create Date: 2025-07-07 14:04:54.378342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0687e706059c'
down_revision: Union[str, None] = 'f0b86d36b83f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter la colonne instantly_campaign_id à la table campaigns
    op.add_column('campaigns', sa.Column('instantly_campaign_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer la colonne instantly_campaign_id de la table campaigns
    op.drop_column('campaigns', 'instantly_campaign_id')
