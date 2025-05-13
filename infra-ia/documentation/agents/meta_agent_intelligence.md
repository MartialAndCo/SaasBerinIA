# MetaAgent: Système d'Intelligence Conversationnelle

## Introduction

Le MetaAgent est un agent central d'intelligence conversationnelle conçu pour analyser les demandes en langage naturel des utilisateurs et les transformer en actions concrètes, en identifiant dynamiquement les agents les plus appropriés pour répondre à ces demandes. Contrairement au système précédent qui nécessitait des mappings explicites pour chaque type de requête, le MetaAgent comprend l'intention sous-jacente et peut router intelligemment les demandes sans configuration préalable.

## Fonctionnalités principales

1. **Analyse sémantique des demandes utilisateur**
   - Compréhension du langage naturel et extraction des intentions
   - Identification des paramètres implicites et explicites
   - Évaluation de la confiance dans l'interprétation

2. **Découverte automatique des capacités du système**
   - Indexation dynamique des agents disponibles
   - Extraction des méthodes, descriptions et mots-clés
   - Classification des agents par domaine fonctionnel

3. **Routage intelligent des demandes**
   - Sélection de l'agent le plus approprié pour chaque demande
   - Exécution séquentielle d'actions complexes impliquant plusieurs agents
   - Gestion des erreurs et des cas de confiance faible

4. **Mémoire conversationnelle**
   - Maintien du contexte des conversations
   - Résolution des références implicites
   - Amélioration de la cohérence des réponses

## Architecture technique

Le MetaAgent repose sur plusieurs composants clés :

1. **Système d'indexation des capacités**
   - Au démarrage, le MetaAgent scanne tous les dossiers d'agents
   - Il analyse les fichiers source pour extraire les informations pertinentes
   - Il construit une représentation structurée des capacités du système

2. **Moteur d'analyse des demandes**
   - Un prompt sophistiqué envoyé au LLM pour analyser les demandes
   - Extraction des intentions, actions et paramètres
   - Structuration de l'analyse au format JSON pour traitement ultérieur

3. **Orchestrateur d'actions**
   - Exécution séquentielle des actions identifiées
   - Gestion des résultats intermédiaires
   - Génération d'une réponse cohérente basée sur tous les résultats

4. **Gestionnaire de contexte conversationnel**
   - Enregistrement de l'historique des conversations
   - Fourniture du contexte pour les analyses futures
   - Limitation de l'historique pour des performances optimales

## Intégration avec le système existant

Le MetaAgent s'intègre de manière transparente avec le système BerinIA existant :

1. **Modification du webhook WhatsApp**
   - Remplacement des mappings rigides groupe-agent par le MetaAgent
   - Simplification du traitement des messages
   - Amélioration de la gestion des erreurs

2. **Enregistrement dans le registre des agents**
   - Ajout du MetaAgent à webhook_config.py
   - Initialisation automatique au démarrage du webhook
   - Intégration avec les agents existants

## Comment utiliser le MetaAgent

Le MetaAgent est conçu pour être utilisé comme point d'entrée principal pour les interactions avec le système. Les demandes peuvent être formulées en langage naturel sans se soucier de la syntaxe ou des commandes spécifiques.

### Exemples de demandes prises en charge

- **Compter des entités**: "Combien de leads avons-nous dans la niche immobilier?"
- **Obtenir des statistiques**: "Montre-moi les performances de la campagne marketing"
- **Envoyer des messages**: "Envoie un SMS à tous les prospects du secteur restauration"
- **Statut du système**: "Quel est l'état actuel du système?"
- **Questions complexes**: "Quels sont les leads qui ont répondu positivement à notre dernier email?"

### Fonctionnement interne

Quand une demande est reçue, le MetaAgent:

1. Analyse la demande pour comprendre l'intention
2. Identifie les agents pertinents basés sur ses connaissances indexées
3. Formule une ou plusieurs actions à exécuter
4. Exécute ces actions séquentiellement
5. Synthétise les résultats en une réponse cohérente
6. Renvoie cette réponse à l'utilisateur

## Maintenance et évolution

Le MetaAgent est conçu pour s'adapter automatiquement aux changements du système:

1. **Ajout de nouveaux agents**
   - Les nouveaux agents sont automatiquement découverts et indexés
   - Aucune modification du MetaAgent n'est nécessaire

2. **Modification des capacités**
   - À chaque démarrage, le système réindexe les capacités
   - Les changements dans les agents sont automatiquement pris en compte

3. **Amélioration des prompts**
   - Le fichier prompt.txt peut être mis à jour pour améliorer l'analyse
   - La configuration dans config.json permet d'ajuster les paramètres

## Limitations actuelles et améliorations futures

1. **Analyse sémantique simplifiée**
   - L'analyse actuelle repose uniquement sur le LLM sans embeddings vectoriels
   - Une future version pourrait intégrer des embeddings pour une meilleure correspondance

2. **Absence d'apprentissage continu**
   - Le système ne s'améliore pas automatiquement basé sur les interactions passées
   - Un système de feedback pourrait être implémenté

3. **Gestion basique du contexte**
   - Le stockage de l'historique est simple et limité
   - Une gestion plus sophistiquée du contexte pourrait être implémentée
