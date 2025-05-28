# Guide d'utilisation de l'API Instantly pour agents IA

Ce document fournit les informations essentielles pour qu'un agent IA puisse interagir avec l'API Instantly.ai. Il est structuré de manière à faciliter l'implémentation programmatique des requêtes API.

## 1. Configuration de base

### Authentification
```python
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
```

Pour obtenir une clé API:
1. Accéder à "integrations" dans l'interface
2. Cliquer sur "API Keys" dans la barre latérale gauche
3. Cliquer sur "Create API Key"
4. Entrer un nom et sélectionner les scopes appropriés
5. Copier immédiatement la clé (affichée une seule fois)

### Point de terminaison de base
```
https://api.instantly.ai/api/v2/
```

### Limite de débit
- 600 requêtes par minute par workspace
- Statut 429 si dépassement
- Limite partagée entre API v1 et v2

## 2. Opérations principales

### 2.1 Gestion des comptes email

#### Lister les comptes
```python
# GET /api/v2/accounts
response = requests.get("https://api.instantly.ai/api/v2/accounts", headers=headers)
accounts = response.json()["items"]
```

Paramètres optionnels:
- `limit`: nombre de comptes à retourner (max 100)
- `search`: recherche par texte
- `status`: filtrer par statut (1=Active, 2=Paused)
- `provider_code`: filtrer par fournisseur (2=Google, 3=Microsoft)

#### Créer un compte
```python
# POST /api/v2/accounts
account_data = {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "provider_code": 2,  # 1=IMAP/SMTP, 2=Google, 3=Microsoft, 4=AWS
    "imap_username": "username",
    "imap_password": "password",
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "smtp_username": "username",
    "smtp_password": "password",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587
}
response = requests.post("https://api.instantly.ai/api/v2/accounts", json=account_data, headers=headers)
new_account = response.json()
```

#### Obtenir, mettre à jour ou supprimer un compte
```python
# GET /api/v2/accounts/{email}
account = requests.get(f"https://api.instantly.ai/api/v2/accounts/user@example.com", headers=headers).json()

# PATCH /api/v2/accounts/{email}
update_data = {"first_name": "Jane", "daily_limit": 150}
updated = requests.patch(f"https://api.instantly.ai/api/v2/accounts/user@example.com", json=update_data, headers=headers).json()

# DELETE /api/v2/accounts/{email}
deleted = requests.delete(f"https://api.instantly.ai/api/v2/accounts/user@example.com", headers=headers).json()
```

#### Pause/Reprise d'un compte
```python
# POST /api/v2/accounts/{email}/pause
paused = requests.post(f"https://api.instantly.ai/api/v2/accounts/user@example.com/pause", headers=headers).json()

# POST /api/v2/accounts/{email}/resume
resumed = requests.post(f"https://api.instantly.ai/api/v2/accounts/user@example.com/resume", headers=headers).json()
```

### 2.2 Campagnes

#### Lister les campagnes
```python
# GET /api/v2/campaigns
response = requests.get("https://api.instantly.ai/api/v2/campaigns", headers=headers)
campaigns = response.json()["items"]
```

Paramètres optionnels:
- `limit`: nombre de campagnes à retourner (max 100)
- `search`: recherche par nom
- `starting_after`: ID pour la pagination

#### Créer une campagne
```python
# POST /api/v2/campaigns
campaign_data = {
    "name": "Ma Campagne",
    "campaign_schedule": {
        "schedules": [
            {
                "name": "Planning principal",
                "timing": {
                    "from": "09:00",
                    "to": "17:00"
                },
                "days": {
                    "0": True,
                    "1": True,
                    "2": True,
                    "3": True,
                    "4": True,
                    "5": False,
                    "6": False
                },
                "timezone": "Europe/Paris"
            }
        ]
    }
}
response = requests.post("https://api.instantly.ai/api/v2/campaigns", json=campaign_data, headers=headers)
new_campaign = response.json()
```

#### Activer/Pauser une campagne
```python
# POST /api/v2/campaigns/{id}/activate
# POST /api/v2/campaigns/{id}/pause
campaign_id = "0196d41a-01ce-73f3-a1c7-eaf05fc7454d"
response = requests.post(f"https://api.instantly.ai/api/v2/campaigns/{campaign_id}/activate", headers=headers)
```

