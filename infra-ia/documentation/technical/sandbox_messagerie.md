# Sandbox de Messagerie BerinIA

## Vue d'ensemble

Le Sandbox de Messagerie est un environnement de test permettant d'optimiser les stratégies de messaging avant leur déploiement sur de vrais prospects. Il offre une simulation réaliste des conversations avec des profils prospects personnalisables.

## Architecture

### Composants Backend

#### 1. Modèles de données (`app/models/sandbox.py`)

**SandboxLead** : Lead de test avec tous les champs du modèle Lead standard
- Informations de base (nom, email, entreprise, etc.)
- Données d'analyse visuelle (scores, maturité du site, etc.)
- Champs spécifiques au sandbox (plateforme de test, template utilisé)

**SandboxConversation** : Stockage des conversations de test
- Messages au format JSON
- Métadonnées de conversation (plateforme, statut)

**SandboxTemplate** : Templates prédéfinis pour créer rapidement des profils
- Données pré-configurées par secteur d'activité
- Profils types (restaurant, e-commerce, artisan)

#### 2. API Endpoints (`app/api/endpoints/sandbox.py`)

- `GET /api/sandbox/templates` : Récupère les templates prédéfinis
- `POST /api/sandbox/leads` : Crée un lead de test
- `GET /api/sandbox/leads` : Liste les leads de test
- `POST /api/sandbox/conversation` : Gère les conversations (démarrage/réponses)
- `DELETE /api/sandbox/leads/{id}` : Supprime un lead de test

#### 3. Simulation IA

Le système simule intelligemment les réponses de l'agent de messaging en fonction :
- Du contenu du message utilisateur (détection d'objections)
- Des informations du profil prospect
- De la plateforme utilisée (SMS vs Email)

**Exemples de réponses automatiques :**
- Objection "pas intéressé" → Questionnement sur les problèmes actuels
- Objection "trop cher" → Discussion sur le ROI et le budget
- "Déjà un prestataire" → Exploration de la satisfaction actuelle

### Composants Frontend

#### 1. Interface principale (`components/dashboard/sandbox-dashboard.tsx`)

**Onglet "Créer Profil" :**
- Formulaire complet avec tous les champs du modèle Lead
- Templates rapides pour différents secteurs
- Choix de la plateforme de test (SMS/Email)
- Validation en temps réel

**Onglet "Conversation" :**
- Chat en temps réel avec l'IA
- Affichage du profil prospect actif
- Interface intuitive pour tester différentes réponses
- Historique des messages

**Onglet "Paramètres" :**
- Configuration avancée (à venir)
- Utilise les prompts de production

#### 2. Intégration (`components/dashboard/messenger-config.tsx`)

- Bouton "Sandbox" bien visible dans la page messagerie
- Notification de la nouvelle fonctionnalité
- Navigation fluide vers l'interface de test

## Base de données

### Tables créées

```sql
-- Leads de test avec structure identique aux vrais leads
sandbox_leads (
    -- Champs identiques au modèle Lead
    -- + champs spécifiques : is_test, test_platform, template_used
)

-- Conversations de test
sandbox_conversations (
    sandbox_lead_id, messages, platform, status, notes
)

-- Templates prédéfinis
sandbox_templates (
    name, description, template_data, category
)
```

### Migration

Script : `backend/migrations/add_sandbox_tables.sql`
- Création des tables avec index optimisés
- Insertion des templates par défaut
- Compatible PostgreSQL et SQLite

## Templates prédéfinis

### 1. Restaurant Traditionnel
```json
{
    "first_name": "Jean",
    "company": "Le Gourmand",
    "industry": "Restauration",
    "score": 65,
    "visual_score": 45,
    "website_maturity": "basique"
}
```

### 2. E-commerce Moderne
```json
{
    "first_name": "Marie",
    "company": "Boutique Tendance",
    "industry": "Commerce",
    "score": 85,
    "visual_score": 90,
    "website_maturity": "avancé"
}
```

### 3. Artisan Local
```json
{
    "first_name": "Pierre",
    "company": "Plomberie Moreau",
    "industry": "Artisanat",
    "score": 70,
    "visual_score": 55,
    "website_maturity": "intermédiaire"
}
```

## Utilisation

### 1. Création d'un profil de test

1. Accéder au sandbox via le bouton dans la page messagerie
2. Utiliser un template ou créer un profil personnalisé
3. Choisir la plateforme (SMS ou Email)
4. Valider pour créer le lead de test

### 2. Test de conversation

1. Cliquer sur "Démarrer la conversation"
2. L'IA envoie son premier message basé sur les prompts de production
3. Répondre en tant que prospect pour tester les réactions
4. Analyser les réponses de l'agent pour optimiser les stratégies

### 3. Cas d'usage typiques

**Test d'objections :**
- "Pas intéressé" → Observer la technique de rebond
- "Trop cher" → Tester la gestion des préoccupations budgétaires
- "Déjà un prestataire" → Analyser l'approche de différenciation

**Test de personnalisation :**
- Différents secteurs d'activité
- Divers niveaux de maturité digitale
- Profils de tailles d'entreprise variées

## Tests et validation

### Script de test automatisé

`backend/test_sandbox.py` vérifie :
- Connexion à la base de données
- Exécution des migrations
- Fonctionnement des modèles
- Simulation des réponses IA
- Templates prédéfinis

### Commande de test

```bash
cd backend
python test_sandbox.py
```

## Avantages

### 1. Test en conditions réelles
- Utilise les vrais prompts de production
- Même logique que le MessagingAgent
- Données complètes identiques aux vrais leads

### 2. Sécurité
- Aucun impact sur les vrais prospects
- Environnement isolé avec flag `is_test`
- Données de test clairement identifiées

### 3. Optimisation rapide
- Tests instantanés de nouvelles stratégies
- Comparaison A/B de différentes approches
- Affinement des prompts sans risque

### 4. Formation et démonstration
- Outil de formation pour les équipes
- Démonstrations client sécurisées
- Validation des nouvelles fonctionnalités

## Extensions futures

### 1. Intégration MessagingAgent réel
- Remplacement de la simulation par le vrai agent
- Utilisation des prompts configurables
- Test des modifications de configuration en direct

### 2. Analytics avancées
- Métriques de performance par template
- Comparaison de stratégies
- Taux de conversion simulés

### 3. Templates dynamiques
- Création de templates personnalisés
- Import/export de configurations
- Partage entre utilisateurs

### 4. Scénarios complexes
- Conversations multi-tours
- Gestion des relances automatiques
- Simulation de réponses prospect variables

## Configuration

### Variables d'environnement

Utilise la configuration existante de l'application principal.

### Déploiement

Le sandbox est automatiquement déployé avec l'application principale :
- Tables créées via migration
- API endpoints exposés
- Interface accessible dans le dashboard

### Maintenance

- Nettoyage périodique des leads de test anciens
- Sauvegarde des conversations importantes
- Mise à jour des templates selon les retours utilisateur

## Sécurité

### Isolation des données
- Tables séparées pour les données de test
- Flag `is_test` sur tous les enregistrements
- Aucune interaction avec les vrais leads

### Permissions
- Accès limité aux utilisateurs autorisés
- Logs des actions de test
- Traçabilité des modifications

Cette fonctionnalité sandbox revolutionne la façon d'optimiser les stratégies de messaging en offrant un environnement de test sûr et réaliste.
