"""add_email_subject_instructions_to_messenger_directives

Revision ID: 98c872284ed6
Revises: 0687e706059c
Create Date: 2025-07-11 00:12:25.483774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98c872284ed6'
down_revision: Union[str, None] = '0687e706059c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter la colonne email_subject_instructions à la table messenger_directives
    op.add_column('messenger_directives', 
                  sa.Column('email_subject_instructions', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer la colonne email_subject_instructions
    op.drop_column('messenger_directives', 'email_subject_instructions')
