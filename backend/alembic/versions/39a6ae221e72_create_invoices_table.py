"""create invoices table

Revision ID: 39a6ae221e72
Revises: 0039a74b70e6
Create Date: 2025-07-03 15:08:01.234638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39a6ae221e72'
down_revision: Union[str, None] = '0039a74b70e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=True),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('invoice_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('paid_date', sa.DateTime(), nullable=True),
        sa.Column('pdf_url', sa.String(length=500), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('services_data', sa.JSON(), nullable=True),
        sa.Column('billing_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_invoices_lead_id', 'invoices', 'leads', ['lead_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_invoices_sale_id', 'invoices', 'sales', ['sale_id'], ['id'], ondelete='SET NULL')
    
    # Add indexes
    op.create_index('idx_invoices_lead_id', 'invoices', ['lead_id'])
    op.create_index('idx_invoices_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('idx_invoices_stripe_invoice_id', 'invoices', ['stripe_invoice_id'])
    op.create_index('idx_invoices_status', 'invoices', ['status'])
    op.create_index('idx_invoices_invoice_date', 'invoices', ['invoice_date'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_invoices_invoice_date', 'invoices')
    op.drop_index('idx_invoices_status', 'invoices')
    op.drop_index('idx_invoices_stripe_invoice_id', 'invoices')
    op.drop_index('idx_invoices_invoice_number', 'invoices')
    op.drop_index('idx_invoices_lead_id', 'invoices')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_invoices_sale_id', 'invoices', type_='foreignkey')
    op.drop_constraint('fk_invoices_lead_id', 'invoices', type_='foreignkey')
    
    # Drop table
    op.drop_table('invoices')
