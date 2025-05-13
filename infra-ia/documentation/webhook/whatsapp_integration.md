# Intégration WhatsApp avec le système BerinIA

## Présentation

Ce document explique le fonctionnement de l'intégration du système BerinIA avec WhatsApp, ainsi que les modifications récentes apportées pour améliorer le traitement intelligent des messages.

## Problème initial

Auparavant, lorsqu'un utilisateur envoyait un message via WhatsApp au système, il recevait systématiquement une réponse générique : "Message reçu et enregistré. Un agent vous répondra prochainement." Cela se produisait parce que le webhook ne faisait pas appel à l'intelligence du système (MetaAgent) mais traitait directement les messages avec le MessagingAgent, qui n'était pas configuré pour produire des réponses intelligentes en temps réel.

En cas d'erreur, le système masquait les détails techniques et renvoyait un message générique, ce qui rendait le débogage difficile pour les administrateurs.

## Architecture du système

### Flux des messages WhatsApp

1. **Client WhatsApp** - L'utilisateur envoie un message depuis son application WhatsApp.
2. **WhatsApp Bot** - Le service `berinia-whatsapp` (basé sur whatsapp-web.js) reçoit le message et le transmet au webhook.
3. **Webhook FastAPI** - Le serveur webhook (`run_webhook.py`) reçoit le message via l'endpoint `/webhook/whatsapp`.
4. **WhatsApp Webhook Handler** - Le module `whatsapp_webhook.py` traite la requête.
5. **Agents BerinIA** - Le métaagent (`MetaAgent`) analyse le message et l'envoie aux agents appropriés.
6. **Réponse** - La réponse est générée et renvoyée au webhook, qui la transmet au bot WhatsApp.
7. **Client WhatsApp** - L'utilisateur reçoit la réponse.

### Composants clés

- **whatsapp-bot/src/services/whatsapp-client.js** : Client WhatsApp qui gère la connexion avec l'API WhatsApp Web et l'envoi/réception des messages.
- **infra-ia/webhook/run_webhook.py** : Point d'entrée du serveur webhook FastAPI.
- **infra-ia/webhook/whatsapp_webhook.py** : Gestionnaire spécifique pour les messages WhatsApp.
- **infra-ia/agents/meta/meta_agent.py** : Agent central d'intelligence conversationnelle.

## Modifications apportées

### 1. Utilisation du MetaAgent comme point d'entrée principal

Nous avons modifié le fichier `whatsapp_webhook.py` pour qu'il utilise le MetaAgent comme point d'entrée principal pour tous les messages, au lieu de les transmettre directement au MessagingAgent. Cette modification permet au système d'analyser intelligemment les demandes et d'y répondre de manière contextualisée.

```python
# Avant - Utilisation directe du MessagingAgent
messaging_agent = self.agents["MessagingAgent"]
# ...
result = messaging_agent.process_incoming(message_content, context)

# Après - Utilisation du MetaAgent comme point d'entrée principal
if "MetaAgent" not in self.agents:
    # Fallback vers MessagingAgent si nécessaire
    agent_key = "MessagingAgent"
else:
    agent_key = "MetaAgent"

agent = self.agents[agent_key]
# ...
result = agent.run(context)
```

### 2. Amélioration de la gestion des erreurs

Nous avons modifié le système pour qu'il remonte les erreurs réelles plutôt que de les masquer derrière un message générique. Cela facilite le débogage pour les administrateurs du système.

```python
# Avant - Message d'erreur générique
except Exception as e:
    logger.error(f"Erreur lors du traitement par l'agent: {str(e)}")
    response = "Message reçu, mais une erreur est survenue lors du traitement."

# Après - Affichage de l'erreur réelle
except Exception as e:
    logger.error(f"Erreur lors du traitement par l'agent {agent_key}: {str(e)}")
    import traceback
    stack_trace = traceback.format_exc()
    logger.error(f"Stack trace: {stack_trace}")
    
    # On renvoie l'erreur réelle en mode debug
    return {
        "error": f"Erreur de traitement: {str(e)}",
        "debug": stack_trace,
        "response": f"Erreur lors du traitement: {str(e)}"
    }
```

### 3. Harmonisation du format des contextes

Nous avons harmonisé le format du contexte envoyé aux agents pour s'assurer que tous les champs nécessaires sont présents, qu'ils utilisent des noms cohérents, et que tous les agents peuvent les traiter correctement.

```python
context = {
    "sender": sender,
    "recipient": "BerinIA",
    "message": message_content,
    "content": message_content,  # Pour compatibilité avec tous les agents
    "profile_name": profile_name,
    "message_type": "whatsapp",
    "source": "whatsapp",
    "group": data.get("group", "Direct Message"),
    "author": sender
}
```

## Comment tester l'intégration

### 1. Vérifier que le webhook est en cours d'exécution

```bash
ps aux | grep run_webhook.py
```

Si ce n'est pas le cas, démarrez-le :

```bash
cd /root/berinia/infra-ia
source .venv/bin/activate
python webhook/run_webhook.py
```

### 2. Vérifier que le service WhatsApp est en cours d'exécution

```bash
systemctl status berinia-whatsapp
```

Si ce n'est pas le cas, démarrez-le :

```bash
systemctl start berinia-whatsapp
```

### 3. Tester l'envoi d'un message

Vous pouvez utiliser l'outil de test intégré :

```bash
cd /root/berinia/infra-ia
source .venv/bin/activate
python test_webhook_whatsapp.py
```

Ou envoyer une requête directement :

```bash
curl -X POST http://localhost:8888/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "+33612345678",
    "profile_name": "Test User",
    "timestamp": "2025-05-08T12:00:00.000000",
    "message": {
      "text": "Quelle est la fonction du MetaAgent dans le système?",
      "type": "text"
    }
  }'
```

## Dépannage

### Le webhook ne répond pas

1. Vérifiez que le serveur webhook est en cours d'exécution :
   ```bash
   ps aux | grep run_webhook.py
   ```

2. Consultez les logs du webhook :
   ```bash
   cat /root/berinia/infra-ia/logs/webhook.log
   ```

### Le bot WhatsApp ne répond pas

1. Vérifiez que le service WhatsApp est en cours d'exécution :
   ```bash
   systemctl status berinia-whatsapp
   ```

2. Consultez les logs du service WhatsApp :
   ```bash
   journalctl -u berinia-whatsapp
   ```

### Les réponses ne sont pas intelligentes

1. Vérifiez que le MetaAgent est correctement initialisé dans le webhook :
   ```bash
   grep -i "MetaAgent" /root/berinia/infra-ia/logs/webhook.log
   ```

2. Vérifiez que le MetaAgent peut accéder au modèle de langage :
   ```bash
   cd /root/berinia/infra-ia
   source .venv/bin/activate
   python -c "from utils.llm import LLMService; print(LLMService.call_llm('Test'))"
   ```

## Améliorations futures possibles

1. **Ajout de threads de conversation** - Conserver l'historique des conversations pour chaque utilisateur afin d'améliorer le contexte et la cohérence des réponses.

2. **Support multilingue** - Ajouter la détection automatique de la langue et la génération de réponses dans la même langue.

3. **Reconnaissance d'images** - Ajouter le support pour analyser les images envoyées via WhatsApp.

4. **Monitoring avancé** - Mettre en place un système de monitoring pour suivre les performances du webhook et la qualité des réponses.

5. **Cache des réponses fréquentes** - Mettre en cache les réponses aux questions fréquentes pour réduire la latence et la consommation de ressources.
