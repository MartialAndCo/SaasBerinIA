# Documentation Technique : Modifications Système BerinIA - Mai 2025

## Table des matières

1. [Introduction](#introduction)
2. [Résumé des interventions](#résumé-des-interventions)
3. [Diagnostic et résolution des problèmes de base de données](#diagnostic-et-résolution-des-problèmes-de-base-de-données)
   - [Identification des erreurs](#identification-des-erreurs)
   - [Amélioration de la connexion à la base de données](#amélioration-de-la-connexion-à-la-base-de-données)
   - [Modernisation du module DatabaseService](#modernisation-du-module-databaseservice)
   - [Adaptation des requêtes SQL](#adaptation-des-requêtes-sql)
4. [Améliorations de l'intelligence conversationnelle](#améliorations-de-lintelligence-conversationnelle)
   - [Problématique des salutations répétitives](#problématique-des-salutations-répétitives)
   - [Enrichissement du contexte temporel](#enrichissement-du-contexte-temporel)
   - [Structuration avancée de l'historique](#structuration-avancée-de-lhistorique)
   - [Post-traitement intelligent des réponses](#post-traitement-intelligent-des-réponses)
5. [Outils de diagnostic développés](#outils-de-diagnostic-développés)
   - [Scripts de test de connexion](#scripts-de-test-de-connexion)
   - [Scripts d'analyse de structure de table](#scripts-danalyse-de-structure-de-table)
   - [Surveillance des erreurs système](#surveillance-des-erreurs-système)
6. [Tests et validation](#tests-et-validation)
7. [Recommandations pour l'avenir](#recommandations-pour-lavenir)

## Introduction

Ce document technique présente l'ensemble des interventions réalisées sur le système BerinIA en mai 2025. Ces interventions ont visé à résoudre plusieurs problèmes critiques affectant les fonctionnalités centrales du système, notamment la connexion à la base de données PostgreSQL et l'intelligence conversationnelle des agents de messagerie.

## Résumé des interventions

Les interventions réalisées se sont articulées autour de deux axes majeurs :

1. **Résolution des problèmes d'infrastructure**
   - Correction des erreurs d'authentification à la base de données
   - Mise à jour du module DatabaseService pour la compatibilité avec SQLAlchemy moderne
   - Adaptation des requêtes SQL aux structures de tables existantes
   - Renforcement de la robustesse face aux erreurs de base de données

2. **Augmentation de l'intelligence conversationnelle**
   - Élimination des formules de salutation répétitives dans les conversations
   - Implémentation d'une conscience temporelle dans les échanges
   - Restructuration complète de la présentation de l'historique conversationnel
   - Ajout d'un post-traitement intelligent des réponses générées

Ces interventions ont été accompagnées par le développement d'outils de diagnostic dédiés permettant d'identifier précisément les causes des problèmes et de valider les solutions mises en place.

## Diagnostic et résolution des problèmes de base de données

### Identification des erreurs

L'analyse des logs système a révélé plusieurs erreurs récurrentes :

```
[ERROR] password authentication failed for user "postgres"
[ERROR] cannot convert dictionary update sequence element #0 to a sequence
[ERROR] column "direction" does not exist
```

Ces erreurs indiquaient trois problèmes distincts mais interconnectés :
1. Mauvaise configuration des identifiants de base de données
2. Incompatibilité avec l'API moderne de SQLAlchemy
3. Références à des colonnes inexistantes dans le schéma de la base de données

### Amélioration de la connexion à la base de données

Le problème d'authentification a été résolu en modifiant le fichier `core/db.py` :

```python
# Avant
load_dotenv()
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Après
load_dotenv("/root/berinia/infra-ia/.env")
DB_USER = os.getenv("DB_USER", "berinia_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "berinia_pass")
```

Ces modifications garantissent :
- Le chargement du fichier .env correct via un chemin absolu
- L'utilisation des identifiants par défaut corrects en cas d'absence de variables d'environnement

### Modernisation du module DatabaseService

La classe `DatabaseService` a été mise à jour pour être compatible avec l'API moderne de SQLAlchemy :

```python
@staticmethod
def execute_query(query: str, params: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None) -> List[Dict[str, Any]]:
    with engine.connect() as connection:
        sql = sa.text(query)
        
        if params is None:
            result = connection.execute(sql)
        else:
            result = connection.execute(sql, params)
            
        return [dict(row._mapping) for row in result]
```

Principales améliorations :
- Support des types Union pour les paramètres (compatibilité avec différents formats)
- Utilisation de `sa.text()` pour convertir les requêtes en TextClause
- Accès aux résultats via `row._mapping` (API SQLAlchemy moderne)
- Gestion explicite des cas avec/sans paramètres

### Adaptation des requêtes SQL

La méthode `get_conversation_history` du `MessagingAgent` a été complètement revue pour s'adapter au schéma réel de la base de données :

```python
def get_conversation_history(self, lead_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        # Vérification et conversion du lead_id
        try:
            lead_id_int = int(lead_id)
        except (ValueError, TypeError):
            self.speak(f"lead_id non valide pour conversion en entier: {lead_id}", target="ProspectionSupervisor")
            return []
        
        # Requête principale utilisant uniquement les colonnes existantes
        query = """
            SELECT 
                id, lead_id, content, 
                sent_date as sent_at,
                type, status,
                CASE 
                    WHEN type = 'reply' THEN 'inbound'
                    ELSE 'outbound'
                END as direction
            FROM messages
            WHERE lead_id = :lead_id
            ORDER BY sent_date DESC
            LIMIT :limit
        """
        
        results = self.db.fetch_all(query, {"lead_id": lead_id_int, "limit": limit})
        return list(reversed(results)) if results else []
    
    except Exception as e:
        self.speak(f"Erreur: {str(e)}", target="ProspectionSupervisor")
        
        # Requête de secours simplifiée en cas d'échec
        try:
            simplified_query = """
                SELECT id, lead_id, content, sent_date as sent_at,
                       'outbound' as direction
                FROM messages
                WHERE lead_id = :lead_id
                ORDER BY sent_date DESC
                LIMIT :limit
            """
            results = self.db.fetch_all(simplified_query, {"lead_id": lead_id_int, "limit": limit})
            return list(reversed(results)) if results else []
        except Exception as e2:
            self.speak(f"Échec requête secours: {str(e2)}", target="ProspectionSupervisor")
            return []
```

Améliorations notables :
- Vérification et conversion du lead_id en entier (type attendu par la base de données)
- Utilisation exclusive des colonnes existantes dans la table messages
- Génération dynamique de la colonne "direction" via une expression CASE
- Mécanisme de fallback avec une requête simplifiée en cas d'échec

## Améliorations de l'intelligence conversationnelle

### Problématique des salutations répétitives

Le système présentait un problème d'intelligence conversationnelle : il commençait systématiquement chaque message par "Bonjour!" ou une autre salutation, même lorsqu'il s'agissait de réponses successives dans une même conversation, ce qui donnait l'impression d'un manque de continuité et de naturel dans les échanges.

### Enrichissement du contexte temporel

La méthode `generate_contextual_response` a été enrichie pour fournir un contexte temporel précis au modèle LLM :

```python
# Préparation des métadonnées conversationnelles
current_time = datetime.datetime.now()
messages_count = len(conversation_history) + 1  # +1 pour le message actuel
is_first_message = messages_count <= 1

# Déterminer le temps écoulé depuis le dernier message
time_since_last_message = None
time_description = "Premier message"

if not is_first_message and conversation_history:
    try:
        last_msg_time_str = conversation_history[-1].get("sent_at", "")
        if last_msg_time_str:
            # Parsing flexible de l'horodatage
            try:
                last_msg_time = datetime.datetime.fromisoformat(last_msg_time_str)
            except ValueError:
                try:
                    last_msg_time = datetime.datetime.strptime(last_msg_time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_msg_time = current_time - datetime.timedelta(minutes=5)  # Fallback
            
            time_since_last_message = current_time - last_msg_time
            
            # Description en langage naturel du temps écoulé
            if time_since_last_message.days > 0:
                time_description = f"Il y a {time_since_last_message.days} jour(s)"
            elif time_since_last_message.seconds // 3600 > 0:
                time_description = f"Il y a {time_since_last_message.seconds // 3600} heure(s)"
            elif time_since_last_message.seconds // 60 > 0:
                time_description = f"Il y a {time_since_last_message.seconds // 60} minute(s)"
            else:
                time_description = "À l'instant"
    except Exception as e:
        time_description = "Temps indéterminé"
```

Ces informations temporelles permettent au modèle de comprendre :
- S'il s'agit d'un premier message ou d'une suite de conversation
- Combien de temps s'est écoulé depuis le dernier échange
- Le nombre total de messages dans la conversation

### Structuration avancée de l'historique

L'historique de conversation a été complètement restructuré pour fournir un contexte riche et explicite au modèle LLM :

```python
# Création d'un historique de conversation structuré et enrichi
history_text = ""
if conversation_history:
    history_text += f"=== CONVERSATION ({messages_count - 1} message(s) précédent(s)) ===\n\n"
    
    for i, msg in enumerate(conversation_history):
        # Extraction et formatage des informations du message
        direction = "BerinIA → Lead" if msg.get("direction") == "outbound" else "Lead → BerinIA"
        content = msg.get("content", "")
        date = msg.get("sent_at", "")
        
        # Formatage de l'horodatage pour une meilleure lisibilité
        try:
            date_obj = datetime.datetime.fromisoformat(date)
            formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M:%S")
        except:
            formatted_date = date
        
        # Construction structurée de l'entrée d'historique
        history_text += f"MESSAGE #{i+1} - {formatted_date}\n"
        history_text += f"[{direction}] {content}\n\n"
    
    # Séparation claire pour le nouveau message
    history_text += f"=== NOUVEAU MESSAGE (#{messages_count}) - {current_time.strftime('%d/%m/%Y à %H:%M:%S')} ===\n"
    history_text += f"[Lead → BerinIA] {message}\n\n"
else:
    # Cas du premier message
    history_text += "=== PREMIER MESSAGE DE LA CONVERSATION ===\n"
    history_text += f"Date et heure: {current_time.strftime('%d/%m/%Y à %H:%M:%S')}\n"
    history_text += f"[Lead → BerinIA] {message}\n\n"
```

Cette structure améliore la compréhension du contexte par le modèle grâce à :
- L'indication explicite du numéro de chaque message
- Le formatage clair des horodatages en format lisible
- La distinction visuelle entre les différents messages
- La démarcation claire entre historique et nouveau message

### Post-traitement intelligent des réponses

Un mécanisme de post-traitement a été implémenté pour éliminer automatiquement les salutations superflues lorsqu'il ne s'agit pas d'un premier message :

```python
# Post-traitement pour supprimer les salutations superflues si ce n'est pas le premier message
if not is_first_message:
    # Modèles de salutations à détecter et supprimer
    greeting_patterns = [
        r'^Bonjour.*?,\s*',
        r'^Salut.*?,\s*',
        r'^Cher.*?,\s*',
        r'^Bien\s+le\s+bonjour.*?,\s*',
        r'^Bonsoir.*?,\s*',
        r'^Bien\s+le\s+bonsoir.*?,\s*',
        r'^Hello.*?,\s*',
        r'^Coucou.*?,\s*',
    ]
    
    # Application des expressions régulières
    for pattern in greeting_patterns:
        response_text = re.sub(pattern, '', response_text, flags=re.IGNORECASE)
    
    # Correction de la casse après suppression
    if response_text and not response_text[0].isupper() and len(response_text) > 1:
        response_text = response_text[0].upper() + response_text[1:]
```

Ce post-traitement :
- Détecte une variété de formules de salutation en français
- Les supprime uniquement dans les messages de suivi (pas le premier message)
- Corrige automatiquement la capitalisation après suppression
- S'adapte à différentes variantes grâce aux expressions régulières

## Outils de diagnostic développés

Plusieurs scripts diagnostiques ont été développés pour analyser et résoudre les problèmes :

### Scripts de test de connexion

`/tmp/test_db_connection.py` - Un script pour tester la connexion à la base de données :
- Affichage des variables d'environnement chargées
- Test direct de connexion via SQLAlchemy
- Vérification des paramètres de connexion

`/tmp/simple_db_check.py` - Un test simplifié de la connexion :
- Affichage de la configuration de connexion
- Tests séparés avec et sans paramètres SQL
- Liste des tables disponibles dans la base de données

### Scripts d'analyse de structure de table

`/tmp/check_table_structure.py` - Un script pour analyser la structure de la table messages :
- Vérification de l'existence de la table
- Listing détaillé des colonnes avec leurs types et contraintes
- Test de requêtes simplifiées

`/tmp/check_messages_table.py` - Un outil d'analyse plus détaillé :
- Affichage des métadonnées des colonnes (types, limites, valeurs par défaut)
- Test de requêtes compatibles avec la structure réelle
- Génération de suggestions pour améliorer les requêtes

### Surveillance des erreurs système

`/tmp/monitor_db_errors.py` - Un outil de surveillance des erreurs :
- Analyse des logs système pour détecter les erreurs de base de données
- Vérification de la configuration .env
- Résumé consolidé de l'état du système

`/tmp/final_test.py` - Un test complet de l'infrastructure :
- Validation du fichier .env
- Test de la connexion à la base de données
- Test du service webhook
- Vérification de la configuration globale

## Tests et validation

L'ensemble des modifications a été validé par une série de tests :

1. **Tests unitaires** des composants modifiés
   - Vérification de la connexion à la base de données
   - Validation des requêtes SQL
   - Test du post-traitement des réponses

2. **Tests d'intégration** du système complet
   - Simulation d'échanges SMS via le webhook
   - Vérification de la persistance en base de données
   - Validation des réponses générées

3. **Analyse des logs système** après modifications
   - Disparition des erreurs d'authentification
   - Absence d'erreurs SQL
   - Vérification du bon fonctionnement du post-traitement

Les tests ont confirmé la résolution des problèmes ciblés et l'amélioration significative de l'intelligence conversationnelle du système.

## Recommandations pour l'avenir

Pour maintenir et améliorer le système BerinIA, nous recommandons :

1. **Standardisation des configurations**
   - Centraliser les fichiers .env dans des emplacements prévisibles
   - Documenter les paramètres attendus et leurs valeurs par défaut
   - Mettre en place des vérifications automatiques de la configuration

2. **Renforcement de la gestion d'erreurs**
   - Ajouter des mécanismes de retry pour les opérations de base de données
   - Implémenter des circuits breakers pour éviter la surcharge en cas de défaillance
   - Améliorer la journalisation avec des contextes explicites

3. **Évolution de l'intelligence conversationnelle**
   - Développer des mécanismes de détection du ton et de l'intention
   - Améliorer la gestion des conversations longues (résumé, références)
   - Intégrer des informations contextuelles supplémentaires (historique client, préférences)

4. **Migration vers des pratiques modernes de développement**
   - Adopter TypeScript pour les composants frontend
   - Utiliser des ORM modernes pour la gestion des bases de données
   - Implémenter des tests automatisés et l'intégration continue
