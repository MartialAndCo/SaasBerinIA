# Intégration du NicheClassifierAgent dans l'architecture BerinIA

## Vue d'ensemble

Le `NicheClassifierAgent` est un agent spécialisé qui s'intègre dans l'architecture BerinIA pour fournir une classification intelligente des niches commerciales et une personnalisation des approches de prospection basée sur l'analyse visuelle des sites web.

## Architecture d'intégration

```
┌───────────────────────┐
│    OverseerAgent      │
└───────────┬───────────┘
            │
            │ Orchestration
            ▼
┌───────────────────────┐     ┌───────────────────────┐
│  NicheClassifierAgent │◄────┤   VisualAnalyzerAgent │
└───────────┬───────────┘     └───────────────────────┘
            │
            │ Approche personnalisée
            ▼
┌───────────────────────┐
│    MessagingAgent     │
└───────────────────────┘
```

## Rôle dans le système

1. **Classification contextuelle**: Le `NicheClassifierAgent` classifie chaque lead dans une famille de niches (santé, commerce, immobilier, etc.) afin d'adapter l'approche commerciale.

2. **Analyse combinée**: En collaboration avec le `VisualAnalyzerAgent`, il utilise les données d'analyse visuelle pour générer des recommandations plus précises.

3. **Personnalisation des messages**: Fournit au `MessagingAgent` des informations contextuelles pour personnaliser les messages de prospection.

## Workflows implémentés

### 1. Analyse visuelle avec classification

```
VisualAnalyzerAgent → NicheClassifierAgent
```

Ce workflow analyse visuellement le site web d'un lead puis utilise cette analyse pour générer une approche personnalisée basée sur la niche.

### 2. Enrichissement complet des leads

```
NicheClassifierAgent → VisualAnalyzerAgent → NicheClassifierAgent → MessagingAgent
```

Ce workflow:
1. Classifie d'abord la niche
2. Effectue une analyse visuelle
3. Génère une approche personnalisée
4. Produit un message adapté

## Intégration avec la base de données

Les champs suivants ont été ajoutés à la table `leads` pour stocker les données d'analyse visuelle:

- `visual_score`: Score global d'analyse visuelle
- `visual_analysis_data`: Données complètes de l'analyse (JSONB)
- `has_popup`: Présence de popups sur le site
- `popup_removed`: Statut de suppression des popups
- `screenshot_path`: Chemin vers la capture d'écran
- `enhanced_screenshot_path`: Chemin vers la capture d'écran améliorée
- `visual_analysis_date`: Date de l'analyse
- `site_type`: Type de site (vitrine, e-commerce, etc.)
- `visual_quality`: Qualité visuelle du site (1-10)
- `website_maturity`: Maturité du site (basic, intermediate, advanced)
- `design_strengths`: Forces de conception
- `design_weaknesses`: Faiblesses de conception

## Appels API et endpoints

De nouveaux endpoints ont été ajoutés à l'API leads:

- `POST /leads/{lead_id}/visual-analysis`: Ajoute une analyse visuelle
- `PUT /leads/{lead_id}/visual-analysis`: Met à jour une analyse existante
- `POST /leads/{lead_id}/upload-screenshot`: Télécharge une capture d'écran
- `GET /leads/visual-analysis`: Récupère les leads avec filtrage sur l'analyse visuelle

## Hiérarchie des niches

La hiérarchie des niches est définie dans le fichier `infra-ia/data/niche_families.json` et comprend:

- **Métiers de la santé**: Chiropracteurs, Ostéopathes, Podologues, etc.
- **Commerces physiques**: Coiffeurs, Barbiers, Instituts de beauté, etc.
- **Immobilier & Habitat**: Agents immobiliers, Diagnostiqueurs, etc.
- **B2B Services**: Experts-comptables, Avocats, Consultants, etc.
- **Artisans & Construction**: Plombiers, Électriciens, Serruriers, etc.

Chaque famille définit:
- Les niches spécifiques
- Les besoins IA typiques
- Les cibles de scraping
- La logique d'approche en fonction de l'analyse visuelle

## Exemple d'utilisation

### Via l'OverseerAgent:

```python
# Appel direct de l'agent
result = overseer.execute_agent("NicheClassifierAgent", {
    "action": "classify",
    "niche": "Dentiste"
})

# Exécution du workflow complet
result = overseer.orchestrate_workflow(
    "lead_enrichment_with_classification",
    {
        "niche": "Plombier",
        "lead_id": 123
    }
)
```

### Via un appel direct:

```python
agent = NicheClassifierAgent()

# Classification simple
classification = agent.run({
    "action": "classify",
    "niche": "Ostéopathe"
})

# Génération d'approche personnalisée
approach = agent.run({
    "action": "generate_approach",
    "niche": "Plombier",
    "visual_analysis": visual_analysis_data
})
```

## Tests et validation

Un script de test d'intégration est disponible: `/root/berinia/infra-ia/tests/test_niche_classifier_integration.py`

Il teste:
- La classification directe des niches
- La génération d'approches personnalisées
- L'intégration avec l'OverseerAgent

Pour l'exécuter:
```bash
cd /root/berinia/infra-ia
python tests/test_niche_classifier_integration.py
