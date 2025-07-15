"""Add payment notifications table only

Revision ID: f0b86d36b83f
Revises: 0943bb702aa0
Create Date: 2025-07-04 18:39:43.836412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0b86d36b83f'
down_revision: Union[str, None] = '0943bb702aa0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create payment_notifications table
    op.create_table('payment_notifications',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id')),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id')),
        sa.Column('stripe_event_id', sa.String(), unique=True, index=True),
        sa.Column('stripe_event_type', sa.String()),
        sa.Column('notification_type', sa.String()),
        sa.Column('amount', sa.Integer()),
        sa.Column('currency', sa.String(), default='eur'),
        sa.Column('client_name', sa.String()),
        sa.Column('client_email', sa.String()),
        sa.Column('stripe_data', sa.JSON()),
        sa.Column('sent_to_telegram', sa.Boolean(), default=False),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('payment_notifications')
