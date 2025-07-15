# Bot Telegram BerinIA

## 🤖 Vue d'ensemble

Le bot Telegram BerinIA (@BerinIABot) est une interface conversationnelle pour gérer et monitorer le système BerinIA directement depuis Telegram.

## 📱 Fonctionnalités

### 🎯 Menu Principal
- 📊 **Statistiques générales** - Vue d'ensemble des métriques
- 🎯 **Campagnes** - Gestion des campagnes de prospection
- 👥 **Leads** - Analyse et suivi des leads
- 📂 **Niches** - Gestion des niches de marché
- 🧠 **Système** - Administration et monitoring

### 📊 Statistiques
- Volume total de leads
- Taux de conversion globaux
- Répartition des réponses (positives/neutres/négatives)
- Historique des performances
- Compensation totale cumulée

### 🎯 Campagnes
- ✅ Voir les campagnes actives
- 📈 Consulter les statistiques détaillées
- 🚀 Lancer une nouvelle campagne
- 🔄 Relancer une campagne en pause
- 🛑 Stopper une campagne
- 📤 Exporter les données

### 👥 Leads
- 🔢 Nombre total de leads
- ✅ Taux de qualification
- 📄 Liste paginée des leads
- 🔍 Recherche par critères
- 📊 Répartition par statut
- 🧮 Calcul des compensations

### 📂 Niches
- 📄 Liste de toutes les niches
- 📊 Analyse des performances
- 🛑 Gestion des niches peu rentables
- 🆕 Proposition de nouvelles niches
- 🧠 Analyse de viabilité
- 📈 Campagnes associées

### 🧠 Système
- 🔁 État des agents IA
- 📆 Tâches planifiées
- 🔒 Logs de sécurité
- 🧠 Logs de décisions
- 🔄 Redémarrage système
- 🔧 État des services

## 🚀 Utilisation

### Premier contact
1. **Rechercher le bot** : @BerinIABot sur Telegram
2. **Démarrer** : Tapez `/start`
3. **Navigation** : Utilisez les boutons interactifs

### Commandes disponibles
- `/start` - Menu principal
- `/help` - Aide et documentation
- `/status` - État rapide du système

### Navigation
- **Boutons interactifs** : Cliquez sur les boutons pour naviguer
- **Retour** : Bouton "⬅️ Retour" dans chaque menu
- **Confirmation** : Actions critiques nécessitent une confirmation

### 🔄 Gestion du cycle de vie des campagnes
Le bot distingue clairement les actions sur les campagnes :

1. **🚀 Lancer une campagne** : Créer une nouvelle campagne de zéro
   - Sélection de niche + ville
   - Création dans la base de données
   - Status initial : "active"

2. **🔄 Relancer une campagne** : Réactiver une campagne en pause
   - Liste des campagnes inactives (paused, draft, completed)
   - Change le status vers "active"
   - Conserve tous les leads existants

3. **🛑 Stopper une campagne** : Mettre en pause une campagne active
   - Liste des campagnes actives
   - Change le status vers "paused"
   - Action réversible, données conservées

## 🔧 Configuration technique

### Fichiers principaux
```
infra-ia/telegram_bot/
├── main.py                    # Point d'entrée
├── config/settings.py         # Configuration
├── handlers/                  # Gestionnaires de menus
├── services/api_client.py     # Client API BerinIA
├── utils/keyboards.py         # Claviers interactifs
└── utils/formatters.py        # Formatage des réponses
```

## 🌐 Intégration API

### Vue d'ensemble
Le bot Telegram communique avec l'API BerinIA via le client `BeriniaAPIClient` qui centralise tous les appels REST vers `http://localhost:8000/api`.

### 📊 Endpoints Statistiques
```bash
# Statistiques générales
GET /api/stats

# Statistiques tableau de bord
GET /api/dashboard
```

### 🎯 Endpoints Campagnes
```bash
# Lister toutes les campagnes
GET /api/campaigns?status=active&limit=10

# Détails d'une campagne
GET /api/campaigns/{id}

# Changer le statut d'une campagne
PUT /api/campaigns/{id}/status
Content-Type: application/json
{"status": "active|paused|completed"}

# Campagnes actives (endpoint spécialisé)
GET /api/campaigns-management/active

# Campagnes inactives (endpoint spécialisé)
GET /api/campaigns-management/inactive

# Créer une nouvelle campagne
POST /api/campaigns-management/launch
Content-Type: application/json
{
  "niche_id": 1,
  "city": "Paris",
  "target_leads": 50,
  "description": "Nouvelle campagne"
}

# Relancer une campagne
PUT /api/campaigns-management/{id}/restart

# Stopper une campagne
PUT /api/campaigns-management/{id}/stop
```

