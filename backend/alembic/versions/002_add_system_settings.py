"""Add system settings tables

Revision ID: 002
Revises: 
Create Date: 2025-04-30

"""
from alembic import op
import sqlalchemy as sa
import enum

# revision identifiers, used by Alembic.
revision = '002'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create system_integrations table
    op.create_table(
        'system_integrations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('twilio_api_key', sa.String(), nullable=True),
        sa.Column('twilio_account_sid', sa.String(), nullable=True),
        sa.Column('twilio_auth_token', sa.String(), nullable=True),
        sa.Column('twilio_integration_active', sa.Boolean(), default=False),
        sa.Column('mailgun_api_key', sa.String(), nullable=True),
        sa.Column('mailgun_domain', sa.String(), nullable=True),
        sa.Column('mailgun_region', sa.Enum('US', 'EU', name='regionenum'), nullable=True),
        sa.Column('mailgun_integration_active', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )

    # Create system_scheduling table
    op.create_table(
        'system_scheduling',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('agent_group_frequency', sa.Enum('MANUAL', 'DAILY', 'WEEKLY', 'CUSTOM_HOURS', name='frequencyenum'), nullable=True),
        sa.Column('agent_group_time', sa.String(), nullable=True),
        sa.Column('custom_hours_interval', sa.Integer(), nullable=True),
        sa.Column('agent_group_active', sa.Boolean(), default=False),
        sa.Column('campaign_launch_time', sa.String(), nullable=True),
        sa.Column('max_execution_duration', sa.Integer(), nullable=True),
        sa.Column('leads_per_campaign', sa.Integer(), default=50),
        sa.Column('max_simultaneous_campaigns', sa.Integer(), default=5),
        sa.Column('daily_report_active', sa.Boolean(), default=False),
        sa.Column('daily_report_time', sa.String(), nullable=True),
        sa.Column('report_channel_slack', sa.Boolean(), default=False),
        sa.Column('report_channel_email', sa.Boolean(), default=False),
        sa.Column('report_channel_dashboard', sa.Boolean(), default=False),
        sa.Column('knowledge_trigger_frequency', sa.Enum('MANUAL', 'DAILY', 'WEEKLY', 'CUSTOM_HOURS', name='frequencyenum'), nullable=True),
        sa.Column('max_learning_delay', sa.Integer(), default=7),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )

def downgrade():
    op.drop_table('system_scheduling')
    op.drop_table('system_integrations')
    op.execute('DROP TYPE IF EXISTS regionenum')
    op.execute('DROP TYPE IF EXISTS frequencyenum')
