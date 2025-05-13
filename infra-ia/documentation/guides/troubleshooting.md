# Guide de Résolution des Problèmes

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Problèmes d'installation](#problèmes-dinstallation)
- [Problèmes de connexion aux services](#problèmes-de-connexion-aux-services)
- [Problèmes avec les agents](#problèmes-avec-les-agents)
- [Problèmes de webhook](#problèmes-de-webhook)
- [Problèmes d'intégration WhatsApp](#problèmes-dintégration-whatsapp)
- [Problèmes de base de données](#problèmes-de-base-de-données)
- [Erreurs communes des LLM](#erreurs-communes-des-llm)
- [Outils de diagnostic](#outils-de-diagnostic)

## Problèmes d'installation

### Erreurs lors de l'installation des dépendances Python

#### Symptôme
```
ERROR: Could not build wheels for [package] which use PEP 517
```

#### Solution
Mettez à jour pip et setuptools:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Erreur "Command 'python' not found"

#### Symptôme
```
Command 'python' not found
```

#### Solution
Utilisez `python3` à la place de `python`, ou créez un alias:
```bash
alias python=python3
```

### Problèmes avec l'environnement virtuel

#### Symptôme
L'activation de l'environnement virtuel ne fonctionne pas ou les packages installés ne sont pas disponibles.

#### Solution
Recréez l'environnement virtuel:
```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Problèmes de connexion aux services

### Erreur d'API OpenAI

#### Symptôme
```
openai.error.AuthenticationError: Incorrect API key provided
```

#### Solution
1. Vérifiez que la clé API est correcte dans le fichier `.env`
2. Assurez-vous que la clé n'a pas expiré sur le portail OpenAI
3. Vérifiez que vous avez suffisamment de crédits sur votre compte

### Erreur de connexion à Qdrant

#### Symptôme
```
ConnectionRefusedError: [Errno 111] Connection refused
```

#### Solution
1. Vérifiez que Qdrant est en cours d'exécution:
   ```bash
   docker ps | grep qdrant
   ```
2. Redémarrez le conteneur si nécessaire:
   ```bash
   docker restart <container_id>
   ```
3. Vérifiez l'URL dans le fichier `.env` (par défaut `http://localhost:6333`)

### Problèmes d'authentification Twilio/Mailgun

#### Symptôme
Des erreurs lors de l'envoi de SMS ou d'emails, ou des erreurs d'authentification pour les webhooks.

#### Solution
1. Vérifiez que les identifiants dans `.env` sont corrects
2. Pour Twilio:
   ```bash
   twilio login # Si l'outil CLI est installé
   ```
3. Pour Mailgun, utilisez l'outil de test sur leur site web
4. Vérifiez que les services sont actifs et que votre compte n'est pas suspendu

## Problèmes avec les agents

### Agent non trouvé dans le registre

#### Symptôme
```
ERROR: Agent 'AgentName' not found in registry
```

#### Solution
1. Vérifiez que l'agent existe dans `infra-ia/agents/`
2. Vérifiez que le nom de l'agent est correctement orthographié
3. Assurez-vous que l'agent est déclaré dans `utils/agent_definitions.py`
4. Exécutez le script de test:
   ```bash
   python test_agent_loading.py
   ```

### Hallucinations LLM sur les noms d'agents

#### Symptôme
L'AdminInterpreterAgent tente d'appeler un agent qui n'existe pas (par exemple "LeadsAgent").

#### Solution
Le système de validation des agents doit corriger ce problème automatiquement. Si ce n'est pas le cas:
1. Vérifiez que le système de validation est actif dans `admin_interpreter_agent.py`
2. Mettez à jour le fichier `VALID_AGENTS` dans `admin_interpreter_agent.py` pour inclure tous les agents disponibles
3. Reformulez votre requête pour utiliser le nom d'agent correct

### Agent bloqué ou qui ne répond pas

#### Symptôme
Un agent semble bloqué et ne répond pas après un certain temps.

#### Solution
1. Vérifiez les logs pour identifier d'éventuelles erreurs:
   ```bash
   tail -n 100 /root/berinia/unified_logs/agents.log
   ```
2. Redémarrez le service webhook si nécessaire:
   ```bash
   sudo systemctl restart berinia-webhook.service
   ```
3. Vérifiez la consommation de mémoire et CPU:
   ```bash
   ps aux | grep python
   ```

## Problèmes de webhook

### Webhook inaccessible

#### Symptôme
Les services externes (Twilio, Mailgun) ne peuvent pas accéder au webhook.

#### Solution
1. Vérifiez que le service webhook est en cours d'exécution:
   ```bash
   sudo systemctl status berinia-webhook.service
   ```
2. Vérifiez que Nginx est correctement configuré:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```
3. Vérifiez les règles de pare-feu:
   ```bash
   sudo ufw status
   ```
4. Assurez-vous que les ports 80 et 443 sont ouverts

### Erreurs de signature Twilio

#### Symptôme
```
WARNING: ALERTE: Signature Twilio invalide pour https://votre-domaine.com/webhook/sms-response
```

#### Solution
1. Vérifiez que `TWILIO_TOKEN` est correctement défini dans `.env`
2. Assurez-vous que l'URL du webhook dans la console Twilio correspond exactement à celle de votre serveur
3. Vérifiez que la requête n'est pas altérée par un proxy intermédiaire
4. En développement, vous pouvez désactiver temporairement la vérification (non recommandé en production)

### Timeout des requêtes webhook

#### Symptôme
Les requêtes webhook prennent trop de temps et expirent.

#### Solution
1. Augmentez les timeouts dans la configuration Nginx:
   ```nginx
   proxy_connect_timeout 600;
   proxy_send_timeout 600;
   proxy_read_timeout 600;
   send_timeout 600;
   ```
2. Optimisez le traitement des webhooks pour qu'il soit plus rapide
3. Utilisez un système de file d'attente pour traiter les requêtes de manière asynchrone

## Problèmes d'intégration WhatsApp

### Erreur de connexion WhatsApp

#### Symptôme
Le bot WhatsApp ne parvient pas à se connecter ou se déconnecte fréquemment.

#### Solution
1. Régénérez le QR code pour la connexion:
   ```bash
   sudo systemctl stop berinia-whatsapp.service
   cd /root/berinia/whatsapp-bot
   node capture-qr.js
   ```
2. Scannez le nouveau QR code depuis votre téléphone
3. Redémarrez le service:
   ```bash
   sudo systemctl start berinia-whatsapp.service
   ```

### "Group not found in BerinIA community"

#### Symptôme
```
Error: Group not found in BerinIA community
```

#### Solution
1. Vérifiez que la communauté WhatsApp est correctement nommée "BerinIA"
2. Vérifiez que les groupes existent avec les noms exacts configurés
3. Exécutez la commande de listing des groupes:
   ```bash
   cd /root/berinia/whatsapp-bot
   node manage-whatsapp.js list
   ```
4. Mettez à jour la configuration des groupes dans `src/config/groups.js` si nécessaire

### Messages non envoyés à WhatsApp

#### Symptôme
Les messages ne sont pas envoyés ou ne sont pas reçus par WhatsApp.

#### Solution
1. Vérifiez les logs WhatsApp:
   ```bash
   tail -f /root/berinia/whatsapp-bot/logs/whatsapp-bot.log
   ```
2. Vérifiez l'état du service:
   ```bash
   sudo systemctl status berinia-whatsapp.service
   ```
3. Testez l'API d'envoi directement:
   ```bash
   curl -X POST http://localhost:3030/send \
     -H "Content-Type: application/json" \
     -d '{"group": "Logs techniques", "message": "Test message"}'
   ```

## Problèmes de base de données

### Erreur de connexion à PostgreSQL

#### Symptôme
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

#### Solution
1. Vérifiez que PostgreSQL est en cours d'exécution:
   ```bash
   sudo systemctl status postgresql
   ```
2. Vérifiez les informations de connexion dans `.env`
3. Vérifiez que l'utilisateur a les bons droits:
   ```bash
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE berinia TO berinia_user;"
   ```

### Erreurs lors des migrations

#### Symptôme
Des erreurs lors de l'exécution des scripts de migration.

#### Solution
1. Vérifiez que tous les scripts de migration sont présents dans `backend/migrations/`
2. Exécutez les migrations manuellement une par une:
   ```bash
   cd /root/berinia/backend
   sudo -u postgres psql -d berinia -f migrations/create_berinia_db.sql
   sudo -u postgres psql -d berinia -f migrations/add_messages_table.sql
   # etc.
   ```
3. Vérifiez les erreurs spécifiques dans les logs PostgreSQL:
   ```bash
   sudo tail -n 100 /var/log/postgresql/postgresql-14-main.log
   ```

### Erreurs "relation does not exist"

#### Symptôme
```
ERROR: relation "table_name" does not exist
```

#### Solution
1. Vérifiez que la table existe réellement:
   ```bash
   sudo -u postgres psql -d berinia -c "\dt"
   ```
2. Recréez la table si nécessaire:
   ```bash
   sudo -u postgres psql -d berinia -f migrations/create_table_name.sql
   ```
3. Si le problème persiste, recréez toute la base de données:
   ```bash
   cd /root/berinia/backend
   ./recreate_database.sh
   ```

## Erreurs communes des LLM

### Token limit exceeded

#### Symptôme
```
openai.error.InvalidRequestError: This model's maximum context length is X tokens
```

#### Solution
1. Réduisez la taille des prompts
2. Utilisez une technique de résumé pour les contextes longs
3. Répartissez le traitement en plusieurs appels API

### API rate limit

#### Symptôme
```
openai.error.RateLimitError: Rate limit reached for [model]
```

#### Solution
1. Implémentez un système de backoff exponentiel
2. Réduisez la fréquence des appels API
3. Distribuez les appels sur plusieurs clés API

### Hallucinations incorrectes

#### Symptôme
Le LLM génère des informations incorrectes ou invente des détails.

#### Solution
1. Améliorez les prompts pour être plus spécifiques
2. Utilisez des techniques de "few-shot prompting"
3. Implémentez un système de validation des sorties

## Outils de diagnostic

### Script de vérification de l'installation

Ce script vérifie l'installation complète:
```bash
cd /root/berinia/infra-ia
python verify_installation.py --full
```

### Vérification des services

Vérifiez l'état de tous les services:
```bash
sudo systemctl status postgresql
sudo systemctl status berinia-webhook.service
sudo systemctl status berinia-whatsapp.service
```

### Scripts de diagnostic spécifiques

1. Test de connexion à la base de données:
   ```bash
   cd /root/berinia/backend
   python test_db_connection.py
   ```

2. Test de l'API OpenAI:
   ```bash
   cd /root/berinia/infra-ia
   python test_openai.py
   ```

3. Test du webhook SMS:
   ```bash
   python test_sms_webhook.py
   ```

4. Test de l'intégration WhatsApp:
   ```bash
   cd /root/berinia/whatsapp-bot
   node test-send.js "Logs techniques" "Test message"
   ```

5. Test de chargement des agents:
   ```bash
   cd /root/berinia/infra-ia
   python test_agent_loading.py
   ```

### Analyse des logs

Les logs sont centralisés dans `/root/berinia/unified_logs/`:

```bash
# Logs système généraux
tail -f /root/berinia/unified_logs/system.log

# Logs d'erreurs
tail -f /root/berinia/unified_logs/error.log

# Logs des agents
tail -f /root/berinia/unified_logs/agents.log

# Logs du webhook
tail -f /root/berinia/unified_logs/webhook.log

# Logs WhatsApp
tail -f /root/berinia/unified_logs/whatsapp.log
```

---

[Retour à l'accueil](../index.md)