#### Obtenir les analytiques de campagne
```python
# GET /api/v2/campaigns/analytics
analytics = requests.get("https://api.instantly.ai/api/v2/campaigns/analytics", 
                        params={"id": "0196d41a-01d1-72da-96c5-8a5892ca52ef"}, 
                        headers=headers).json()

# Analytiques quotidiennes
daily = requests.get("https://api.instantly.ai/api/v2/campaigns/analytics/daily", 
                    params={"campaign_id": "0196d41a-01d2-766b-a320-d7d44071a2be"}, 
                    headers=headers).json()

# Analytiques par étape
steps = requests.get("https://api.instantly.ai/api/v2/campaigns/analytics/steps", 
                    params={"campaign_id": "0196d41a-01d3-71c1-86b4-f1aee403a5f0"}, 
                    headers=headers).json()
```

### 2.3 Gestion des leads

#### Ajouter un lead
```python
# POST /api/v2/leads
lead_data = {
    "email": "prospect@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "company_name": "Acme Inc",
    "campaign": "0196d419-f537-7819-819b-33d7287dd380",  # ID de la campagne
    "list_id": "0196d419-f537-7819-819b-33dcab7cafa3",   # ID de la liste (optionnel)
    "custom_variables": {                                # Variables personnalisées
        "source": "website",
        "interest_level": "high"
    }
}
response = requests.post("https://api.instantly.ai/api/v2/leads", json=lead_data, headers=headers)
new_lead = response.json()
```

Options supplémentaires:
- `skip_if_in_workspace`: éviter les doublons dans le workspace
- `skip_if_in_campaign`: éviter les doublons dans la campagne
- `verify_leads_on_import`: vérifier l'email lors de l'import

#### Rechercher des leads
```python
# POST /api/v2/leads/list
search_data = {
    "campaign": "0196d419-ff93-7be5-95fc-9d85314c9238",  # Optionnel: ID de campagne
    "search": "Smith",                                    # Optionnel: recherche par nom/email
    "limit": 50,                                          # Nombre de résultats
    "list_id": "0196d419-ff93-7be5-95fc-9d867d3d34aa",   # Optionnel: ID de liste
    "is_unread": True,                                    # Optionnel: filtrer non lus
    "lt_interest_status": 1                               # Optionnel: filtrer par statut d'intérêt
}
response = requests.post("https://api.instantly.ai/api/v2/leads/list", json=search_data, headers=headers)
leads = response.json()["items"]
```

#### Mettre à jour le statut d'intérêt
```python
# POST /api/v2/leads/update-interest-status
status_data = {
    "lead_email": "prospect@example.com",
    "interest_value": 1,  # 1=Interested, 2=Meeting Booked, 3=Meeting Completed, 4=Closed
                          # 0=Out of Office, -1=Not Interested, -2=Wrong Person, -3=Lost
    "campaign_id": "0196d419-ff93-7be5-95fc-9d85314c9238"  # Optionnel
}
response = requests.post("https://api.instantly.ai/api/v2/leads/update-interest-status", json=status_data, headers=headers)
```

#### Déplacer des leads
```python
# POST /api/v2/leads/move
move_data = {
    "campaign": "0196d419-ff93-7be5-95fc-9d85314c9238",  # Source (optionnel)
    "to_campaign_id": "0196d41a-020c-72b9-b686-07e357e1ca74",  # Destination
    "limit": 100  # Nombre de leads à déplacer
}
response = requests.post("https://api.instantly.ai/api/v2/leads/move", json=move_data, headers=headers)
```

### 2.4 Email

#### Répondre à un email
```python
# POST /api/v2/emails/reply
reply_data = {
    "reply_to_uuid": "123e4567-e89b-12d3-a456-426614174000",  # ID de l'email auquel répondre
    "eaccount": "user@example.com",                           # Compte expéditeur
    "subject": "Re: Votre demande",
    "body": {
        "html": "<p>Bonjour, merci pour votre message.</p>",
        "text": "Bonjour, merci pour votre message."
    }
}
response = requests.post("https://api.instantly.ai/api/v2/emails/reply", json=reply_data, headers=headers)
```

#### Lister les emails
```python
# GET /api/v2/emails
params = {
    "limit": 10,
    "is_unread": True,
    "campaign_id": "0196d419-ff93-7be5-95fc-9d85314c9238"  # Optionnel
}
response = requests.get("https://api.instantly.ai/api/v2/emails", params=params, headers=headers)
emails = response.json()["items"]
```

Autres filtres:
- `mode`: "emode_focused", "emode_others", "emode_all"
- `lead`: filtrer par email du lead
- `email_type`: "received", "sent", "manual"

