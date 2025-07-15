"""remove_ville_from_niches_keep_only_campaigns

Revision ID: 941a85366a89
Revises: 4c2d25f02243
Create Date: 2025-06-04 18:59:05.428041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '941a85366a89'
down_revision: Union[str, None] = '4c2d25f02243'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove ville column from niches table and clean data."""
    
    # 1. Nettoyer les noms des niches (retirer les villes qui s'y seraient glissées)
    op.execute("""
        UPDATE niches SET 
            name = CASE 
                WHEN name LIKE '%Paris%' THEN 
                    TRIM(REPLACE(name, 'Paris', ''))
                WHEN name LIKE '%Lyon%' THEN 
                    TRIM(REPLACE(name, 'Lyon', ''))
                WHEN name LIKE '%Marseille%' THEN 
                    TRIM(REPLACE(name, 'Marseille', ''))
                WHEN name LIKE '%Toulouse%' THEN 
                    TRIM(REPLACE(name, 'Toulouse', ''))
                WHEN name LIKE '%Nice%' THEN 
                    TRIM(REPLACE(name, 'Nice', ''))
                WHEN name LIKE '%Bordeaux%' THEN 
                    TRIM(REPLACE(name, 'Bordeaux', ''))
                WHEN name LIKE '%Lille%' THEN 
                    TRIM(REPLACE(name, 'Lille', ''))
                WHEN name LIKE '%Nantes%' THEN 
                    TRIM(REPLACE(name, 'Nantes', ''))
                WHEN name LIKE '%Strasbourg%' THEN 
                    TRIM(REPLACE(name, 'Strasbourg', ''))
                WHEN name LIKE '%Montpellier%' THEN 
                    TRIM(REPLACE(name, 'Montpellier', ''))
                ELSE name
            END
    """)
    
    # 2. Supprimer les doublons de niches (même métier)
    op.execute("""
        DELETE FROM niches 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM niches 
            GROUP BY LOWER(TRIM(name))
        )
    """)
    
    # 3. Supprimer la colonne ville des niches
    op.drop_column('niches', 'ville')


def downgrade() -> None:
    """Add back ville column to niches."""
    
    # Rajouter la colonne ville aux niches
    op.add_column('niches', sa.Column('ville', sa.String(), nullable=True))
    
    # Note: Les données ne seront pas restaurées automatiquement
    # car elles ont été nettoyées et dédupliquées
