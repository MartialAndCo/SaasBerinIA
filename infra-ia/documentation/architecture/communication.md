# Communication Inter-Agents

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Mécanismes de communication](#mécanismes-de-communication)
- [Canal de discussion](#canal-de-discussion)
- [Délégation de tâches](#délégation-de-tâches)
- [Implémentation technique](#implémentation-technique)
- [Traçabilité et visualisation](#traçabilité-et-visualisation)

## Vue d'ensemble

La communication entre les agents est un aspect fondamental du système BerinIA. Elle permet une coordination efficace, une visibilité sur les processus en cours et une traçabilité complète des actions. Le système utilise plusieurs mécanismes complémentaires pour permettre aux agents d'échanger des informations et de coordonner leurs actions.

## Mécanismes de communication

Le système BerinIA utilise trois mécanismes de communication principaux :

### 1. Appels directs (synchrones)

```python
result = agent.run({"action": "specific_action", "parameters": {...}})
```

Utilisés pour :
- Interactions synchrones où un résultat immédiat est nécessaire
- Opérations critiques qui doivent être complétées avant de continuer
- Communication directe entre l'OverseerAgent et les agents opérationnels

### 2. Messages asynchrones (logs)

```python
agent.speak("Message important", target="OverseerAgent")
```

Utilisés pour :
- Notifications non-bloquantes
- Journalisation des décisions et actions
- Informations contextuelles sur l'état du système

### 3. Délégation structurée

```python
result = overseer.delegate_to_supervisor("QualificationSupervisor", {
    "action": "qualify_leads",
    "parameters": {
        "leads": [...],
        "min_score": 70
    }
})
```

Utilisée pour :
- Distribution hiérarchique des tâches
- Transmission de responsabilités à un superviseur
- Exécution de workflows complexes impliquant plusieurs agents

## Canal de discussion

Chaque agent possède une méthode `speak()` qui lui permet d'envoyer des messages vers un canal de log centralisé :

```python
def speak(self, message: str, target: str = None):
    """
    Envoie un message à un autre agent ou au log général.
    
    Args:
        message: Le message à envoyer
        target: L'agent destinataire (optionnel)
    """
    LoggerAgent.log_interaction(self.name, target, message)
```

### Format des messages

Les interactions entre agents sont enregistrées dans un format JSON structuré :

```json
{
  "timestamp": "2025-05-03T18:52:14",
  "from": "ScraperAgent",
  "to": "CleanerAgent",
  "message": "J'ai terminé le scraping sur la niche coaching. Voici 47 leads.",
  "context_id": "campaign_042"
}
```

### Règles de communication

1. **Pas de communication directe entre agents opérationnels**
   - Les agents ne doivent pas s'appeler entre eux directement
   - Toute communication passe par le niveau supérieur (OverseerAgent ou superviseurs)

2. **L'OverseerAgent est le seul à pouvoir initier des workflows**
   - Les agents opérationnels ne démarrent jamais d'actions par eux-mêmes
   - L'OverseerAgent décide quand et comment enchaîner les actions

3. **Tous les messages importants doivent être loggés**
   - Utiliser `speak()` pour toute information pertinente
   - Inclure le contexte (campaign_id, lead_id, etc.)

## Délégation de tâches

L'OverseerAgent utilise un mécanisme spécifique pour déléguer les tâches aux superviseurs :

```python
def delegate_to_supervisor(self, supervisor_name: str, task_data: dict) -> dict:
    """
    Délègue une tâche à un superviseur spécifique.
    
    Args:
        supervisor_name: Nom du superviseur (ScrapingSupervisor, etc.)
        task_data: Données de la tâche à déléguer
        
    Returns:
        Résultat de la tâche déléguée
    """
    supervisor = self.registry.get_or_create(supervisor_name)
    if not supervisor:
        return {"status": "error", "message": f"Superviseur {supervisor_name} non trouvé"}
    
    self.speak(f"Délégation de tâche à {supervisor_name}: {task_data.get('action')}", 
               target=supervisor_name)
    
    result = supervisor.run(task_data)
    
    return result
```

Les superviseurs peuvent ensuite déléguer à leur tour aux agents opérationnels :

```python
def handle_qualify_leads(self, task_data: dict) -> dict:
    """
    Gère la qualification de leads.
    
    Args:
        task_data: Données de la tâche
        
    Returns:
        Résultat de la qualification
    """
    leads = task_data.get("leads", [])
    min_score = task_data.get("min_score", 50)
    
    # Étape 1: Validation
    validator = self.registry.get_or_create("ValidatorAgent")
    valid_leads = validator.run({"action": "validate", "leads": leads})
    
    # Étape 2: Scoring
    scorer = self.registry.get_or_create("ScoringAgent")
    scored_leads = scorer.run({"action": "score", "leads": valid_leads["result"]})
    
    # Étape 3: Filtrage par score
    filtered_leads = [lead for lead in scored_leads["result"] if lead["score"] >= min_score]
    
    return {
        "status": "success",
        "result": filtered_leads,
        "metrics": {
            "total": len(leads),
            "valid": len(valid_leads["result"]),
            "qualified": len(filtered_leads)
        }
    }
```

## Implémentation technique

### Classe LoggerAgent

Le `LoggerAgent` est responsable de l'enregistrement de toutes les interactions :

```python
class LoggerAgent(AgentBase):
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.interaction_log_path = self.config.get("interaction_log_path", 
                                                   "logs/agent_interactions.jsonl")
    
    @classmethod
    def log_interaction(cls, from_agent: str, to_agent: str, message: str, 
                       context_id: str = None) -> None:
        """
        Enregistre une interaction entre agents.
        
        Args:
            from_agent: Agent source
            to_agent: Agent destination (optionnel)
            message: Contenu du message
            context_id: Identifiant de contexte (campagne, etc.)
        """
        instance = cls()
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "context_id": context_id
        }
        
        # Log dans le fichier JSONL
        with open(instance.interaction_log_path, "a") as f:
            f.write(json.dumps(interaction) + "\n")
        
        # Log également dans le fichier de log standard
        logger.info(f"{from_agent} → {to_agent or 'System'}: {message}")
```

### Communication par événements

Pour les événements asynchrones (comme les réponses aux messages), le système utilise un mécanisme d'événements :

```python
def handle_event(self, event_data: dict) -> dict:
    """
    Gère un événement système (réponse SMS, email, etc.)
    
    Args:
        event_data: Données de l'événement
        
    Returns:
        Résultat du traitement de l'événement
    """
    event_type = event_data.get("type")
    
    if event_type == "sms_response":
        return self.handle_sms_response(event_data)
    elif event_type == "email_response":
        return self.handle_email_response(event_data)
    elif event_type == "whatsapp_message":
        return self.handle_whatsapp_message(event_data)
    else:
        return {"status": "error", "message": f"Type d'événement inconnu: {event_type}"}
```

## Traçabilité et visualisation

### Format de visualisation

Dans l'interface sandbox (ou admin), les interactions entre agents sont visualisées comme un fil de discussion :

```
🧠 OverseerAgent → ScrapingSupervisor :
    Reprends le scraping sur la niche "menuisier" demain à 10h.

🔎 ScraperAgent → CleanerAgent :
    Voici 38 leads valides sur la niche immobilier B2C.

🧽 CleanerAgent → QualificationSupervisor :
    Tous les leads ont été nettoyés. 2 doublons supprimés.
```

### Filtrage des interactions

Les interactions peuvent être filtrées par :
- Agent source ou destination
- Campagne ou contexte
- Plage de dates
- Type de message ou contenu

### Analyse des workflows

La journalisation complète permet d'analyser les workflows et d'identifier les goulots d'étranglement :

```python
def analyze_workflow(workflow_id: str) -> dict:
    """
    Analyse un workflow complet à partir des logs d'interactions.
    
    Args:
        workflow_id: Identifiant du workflow à analyser
        
    Returns:
        Analyse du workflow (étapes, durées, résultats)
    """
    interactions = load_interactions_by_context(workflow_id)
    
    steps = []
    current_step = None
    
    for interaction in interactions:
        if interaction["from"] == "OverseerAgent":
            # Nouvelle étape initiée par l'OverseerAgent
            if current_step:
                steps.append(current_step)
            
            current_step = {
                "start_time": interaction["timestamp"],
                "agent": interaction["to"],
                "action": extract_action(interaction["message"]),
                "sub_interactions": []
            }
        elif current_step and (interaction["from"] == current_step["agent"] or 
                             interaction["to"] == current_step["agent"]):
            # Interaction liée à l'étape en cours
            current_step["sub_interactions"].append(interaction)
            
            if "completed" in interaction["message"].lower():
                current_step["end_time"] = interaction["timestamp"]
                
                # Calculer la durée
                start = datetime.fromisoformat(current_step["start_time"])
                end = datetime.fromisoformat(current_step["end_time"])
                current_step["duration_seconds"] = (end - start).total_seconds()
                
                steps.append(current_step)
                current_step = None
    
    return {
        "workflow_id": workflow_id,
        "steps": steps,
        "total_steps": len(steps),
        "total_duration": sum(step.get("duration_seconds", 0) for step in steps)
    }
```

---

[Retour à l'accueil](../index.md) | [Documentation des agents →](../agents/meta-agent.md)