#### Compter les emails non lus
```python
# GET /api/v2/emails/unread/count
count = requests.get("https://api.instantly.ai/api/v2/emails/unread/count", headers=headers).json()["count"]
```

#### Marquer les emails comme lus
```python
# POST /api/v2/emails/threads/{thread_id}/mark-as-read
thread_id = "0196d419-f5f8-7166-af75-a4017b4ce1e1"
response = requests.post(f"https://api.instantly.ai/api/v2/emails/threads/{thread_id}/mark-as-read", headers=headers)
```

### 2.5 Vérification d'email

```python
# POST /api/v2/email-verification
verification_data = {
    "email": "prospect@example.com",
    "webhook_url": "https://your-webhook.com/callback"  # Optionnel
}
response = requests.post("https://api.instantly.ai/api/v2/email-verification", json=verification_data, headers=headers)
verification = response.json()

# Vérifier le statut (si webhook non utilisé)
status = requests.get(f"https://api.instantly.ai/api/v2/email-verification/prospect@example.com", headers=headers).json()
```

## 3. Sous-workspaces (gestion multi-workspaces)

Pour exécuter une requête au nom d'un sous-workspace, ajoutez l'en-tête:
```python
headers["x-as-workspace"] = "ID_DU_SOUS_WORKSPACE"
```

## 4. Webhooks

### Format d'événement webhook
```json
{
    "timestamp": "2025-05-15T13:19:53.336Z",
    "event_type": "email_opened",
    "workspace": "uuid-workspace",
    "campaign_id": "uuid-campaign",
    "campaign_name": "Nom de la campagne",
    "lead_email": "prospect@example.com",
    "email_account": "sender@example.com",
    "step": 1,
    "variant": 1
}
```

Types d'événements:
- `email_sent`: Email envoyé
- `email_opened`: Email ouvert
- `reply_received`: Réponse reçue
- `link_clicked`: Lien cliqué
- `lead_interested`: Lead intéressé
- `lead_meeting_booked`: Meeting réservé
- `lead_meeting_completed`: Meeting effectué

## 5. Conseils d'implémentation pour IA

1. **Authentification persistante**: Conservez le token API et vérifiez son état à chaque requête. Prévoyez le renouvellement si nécessaire.

2. **Gestion des erreurs**: Implémentez une logique robuste pour les statuts suivants:
   - 401: Non autorisé (token invalide ou expiré)
   - 429: Limite de débit dépassée (attendre et réessayer)
   - 404: Ressource non trouvée
   - 400: Requête mal formée (vérifier les paramètres)

3. **Pagination**: Pour les endpoints qui retournent beaucoup de résultats, utilisez le paramètre `next_starting_after` retourné dans les réponses pour paginer.
   ```python
   response = requests.get("https://api.instantly.ai/api/v2/leads/list", json={"limit": 100}, headers=headers)
   next_token = response.json().get("next_starting_after")
   if next_token:
       next_page = requests.get("https://api.instantly.ai/api/v2/leads/list", 
                             json={"limit": 100, "starting_after": next_token}, 
                             headers=headers)
   ```

4. **Traitement asynchrone**: Pour les opérations lourdes comme l'importation ou le déplacement de leads, utilisez les webhooks ou polling pour surveiller l'état du job en arrière-plan.

5. **Contexte des leads**: Stockez les données clés des leads dans votre propre mémoire/base de données pour éviter des requêtes API redondantes.

6. **Rate limiting**: Implémentez un mécanisme de backoff exponentiel pour les requêtes qui échouent avec 429.
   ```python
   def make_request_with_backoff(url, method="GET", data=None, max_retries=5):
       retries = 0
       while retries < max_retries:
           response = requests.request(method, url, json=data, headers=headers)
           if response.status_code != 429:
               return response
           
           # Exponentiel backoff (1s, 2s, 4s, 8s, 16s)
           wait_time = 2**retries
           time.sleep(wait_time)
           retries += 1
       
       # Dernière tentative après tous les retries
       return requests.request(method, url, json=data, headers=headers)
   ```

7. **Traitement par lots**: Pour les opérations sur un grand nombre de leads, répartissez-les en plusieurs requêtes pour éviter les timeouts et les limites de taille de payload.

## 6. Exemple de flux complet

