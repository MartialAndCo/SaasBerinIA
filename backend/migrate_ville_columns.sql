-- Migration manuelle pour ajouter les colonnes ville
-- et migrer les données existantes

-- 1. Ajouter les colonnes ville
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS ville VARCHAR;
ALTER TABLE niches ADD COLUMN IF NOT EXISTS ville VARCHAR;

-- 2. Migration des données existantes - CAMPAGNES
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
WHERE ville IS NULL;

-- 3. Nettoyage du champ name pour les campagnes
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
WHERE ville IS NOT NULL;

-- 4. Migration des données existantes - NICHES  
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
WHERE ville IS NULL;

-- 5. Nettoyage du champ name pour les niches
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
WHERE ville IS NOT NULL;

-- 6. Vérification des résultats
SELECT 'CAMPAGNES MIGREES' as type, name, ville FROM campaigns WHERE ville IS NOT NULL LIMIT 10;
SELECT 'NICHES MIGREES' as type, name, ville FROM niches WHERE ville IS NOT NULL LIMIT 10;
