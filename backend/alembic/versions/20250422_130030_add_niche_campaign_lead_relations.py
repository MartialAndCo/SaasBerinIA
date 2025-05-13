"""add relations between niches, campaigns, and leads"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250422_130030'
down_revision = '5a169e59a4fe'
branch_labels = None
depends_on = None


def upgrade():
    # Création de la table niches
    op.create_table(
        'niches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nom', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date_creation', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('statut', sa.Enum('Rentable', 'En test', 'Abandonnée', name='statut_type'), nullable=False, server_default='En test'),
        sa.Column('taux_conversion', sa.Float(), server_default='0.0'),
        sa.Column('cout_par_lead', sa.Float(), server_default='0.0'),
        sa.Column('recommandation', sa.Enum('Continuer', 'Développer', 'Optimiser', 'Pivoter', name='recommandation_type'), nullable=False, server_default='Continuer')
    )

    # Création de la table campaigns
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nom', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('date_creation', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('statut', sa.String(), nullable=False, server_default='active'),
        sa.Column('niche_id', sa.Integer(), sa.ForeignKey('niches.id', ondelete="CASCADE"), nullable=False)
    )

    # Création de la table leads
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nom', sa.String(), nullable=False),
        sa.Column('email', sa.String(), unique=True, index=True),
        sa.Column('telephone', sa.String(), unique=True, index=True),
        sa.Column('date_creation', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('statut', sa.String(), nullable=False, server_default='new'),
        sa.Column('campagne_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete="CASCADE"), nullable=False)
    )


def downgrade():
    op.drop_table('leads')
    op.drop_table('campaigns')
    op.drop_table('niches')