### 👥 Endpoints Leads
```bash
# Compter les leads
GET /api/leads/count

# Statistiques leads
GET /api/leads/stats

# Lister les leads avec pagination
GET /api/leads?limit=10&offset=0&status=qualified

# Rechercher des leads
GET /api/leads/search?search=exemple

# Détails d'un lead
GET /api/leads/{id}

# Compensation d'un lead
GET /api/leads/{id}/compensation
```

### 📂 Endpoints Niches
```bash
# Lister les niches
GET /api/niches

# Détails d'une niche
GET /api/niches/{id}

# Performance d'une niche
GET /api/niches/{id}/performance

# Campagnes d'une niche
GET /api/niches/{id}/campaigns

# Analyser viabilité d'une niche
POST /api/niches/analyze
Content-Type: application/json
{"niche_name": "Dentistes"}
```

### 🧠 Endpoints Système
```bash
# État du système
GET /api/system/status

# État des agents
GET /api/agents

# Détails d'un agent
GET /api/agents/{name}

# Redémarrer un agent
POST /api/agents/{name}/restart

# Tâches planifiées
GET /api/tasks

# Logs système
GET /api/logs?limit=50

# État des services
GET /api/services/status

# Redémarrer un service
POST /api/services/{name}/restart
```

### 🔗 Client API
Le fichier `services/api_client.py` encapsule tous ces appels :

```python
class BeriniaAPIClient:
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.timeout = 30
    
    # Exemples de méthodes
    def get_active_campaigns(self) -> List[Dict]:
        return self._make_request('GET', '/campaigns-management/active')
    
    def start_campaign(self, campaign_id: str) -> Dict:
        data = {"status": "active"}
        return self._make_request('PUT', f'/campaigns/{campaign_id}/status', json=data)
    
    def restart_campaign(self, campaign_id: str) -> Dict:
        return self._make_request('PUT', f'/campaigns-management/{campaign_id}/restart')
```

### ⚙️ Gestion des erreurs
```python
def _make_request(self, method: str, endpoint: str, **kwargs):
    try:
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API {method} {endpoint}: {e}")
        return None
```

### 🔄 Endpoints corrigés récemment

### Correction des niches (4 juin 2025)
- **Problème résolu** : `'list' object has no attribute 'get'` lors de l'affichage des niches
- **Cause** : L'API `/niches` retourne directement une liste `[...]` au lieu d'un objet `{"niches": [...]}`
- **Solution appliquée** : 
  - Ajout de la méthode `_extract_list_from_response()` dans le client API
  - Gestion automatique des deux formats de réponse (liste directe ou objet avec clé)
- **Impact** : Fonctionnalité "📂 Lister les niches" entièrement fonctionnelle

### Correction des agents (4 juin 2025)
- **Problème résolu** : Informations d'agents affichées comme "N/A" et redirection HTTP 307
- **Cause** : 
  - Endpoint `/agents` redirige vers `/agents/` 
  - Champ `last_activity` inexistant (le vrai champ est `derniere_execution`)
- **Solution appliquée** :
  - Correction de l'endpoint vers `/agents/` dans le client API
  - Mise à jour du formatter pour utiliser `derniere_execution`
  - Ajout du formatage de date pour afficher "Jamais exécuté" si null
- **Impact** : État des agents avec informations de dernière exécution correctes

### Correction des campagnes (précédent)
- **Problème résolu** : `start_campaign()` utilisait `POST /campaigns/{id}/start` (inexistant)
- **Solution appliquée** : Utilise maintenant `PUT /campaigns/{id}/status` avec `{"status": "active"}`
- **Impact** : Bouton "Relancer une campagne" entièrement fonctionnel

### Service systemd
```bash
# Statut du service
sudo systemctl status berinia-telegram-bot

# Logs en temps réel
sudo journalctl -u berinia-telegram-bot.service -f

# Redémarrage
sudo systemctl restart berinia-telegram-bot
```

### Variables d'environnement (.env)
```bash
TELEGRAM_BOT_TOKEN=7655899986:AAHcKqAzUoysvQE64qRBue19BQw5QIqykfA
TELEGRAM_ADMIN_IDS=5380358558
TELEGRAM_API_BASE_URL=http://localhost:8000/api
```

## 🔐 Sécurité

### Authentification
- **Liste blanche** : Seuls les IDs autorisés peuvent utiliser le bot
- **ID admin configuré** : 5380358558
- **Vérification automatique** : Chaque interaction est vérifiée

