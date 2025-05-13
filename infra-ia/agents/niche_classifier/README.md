# NicheClassifierAgent

## Description

Le **NicheClassifierAgent** est un agent spécialisé dans le système BerinIA qui analyse et classifie les niches commerciales dans des familles prédéfinies pour personnaliser les approches de prospection. Il combine:

1. **Classification intelligente des niches** en familles (santé, retail, immobilier, etc.)
2. **Analyse des données visuelles** issues du VisualAnalyzer
3. **Génération d'approches personnalisées** adaptées au secteur et à la maturité digitale

Cet agent permet d'optimiser les stratégies de prospection en proposant automatiquement les services IA les plus pertinents en fonction du secteur d'activité et de la qualité de la présence web.

## Fonctionnement

### Classification des niches

L'agent utilise plusieurs méthodes pour classifier une niche:

1. **Correspondance directe**: Vérifie si la niche est dans le dictionnaire prédéfini
2. **Classification par LLM**: Utilise GPT pour classifier les niches inconnues
3. **Méthode de secours**: En cas d'échec, trouve la famille la plus proche par similarité textuelle

### Intégration avec le VisualAnalyzer

Le NicheClassifierAgent utilise les données d'analyse visuelle pour:

- Déterminer la maturité digitale du site web
- Évaluer la présence ou absence de fonctionnalités clés
- Identifier des éléments spécifiques au secteur (ex: intégration Doctolib)
- Adapter les propositions en fonction de l'état du site

### Génération d'approches personnalisées

En combinant la famille de niche et l'analyse visuelle, l'agent propose:

- Les **besoins IA spécifiques** au secteur
- Une **approche contextuelle** adaptée à la situation
- Des **recommandations de services** personnalisés

## Structure des données

### Hiérarchie des niches

La hiérarchie est définie dans `infra-ia/data/niche_families.json` et comprend:

- **Familles**: Regroupements logiques de secteurs d'activité
- **Niches**: Métiers spécifiques dans chaque famille
- **Besoins**: Services IA recommandés pour chaque famille
- **Logique**: Règles d'approche selon le contexte

## Intégration dans le système

### Avec l'OverseerAgent

```python
# L'OverseerAgent peut appeler le NicheClassifierAgent
niche_classifier_result = niche_classifier_agent.run({
    "action": "classify",
    "niche": "Dentiste"
})

# Obtenir une approche personnalisée avec analyse visuelle
approach = niche_classifier_agent.run({
    "action": "generate_approach",
    "niche": "Dentiste",
    "visual_analysis": visual_analyzer_result
})
```

### Avec le MessagingAgent

Le MessagingAgent peut utiliser les données de classification pour personnaliser les messages:

```python
personalized_approach = niche_classifier_agent.run({
    "action": "generate_approach",
    "niche": lead.niche,
    "visual_analysis": lead.visual_analysis_data
})

# Utilisation dans le template de message
message_context = {
    "lead": lead,
    "approach": personalized_approach,
    "needs": personalized_approach["recommended_needs"]
}
```

## Exemples d'utilisation

### Classification d'une niche

```python
result = niche_classifier_agent.run({
    "action": "classify",
    "niche": "Ostéopathe"
})
```

Résultat:
```json
{
    "family_id": "health",
    "family_name": "Métiers de la santé",
    "match_type": "exact",
    "confidence": 1.0,
    "family_info": {...}
}
```

### Génération d'approche personnalisée

```python
approach = niche_classifier_agent.run({
    "action": "generate_approach",
    "niche": "Plombier",
    "visual_analysis": {
        "visual_score": 35,
        "visual_quality": 3,
        "has_popup": False,
        "screenshot_path": "/path/to/screenshot.png"
    }
})
```

Résultat:
```json
{
    "niche": "Plombier",
    "family": "Artisans & Construction",
    "family_id": "construction",
    "match_confidence": 1.0,
    "recommended_needs": ["ia_urgence", "accueil_telephonique"],
    "conditions_detected": ["no_site_or_gmb", "site_pauvre"],
    "proposal": "pack visibilité + IA",
    "visual_score": 35,
    "site_quality": 3,
    "website_maturity": "basic"
}
```

## Configuration

La configuration de l'agent est définie dans `config.json`:

```json
{
  "name": "NicheClassifierAgent",
  "llm_model": "gpt-4.1-mini",
  "confidence_threshold": 0.6,
  "use_visual_analysis": true,
  "enable_llm_fallback": true,
  "default_family": "b2b_services"
}
```

## Évolution future

- Intégration de sources de données supplémentaires (LinkedIn, GMB)
- Ajout de nouvelles familles et niches
- Raffinement des règles de classification
- Apprentissage continu à partir des résultats de prospection
