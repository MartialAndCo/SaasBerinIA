# Chargement Automatique des Agents dans BerinIA

Ce document explique l'architecture de chargement automatique des agents dans le système BerinIA, en particulier pour le webhook WhatsApp.

## Problématique Résolue

Auparavant, nous devions explicitement lister les agents requis dans la liste `WEBHOOK_REQUIRED_AGENTS` du fichier `utils/agent_definitions.py`. Cela posait plusieurs problèmes :

1. À chaque ajout d'un nouvel agent, il fallait mettre à jour manuellement cette liste
2. Si on oubliait d'ajouter un agent dans cette liste, il n'était pas chargé par le webhook
3. Certaines fonctionnalités pouvaient être indisponibles car les agents nécessaires n'étaient pas chargés

## Nouvelle Solution

Nous avons mis en place un système de chargement automatique de tous les agents disponibles :

1. Une fonction `get_all_agent_names()` dans `utils/agent_definitions.py` retourne la liste complète des agents définis
2. La fonction `get_webhook_agents()` dans `webhook/webhook_config.py` charge automatiquement tous ces agents

Cela garantit que :
- Tous les agents sont disponibles pour répondre à n'importe quelle question
- Les nouveaux agents sont automatiquement détectés et chargés
- Aucune mise à jour manuelle n'est nécessaire lors de l'ajout de nouveaux agents

## Comment Ajouter un Nouvel Agent

Pour ajouter un nouvel agent au système, il suffit de :

1. Ajouter sa définition dans la liste `AGENT_DEFINITIONS` dans `utils/agent_definitions.py`
2. Implémenter l'agent dans le dossier approprié

Le webhook chargera automatiquement cet agent sans aucune autre modification nécessaire.

## Agents Principaux

Bien que tous les agents soient chargés, nous vérifions encore la présence de certains agents principaux qui sont absolument nécessaires au fonctionnement du webhook :

```python
core_agents = ["LoggerAgent", "OverseerAgent", "MessagingAgent"]
```

Si ces agents sont absents, un message d'erreur est affiché, mais le webhook continue de fonctionner si possible.

## Performances

Cette approche a été validée sur un serveur avec 8 Go de RAM, où le chargement complet de tous les agents (24 actuellement) a un impact négligeable sur les performances. 

Le webhook démarre en quelques secondes et répond rapidement aux requêtes, même avec tous les agents chargés.

## Logs

Le système produit des logs détaillés du chargement des agents, ce qui permet de diagnostiquer facilement les problèmes :

```
11:39:52 | INFO     | Registre d'agents initialisé avec 24 agents
11:39:52 | INFO     | Tous les agents principaux pour le webhook sont disponibles
11:39:52 | INFO     | Total des agents chargés: 24
```

Ces logs indiquent combien d'agents ont été chargés avec succès.
