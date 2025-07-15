"""add_ville_column_to_campaigns_and_niches

Revision ID: 4c2d25f02243
Revises: 14932dff94e9
Create Date: 2025-06-04 18:25:44.631776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c2d25f02243'
down_revision: Union[str, None] = '14932dff94e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ville column to campaigns and niches tables."""
    
    # 1. Ajouter la colonne ville aux campagnes
    op.add_column('campaigns', sa.Column('ville', sa.String(), nullable=True))
    
    # 2. Ajouter la colonne ville aux niches
    op.add_column('niches', sa.Column('ville', sa.String(), nullable=True))
    
    # 3. Migration des données existantes - CAMPAGNES
    # Extraction intelligente ville/métier depuis le name existant
    op.execute("""
        UPDATE campaigns SET 
            ville = CASE 
                WHEN name LIKE '%Paris%' THEN 'Paris'
                WHEN name LIKE '%Lyon%' THEN 'Lyon'
                WHEN name LIKE '%Marseille%' THEN 'Marseille'
                WHEN name LIKE '%Toulouse%' THEN 'Toulouse'
                WHEN name LIKE '%Nice%' THEN 'Nice'
                WHEN name LIKE '%Bordeaux%' THEN 'Bordeaux'
                WHEN name LIKE '%Lille%' THEN 'Lille'
                WHEN name LIKE '%Nantes%' THEN 'Nantes'
                WHEN name LIKE '%Strasbourg%' THEN 'Strasbourg'
                WHEN name LIKE '%Montpellier%' THEN 'Montpellier'
                ELSE NULL
            END
    """)
    
    # Nettoyage du champ name pour les campagnes
    op.execute("""
        UPDATE campaigns SET 
            name = CASE 
                WHEN ville IS NOT NULL THEN 
                    TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                        name, 
                        ' Paris', ''), 
                        ' Lyon', ''), 
                        ' Marseille', ''), 
                        ' Toulouse', ''), 
                        ' Nice', ''), 
                        ' Bordeaux', ''), 
                        ' Lille', ''), 
                        ' Nantes', ''), 
                        ' Strasbourg', ''), 
                        ' Montpellier', ''))
                ELSE name
            END
        WHERE ville IS NOT NULL
    """)
    
    # 4. Migration des données existantes - NICHES  
    op.execute("""
        UPDATE niches SET 
            ville = CASE 
                WHEN name LIKE '%Paris%' THEN 'Paris'
                WHEN name LIKE '%Lyon%' THEN 'Lyon'
                WHEN name LIKE '%Marseille%' THEN 'Marseille'
                WHEN name LIKE '%Toulouse%' THEN 'Toulouse'
                WHEN name LIKE '%Nice%' THEN 'Nice'
                WHEN name LIKE '%Bordeaux%' THEN 'Bordeaux'
                WHEN name LIKE '%Lille%' THEN 'Lille'
                WHEN name LIKE '%Nantes%' THEN 'Nantes'
                WHEN name LIKE '%Strasbourg%' THEN 'Strasbourg'
                WHEN name LIKE '%Montpellier%' THEN 'Montpellier'
                ELSE NULL
            END
    """)
    
    # Nettoyage du champ name pour les niches
    op.execute("""
        UPDATE niches SET 
            name = CASE 
                WHEN ville IS NOT NULL THEN 
                    TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                        name, 
                        ' Paris', ''), 
                        ' Lyon', ''), 
                        ' Marseille', ''), 
                        ' Toulouse', ''), 
                        ' Nice', ''), 
                        ' Bordeaux', ''), 
                        ' Lille', ''), 
                        ' Nantes', ''), 
                        ' Strasbourg', ''), 
                        ' Montpellier', ''))
                ELSE name
            END
        WHERE ville IS NOT NULL
    """)


def downgrade() -> None:
    """Remove ville column and restore original names."""
    
    # 1. Restaurer les noms originaux des campagnes
    op.execute("""
        UPDATE campaigns SET 
            name = CASE 
                WHEN ville IS NOT NULL THEN name || ' ' || ville
                ELSE name
            END
        WHERE ville IS NOT NULL
    """)
    
    # 2. Restaurer les noms originaux des niches
    op.execute("""
        UPDATE niches SET 
            name = CASE 
                WHEN ville IS NOT NULL THEN name || ' ' || ville
                ELSE name
            END
        WHERE ville IS NOT NULL
    """)
    
    # 3. Supprimer les colonnes ville
    op.drop_column('campaigns', 'ville')
    op.drop_column('niches', 'ville')