### Logs et audit
- **Logs système** : Toutes les actions sont tracées
- **Journal systemd** : Historique complet des événements
- **Erreurs** : Gestion robuste avec fallback

## 🛠️ Maintenance

### Ajout d'un nouvel administrateur
1. Modifier `.env` : `TELEGRAM_ADMIN_IDS=5380358558,NOUVEL_ID`
2. Redémarrer le service : `sudo systemctl restart berinia-telegram-bot`

### Diagnostic des problèmes
```bash
# Vérifier le statut
sudo systemctl status berinia-telegram-bot

# Voir les logs détaillés
sudo journalctl -u berinia-telegram-bot.service --since="1 hour ago"

# Tester la configuration
cd /root/berinia/infra-ia/telegram_bot
source ../.venv/bin/activate
python -c "from config.settings import *; print('Config OK')"
```

### Mise à jour du bot
1. Modifier les fichiers dans `infra-ia/telegram_bot/`
2. Redémarrer le service : `sudo systemctl restart berinia-telegram-bot`
3. Vérifier les logs pour s'assurer du bon fonctionnement

## 📈 Monitoring

### Métriques système
- **Utilisation CPU** : Limitée à 25%
- **Mémoire** : Limitée à 500MB
- **Redémarrage automatique** : En cas d'erreur

### Alertes
- **Échec de démarrage** : Logs dans journalctl
- **Erreurs API** : Notifications dans les logs
- **Perte de connexion** : Reconnexion automatique

## 🔄 Évolutions prévues

### Fonctionnalités en développement
- **Notifications proactives** : Alertes automatiques
- **Recherche avancée** : Filtres personnalisés
- **Rapports personnalisés** : Export sur mesure
- **Intégration calendrier** : Planification avancée

### Améliorations techniques
- **Pagination avancée** : Gestion de grandes listes
- **Cache intelligent** : Performance optimisée
- **Multi-utilisateurs** : Gestion des permissions
- **API REST complète** : Intégration externe

## 📞 Support

En cas de problème :
1. **Vérifier les logs** : `sudo journalctl -u berinia-telegram-bot.service -f`
2. **Redémarrer le service** : `sudo systemctl restart berinia-telegram-bot`
3. **Vérifier la configuration** : Variables d'environnement et permissions
4. **Contacter l'administrateur** : Si le problème persiste

## 🆕 Gestion Avancée des Tâches (NOUVEAU)

### Vue d'ensemble
Le système de gestion des tâches a été entièrement repensé pour supporter 4 types de tâches avec workflow complet et paramètres avancés.

### 🔧 Types de tâches disponibles

#### **SYSTEM_RECURRING** 🔧
- **Usage** : Tâches système permanentes critiques
- **Caractéristiques** :
  - Jamais supprimées automatiquement
  - Priorité système (haute)
  - Pas de dégradation de priorité
  - Pour fonctions core du système

#### **BUSINESS_RECURRING** 💼
- **Usage** : Tâches business temporaires
- **Caractéristiques** :
  - Date de fin automatique configurable
  - Nettoyage après 30 jours par défaut
  - Dégradation de priorité dans le temps
  - Pour campagnes et processus business

#### **ONE_TIME** ⚡
- **Usage** : Actions ponctuelles
- **Caractéristiques** :
  - Exécution unique puis suppression
  - Nettoyage immédiat après exécution
  - Max 1 exécution autorisée
  - Pour tâches urgentes ou tests

#### **CONDITIONAL** ❓
- **Usage** : Tâches déclenchées par conditions
- **Caractéristiques** :
  - Exécution selon condition prédéfinie
  - Vérification périodique des conditions
  - Nettoyage après 7 jours par défaut
  - Pour automatisation intelligente

### 🎯 Workflow de création

#### Étape 1 : Sélection du type
Interface avec 4 boutons pour choisir le type de tâche selon les besoins.

#### Étape 2 : Choix de l'agent
Sélection parmi les agents disponibles :
- 📧 **MessagingAgent** - Messages et communications
- 🎯 **ProspectionSupervisor** - Supervision prospection  
- 📊 **PivotStrategyAgent** - Analyse stratégique
- 🛡️ **TaskWatchdogAgent** - Surveillance système
- 🔍 **ScrapingSupervisorAgent** - Supervision scraping
- 💬 **ResponseInterpreterAgent** - Interprétation réponses
- 📅 **FollowUpAgent** - Suivi et relances
- 🧹 **CleanerAgent** - Nettoyage données

#### Étape 3 : Action spécifique
Actions disponibles selon l'agent sélectionné :

