# NicheClassifierAgent - Classification et Personnalisation des Niches

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Fonctionnalités principales](#fonctionnalités-principales)
- [Hiérarchie des niches](#hiérarchie-des-niches)
- [Interaction avec le VisualAnalyzerAgent](#interaction-avec-le-visualanalyzeragent)
- [Workflows implémentés](#workflows-implémentés)
- [Utilisation](#utilisation)
- [Exemples](#exemples)

## Vue d'ensemble

Le NicheClassifierAgent est un agent spécialisé qui classifie les leads dans des familles de niches commerciales et génère des approches personnalisées basées sur le contexte de la niche et l'analyse visuelle du site web. En collaboration avec le VisualAnalyzerAgent, il fournit une compréhension approfondie du secteur d'activité du lead et des recommandations personnalisées pour une approche commerciale optimale.

## Fonctionnalités principales

1. **Classification contextuelle**
   - Classification automatique des niches en familles (santé, commerce, immobilier, etc.)
   - Détection des spécificités métier
   - Identification des besoins IA typiques par secteur

2. **Analyse combinée**
   - Intégration des données d'analyse visuelle du VisualAnalyzerAgent
   - Corrélation entre maturité digitale et besoins sectoriels
   - Détection des opportunités spécifiques au segment

3. **Personnalisation des messages**
   - Génération d'approches personnalisées par niche
   - Adaptation du ton et du vocabulaire au secteur
   - Recommandations de services IA adaptés au contexte

4. **Enrichissement des leads**
   - Ajout de métadonnées de classification
   - Suggestion de points d'accroche pertinents
   - Calcul de scores d'adéquation service/besoin

## Hiérarchie des niches

La hiérarchie des niches est définie dans le fichier `infra-ia/data/niche_families.json` et comprend cinq grandes familles :

### 1. Métiers de la santé
- Chiropracteurs
- Ostéopathes
- Podologues
- Dentistes
- Psychologues
- Naturopathes

### 2. Commerces physiques
- Coiffeurs
- Barbiers
- Instituts de beauté
- Restaurants
- Boutiques de mode
- Fleuristes

### 3. Immobilier & Habitat
- Agents immobiliers
- Diagnostiqueurs
- Architectes
- Décorateurs d'intérieur
- Courtiers immobiliers

### 4. B2B Services
- Experts-comptables
- Avocats
- Consultants
- Agences de communication
- Services informatiques

### 5. Artisans & Construction
- Plombiers
- Électriciens
- Serruriers
- Peintres
- Charpentiers

Chaque famille définit :
- Les niches spécifiques
- Les besoins IA typiques
- Les cibles de scraping
- La logique d'approche en fonction de l'analyse visuelle

## Interaction avec le VisualAnalyzerAgent

Le NicheClassifierAgent travaille en étroite collaboration avec le VisualAnalyzerAgent pour combiner l'analyse de niche avec l'analyse visuelle :

### Flux de données

1. Le VisualAnalyzerAgent analyse le site web et fournit :
   - Score de maturité digitale
   - Type de site (vitrine, e-commerce, etc.)
   - Forces et faiblesses de conception
   - Détails techniques (CTA, navigation, formulaires)

2. Le NicheClassifierAgent combine ces données avec :
   - Classification de la niche
   - Besoins typiques du secteur
   - Attentes digitales de la niche
   - Opportunités d'amélioration sectorielles

3. Le résultat est utilisé par le MessagingAgent pour :
   - Personnaliser le message initial
   - Créer des points d'accroche pertinents
   - Adapter le ton et le niveau technique du message

## Workflows implémentés

### 1. Analyse visuelle avec classification

```
VisualAnalyzerAgent → NicheClassifierAgent
```

Ce workflow permet d'analyser visuellement le site web d'un lead puis utiliser cette analyse pour générer une approche personnalisée basée sur la niche.

### 2. Enrichissement complet des leads

```
NicheClassifierAgent → VisualAnalyzerAgent → NicheClassifierAgent → MessagingAgent
```

Ce workflow plus complet :
1. Classifie d'abord la niche
2. Effectue une analyse visuelle
3. Génère une approche personnalisée
4. Produit un message parfaitement adapté

## Utilisation

### Via l'OverseerAgent

```python
# Classification simple d'une niche
result = overseer.execute_agent("NicheClassifierAgent", {
    "action": "classify",
    "niche": "Dentiste"
})

# Génération d'approche personnalisée
result = overseer.execute_agent("NicheClassifierAgent", {
    "action": "generate_approach",
    "niche": "Plombier",
    "visual_analysis": visual_analysis_data
})

# Exécution du workflow complet
result = overseer.orchestrate_workflow(
    "lead_enrichment_with_classification",
    {
        "niche": "Ostéopathe",
        "lead_id": 123
    }
)
```

### Via appel direct

```python
# Initialisation de l'agent
agent = NicheClassifierAgent()

# Classification simple
classification = agent.run({
    "action": "classify",
    "niche": "Consultant en cybersécurité"
})

# Génération d'approche personnalisée
approach = agent.run({
    "action": "generate_approach",
    "niche": "Photographe",
    "visual_analysis": visual_analysis_data,
    "lead_id": 123
})
```

## Exemples

### Format de résultat de classification

```json
{
  "niche": "Ostéopathe",
  "family": "Métiers de la santé",
  "confidence": 0.95,
  "typical_needs": [
    "Système de prise de rendez-vous en ligne",
    "Marketing digital ciblé pour patients",
    "Automatisation des rappels de rendez-vous",
    "Présence en ligne professionnelle"
  ],
  "digital_expectations": "medium-high",
  "typical_pain_points": [
    "Difficulté à se différencier de la concurrence",
    "Manque de visibilité en ligne",
    "Gestion manuelle des rendez-vous"
  ],
  "related_niches": [
    "Chiropracteur",
    "Kinésithérapeute",
    "Naturopathe"
  ]
}
```

### Format de résultat d'approche personnalisée

```json
{
  "niche": "Ostéopathe",
  "family": "Métiers de la santé",
  "approach": {
    "tone": "professionnel et rassurant",
    "focus_points": [
      "Amélioration de la visibilité en ligne",
      "Automatisation de la prise de rendez-vous",
      "Professionnalisation du site web"
    ],
    "pain_points_to_address": [
      "Difficulté de gestion des disponibilités",
      "Manque d'outils pour fidéliser les patients"
    ],
    "suggested_services": [
      "Refonte du site avec système de réservation intégré",
      "Automatisation des rappels par SMS",
      "Optimisation du référencement local"
    ],
    "hook_sentences": [
      "La plupart des ostéopathes que nous accompagnons constatent une augmentation de 30% des nouveaux patients après l'implémentation de notre système de réservation en ligne.",
      "Votre site actuel manque des éléments clés que les patients recherchent aujourd'hui chez un professionnel de santé."
    ]
  },
  "visual_context": {
    "website_maturity": "basic",
    "improvement_opportunities": [
      "Ajouter un système de prise de rendez-vous en ligne",
      "Améliorer la présentation des soins proposés",
      "Moderniser l'aspect visuel pour renforcer la confiance"
    ]
  }
}
```

---

[Retour à l'accueil](../index.md) | [Système de logs →](../technical/logging.md)
