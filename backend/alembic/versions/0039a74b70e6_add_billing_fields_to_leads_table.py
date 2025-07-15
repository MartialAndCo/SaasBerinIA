"""add billing fields to leads table

Revision ID: 0039a74b70e6
Revises: 941a85366a89
Create Date: 2025-07-03 15:07:12.207369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0039a74b70e6'
down_revision: Union[str, None] = '941a85366a89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add billing fields to leads table
    op.add_column('leads', sa.Column('billing_address', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('billing_city', sa.String(length=255), nullable=True))
    op.add_column('leads', sa.Column('billing_postal_code', sa.String(length=20), nullable=True))
    op.add_column('leads', sa.Column('billing_country', sa.String(length=100), nullable=True))
    op.add_column('leads', sa.Column('vat_number', sa.String(length=50), nullable=True))
    op.add_column('leads', sa.Column('billing_email', sa.String(length=255), nullable=True))
    op.add_column('leads', sa.Column('billing_contact_name', sa.String(length=255), nullable=True))
    op.add_column('leads', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))
    
    # Add index for stripe_customer_id for faster lookups
    op.create_index('idx_leads_stripe_customer_id', 'leads', ['stripe_customer_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index
    op.drop_index('idx_leads_stripe_customer_id', 'leads')
    
    # Remove billing fields from leads table
    op.drop_column('leads', 'stripe_customer_id')
    op.drop_column('leads', 'billing_contact_name')
    op.drop_column('leads', 'billing_email')
    op.drop_column('leads', 'vat_number')
    op.drop_column('leads', 'billing_country')
    op.drop_column('leads', 'billing_postal_code')
    op.drop_column('leads', 'billing_city')
    op.drop_column('leads', 'billing_address')