```python
import requests
import time

# 1. Configuration de l'authentification
API_KEY = "votre_clé_api"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
base_url = "https://api.instantly.ai/api/v2"

# 2. Vérifier les comptes disponibles
response = requests.get(f"{base_url}/accounts", headers=headers)
if response.status_code != 200:
    raise Exception(f"Erreur lors de la récupération des comptes: {response.status_code}")

accounts = response.json()["items"]
if not accounts:
    raise Exception("Aucun compte disponible")

# Sélectionner le premier compte actif
active_account = next((acc for acc in accounts if acc["status"] == 1), None)
if not active_account:
    raise Exception("Aucun compte actif disponible")

# 3. Créer ou récupérer une campagne
response = requests.get(f"{base_url}/campaigns", headers=headers)
campaigns = response.json()["items"]
campaign_id = campaigns[0]["id"] if campaigns else None

if not campaign_id:
    # Créer une campagne si aucune n'existe
    campaign_data = {
        "name": "Nouvelle Campagne Auto",
        "campaign_schedule": {
            "schedules": [
                {
                    "name": "Default", 
                    "timing": {"from": "09:00", "to": "17:00"}, 
                    "days": {"0": True, "1": True, "2": True, "3": True, "4": True, "5": False, "6": False},
                    "timezone": "Europe/Paris"
                }
            ]
        },
        "email_list": [active_account["email"]]  # Utiliser le compte actif
    }
    response = requests.post(f"{base_url}/campaigns", json=campaign_data, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erreur lors de la création de la campagne: {response.status_code}")
    
    new_campaign = response.json()
    campaign_id = new_campaign["id"]

# 4. Ajouter un lead à la campagne
lead_data = {
    "email": "nouveau_prospect@example.com",
    "first_name": "Pierre",
    "last_name": "Martin",
    "company_name": "Entreprise XYZ",
    "campaign": campaign_id,
    "custom_variables": {
        "source": "api_integration",
        "segment": "enterprise"
    }
}

response = requests.post(f"{base_url}/leads", json=lead_data, headers=headers)
if response.status_code != 200:
    raise Exception(f"Erreur lors de l'ajout du lead: {response.status_code}")

lead = response.json()

# 5. Activer la campagne si elle n'est pas active
response = requests.get(f"{base_url}/campaigns/{campaign_id}", headers=headers)
campaign = response.json()
if campaign["status"] != 1:  # Si pas active
    response = requests.post(f"{base_url}/campaigns/{campaign_id}/activate", headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erreur lors de l'activation de la campagne: {response.status_code}")

# 6. Surveiller les réponses (en boucle ou webhook)
def check_for_responses():
    response = requests.get(f"{base_url}/emails", 
                        params={"campaign_id": campaign_id, "is_unread": True}, 
                        headers=headers)
    if response.status_code != 200:
        return []
    
    return response.json()["items"]

# Exemple de boucle de surveillance
def monitor_responses(duration_minutes=60, check_interval_seconds=60):
    end_time = time.time() + (duration_minutes * 60)
    while time.time() < end_time:
        unread_emails = check_for_responses()
        
        for email in unread_emails:
            if email["ue_type"] == 2:  # Email reçu
                # Traiter la réponse (IA peut analyser le contenu et décider de la réponse)
                process_response(email)
        
        time.sleep(check_interval_seconds)

def process_response(email):
    # Analyser le contenu et générer une réponse appropriée
    reply_content = generate_ai_response(email["body"]["text"])
    
    # Envoyer la réponse
    reply_data = {
        "reply_to_uuid": email["id"],
        "eaccount": active_account["email"],
        "subject": f"Re: {email['subject']}",
        "body": {
            "html": f"<p>{reply_content}</p>",
            "text": reply_content
        }
    }
    
    requests.post(f"{base_url}/emails/reply", json=reply_data, headers=headers)
    
    # Marquer comme traité
    if email["thread_id"]:
        requests.post(f"{base_url}/emails/threads/{email['thread_id']}/mark-as-read", headers=headers)

def generate_ai_response(email_text):
    # Ici, l'IA analyse le texte et génère une réponse appropriée
    # Cette fonction serait implémentée selon les capacités de l'IA
    return "Merci pour votre réponse. Je vais analyser votre demande et revenir vers vous rapidement."

# Lancer la surveillance (par exemple pour 1 heure)
monitor_responses(60)
```

Cette documentation contient les éléments essentiels pour qu'un agent IA puisse interagir efficacement avec l'API Instantly tout en gérant les cas d'erreur et en implémentant les bonnes pratiques.
