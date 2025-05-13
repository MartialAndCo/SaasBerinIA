# Intégration Base de Données

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [DatabaseQueryAgent](#databasequeryagent)
- [Configuration de la base de données](#configuration-de-la-base-de-données)
- [Utilisation](#utilisation)
- [Formats de données](#formats-de-données)
- [Dépannage](#dépannage)

## Vue d'ensemble

BerinIA utilise une base de données PostgreSQL pour stocker toutes les données du système, y compris les leads, les campagnes, les messages et les analyses. Cette documentation détaille l'intégration de la base de données avec le système, y compris l'agent spécialisé DatabaseQueryAgent qui permet d'interroger la base de données en langage naturel.

## DatabaseQueryAgent

Le DatabaseQueryAgent est un agent spécialisé qui permet d'interroger la base de données en langage naturel. Il traduit les questions en requêtes SQL et renvoie les résultats formatés.

### Fonctionnalités principales

- Traduction automatique des questions en requêtes SQL
- Préchargement du schéma de la base de données pour des réponses plus rapides
- Gestion de requêtes prédéfinies pour les questions courantes
- Support de différents formats d'entrée pour plus de flexibilité

## Configuration de la base de données

### Variables d'environnement

Le fichier `.env` dans `infra-ia/` et `backend/` doit contenir les informations de connexion à la base de données :

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=berinia
DB_USER=berinia_user
DB_PASSWORD=your_password
```

### Structure de la base de données

La structure principale de la base de données comprend les tables suivantes :

1. **leads** - Informations sur les leads prospectés
   - Inclut des champs pour l'analyse visuelle (ajoutés dans la migration `add_visual_analysis_fields.sql`)

2. **campaigns** - Campagnes de prospection

3. **messages** - Messages envoyés et reçus
   
4. **niches** - Niches commerciales exploitées

5. **stats** - Statistiques de performance

### Scripts de migration

Les scripts de migration sont situés dans `backend/migrations/` :

- `create_berinia_db.sql` - Création de la base initiale
- `add_messages_table.sql` - Ajout de la table de messages
- `add_missing_columns.sql` - Ajout de colonnes manquantes
- `add_visual_analysis_fields.sql` - Ajout des champs d'analyse visuelle

Pour appliquer une migration :

```bash
cd /root/berinia/backend
./apply_visual_analysis_migration.sh
```

## Utilisation

### Format d'entrée standard pour le DatabaseQueryAgent

```json
{
  "message": "Combien de leads avons-nous dans la base de données?",
  "parameters": {}
}
```

### Format d'entrée avec action directe

```json
{
  "action": "count_leads",
  "parameters": {}
}
```

### Actions directes supportées

- `count_leads` : Compte le nombre total de leads dans la base de données
- `active_conversations` : Récupère les conversations actives des derniers jours
- `conversion_rate` : Calcule le taux de conversion pour les dernières campagnes

### Exemples de requêtes

#### Requête simple

```
Combien de leads avons-nous dans la niche "plombier" ?
```

Génère une requête SQL comme :

```sql
SELECT COUNT(*) FROM leads WHERE niche = 'plombier';
```

#### Requête plus complexe

```
Quelles sont les 5 niches avec le meilleur taux de conversion ce mois-ci ?
```

Génère une requête SQL comme :

```sql
SELECT 
    n.name,
    COUNT(m.id) FILTER (WHERE m.response_status = 'positive') / COUNT(m.id)::float * 100 AS conversion_rate
FROM 
    niches n
JOIN 
    leads l ON l.niche_id = n.id
JOIN 
    messages m ON m.lead_id = l.id
WHERE 
    m.sent_at >= date_trunc('month', current_date)
GROUP BY 
    n.name
ORDER BY 
    conversion_rate DESC
LIMIT 5;
```

## Formats de données

### Format de sortie standard

```json
{
  "status": "success",
  "result": {
    "count": 2584,
    "message": "Il y a 2584 leads dans la base de données."
  }
}
```

### Format de sortie pour une requête complexe

```json
{
  "status": "success",
  "result": {
    "data": [
      {"niche": "plombier", "conversion_rate": 12.5},
      {"niche": "coach sportif", "conversion_rate": 11.8},
      {"niche": "ostéopathe", "conversion_rate": 10.3},
      {"niche": "avocat", "conversion_rate": 9.7},
      {"niche": "coiffeur", "conversion_rate": 9.2}
    ],
    "message": "Voici les 5 niches avec le meilleur taux de conversion ce mois-ci."
  }
}
```

## Dépannage

### Problèmes de connexion

Si vous rencontrez des problèmes de connexion à la base de données, vérifiez :

1. Que le service PostgreSQL est en cours d'exécution :
   ```bash
   sudo systemctl status postgresql
   ```

2. Que les variables d'environnement sont correctement définies :
   ```bash
   cd /root/berinia/backend
   python test_db_connection.py
   ```

3. Que l'utilisateur a les droits nécessaires :
   ```bash
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE berinia TO berinia_user;"
   ```

### Erreurs de requêtes

Si le DatabaseQueryAgent renvoie des erreurs lors de l'exécution de requêtes :

1. **"Aucune question ou requête fournie"**
   - Vérifiez que le message est bien inclus dans le champ "message" ou "question" de l'entrée
   - OU qu'une action reconnue est fournie dans le champ "action"
   - Vérifiez que le format JSON est correct et complet

2. **"Erreur lors de l'exécution de la requête SQL"**
   - Consultez les logs pour voir la requête SQL qui a échoué
   - Vérifiez que les tables et colonnes référencées existent
   - Testez directement la requête dans psql pour identifier l'erreur

### Commandes utiles

```bash
# Connexion à la base de données
sudo -u postgres psql berinia

# Affichage des tables
\dt

# Description d'une table
\d leads

# Exécution d'une requête SQL
SELECT COUNT(*) FROM leads;

# Quitter psql
\q
```

---

[Retour à l'accueil](../index.md) | [Documentation des agents →](../agents/meta-agent.md)
