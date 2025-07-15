"""add_stripe_fields_to_services_simple

Revision ID: bd9e52c95e72
Revises: 39a6ae221e72
Create Date: 2025-07-03 17:10:17.263370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd9e52c95e72'
down_revision: Union[str, None] = '39a6ae221e72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Stripe integration fields to services table and create sync table."""
    # Add Stripe fields to services table
    op.add_column('services', sa.Column('stripe_product_id', sa.String(length=255), nullable=True))
    op.add_column('services', sa.Column('stripe_price_id', sa.String(length=255), nullable=True))
    op.add_column('services', sa.Column('product_type', sa.String(length=20), nullable=True, default='one_time'))
    op.add_column('services', sa.Column('sync_with_stripe', sa.Boolean(), nullable=True, default=False))
    
    # Create indexes for Stripe fields
    op.create_index('ix_services_stripe_product_id', 'services', ['stripe_product_id'], unique=False)
    op.create_index('ix_services_stripe_price_id', 'services', ['stripe_price_id'], unique=False)
    
    # Create stripe_product_sync table
    op.create_table('stripe_product_sync',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_timestamp', sa.DateTime(), nullable=False),
        sa.Column('products_count', sa.Integer(), nullable=False),
        sa.Column('one_time_products', sa.Integer(), nullable=False, default=0),
        sa.Column('recurring_products', sa.Integer(), nullable=False, default=0),
        sa.Column('sync_status', sa.String(length=20), nullable=False, default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sync_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for sync table
    op.create_index('ix_stripe_product_sync_sync_timestamp', 'stripe_product_sync', ['sync_timestamp'], unique=False)
    op.create_index('ix_stripe_product_sync_sync_status', 'stripe_product_sync', ['sync_status'], unique=False)


def downgrade() -> None:
    """Remove Stripe integration fields and sync table."""
    # Drop sync table
    op.drop_index('ix_stripe_product_sync_sync_status', table_name='stripe_product_sync')
    op.drop_index('ix_stripe_product_sync_sync_timestamp', table_name='stripe_product_sync')
    op.drop_table('stripe_product_sync')
    
    # Drop indexes for Stripe fields
    op.drop_index('ix_services_stripe_price_id', table_name='services')
    op.drop_index('ix_services_stripe_product_id', table_name='services')
    
    # Remove Stripe fields from services table
    op.drop_column('services', 'sync_with_stripe')
    op.drop_column('services', 'product_type')
    op.drop_column('services', 'stripe_price_id')
    op.drop_column('services', 'stripe_product_id')