**MessagingAgent** :
- 📨 Envoyer message
- 📬 Messages groupés
- 📋 Créer template
- 📅 Planifier relance
- 🔄 Contact automatique

**ProspectionSupervisor** :
- 🎯 Démarrer prospection
- 📊 Surveiller campagnes
- 📈 Rapport quotidien
- 🔍 Analyse performance
- ✅ Qualification leads

**FollowUpAgent** :
- 📅 Planifier relance
- 📧 Envoyer rappel
- 🔍 Analyser réponses
- 📊 Rapport suivi

#### Étape 4 : Paramètres d'action
Configuration selon l'action choisie :

**Pour "Envoyer message"** :
- 🎯 Tous les leads qualifiés
- 👤 Lead spécifique (avec liste)
- 🎯 Leads d'une campagne (avec sélection)
- 📂 Leads d'une niche (avec sélection)

**Pour "Démarrer prospection"** :
- 📂 Sélectionner niche
- 🏙️ Sélectionner ville

**Pour "Envoyer rappel"** :
- 🎯 Campagne spécifique
- ⏰ Délai 24h/48h/personnalisé

#### Étape 5 : Conditions (si CONDITIONAL)
Conditions prédéfinies disponibles :
- 📧 **no_response_after_24h** - Aucune réponse après 24h
- 📧 **no_response_after_48h** - Aucune réponse après 48h  
- 📊 **low_campaign_performance** - Performance campagne faible
- 👥 **no_new_leads_today** - Aucun nouveau lead aujourd'hui
- 🔄 **system_idle_for_1h** - Système inactif depuis 1h
- 📈 **conversion_rate_below_5** - Taux conversion < 5%
- ⚠️ **error_rate_above_10** - Taux erreur > 10%
- 🎯 **campaign_budget_75** - Budget campagne à 75%

#### Étape 6 : Configuration temporelle
Selon le type de tâche :

**SYSTEM_RECURRING** :
- ⏰ Toutes les heures
- 📅 Quotidien  
- 📆 Hebdomadaire

**BUSINESS_RECURRING** :
- Récurrence + date de fin optionnelle
- Configuration du nettoyage automatique

**ONE_TIME** :
- ⚡ Maintenant
- ⏰ Dans 1 heure
- 📅 Dans 24h

**CONDITIONAL** :
- 🔍 Vérification toutes les heures
- 🔍 Vérification toutes les 6h

### 🔌 API avancée

#### Endpoint de création avancée
```bash
POST /api/tasks
Content-Type: application/json
{
  "action": "send_message",
  "agent_id": 1,
  "parameters": {
    "created_via": "telegram_bot_advanced",
    "target": "qualified_leads",
    "task_type": "business_recurring",
    "task_behavior": {
      "task_type": "business_recurring",
      "auto_cleanup": true,
      "cleanup_after_days": 30,
      "end_date": "2025-07-04T21:52:00",
      "priority_decay": true
    }
  },
  "priority": 3,
  "scheduled_time": "2025-06-05T08:00:00",
  "is_recurring": true,
  "recurrence_interval": 86400
}
```

#### Paramètres task_behavior
```json
{
  "task_type": "system_recurring|business_recurring|one_time|conditional",
  "auto_cleanup": true|false,
  "cleanup_after_days": 30,
  "end_date": "2025-12-31T23:59:59",
  "condition": "no_response_after_24h",
  "max_executions": 1,
  "priority_decay": true|false
}
```

### 🧠 Intelligence du système

#### Gestion automatique selon le type
- **SYSTEM** : Priorité préservée, jamais de nettoyage
- **BUSINESS** : Dégradation progressive, fin automatique
- **ONE_TIME** : Suppression immédiate après exécution
- **CONDITIONAL** : Vérification intelligente des conditions

#### État de création persistant
Le workflow maintient l'état de création par utilisateur pour permettre une navigation fluide entre les étapes.

#### Validation et sécurité
- Validation des paramètres à chaque étape
- Gestion d'erreurs robuste avec fallbacks
- Nettoyage automatique des sessions expirées

### 📊 Monitoring avancé

#### Nouvelles métriques
- Répartition par type de tâche
- Taux de réussite par condition
- Performance des agents selon les actions
- Analyse des patterns d'utilisation

#### Logs détaillés
- Traçabilité complète de création
- Historique des modifications
- Audit des exécutions conditionnelles

---

**Status actuel** : ✅ Opérationnel avec système avancé
**Dernière mise à jour** : 4 juin 2025 - Ajout workflow complet tâches avancées
**Version** : 2.0.0
