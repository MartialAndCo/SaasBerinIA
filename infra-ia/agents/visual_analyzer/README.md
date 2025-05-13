# Visual Analyzer Agent

## Description

L'agent d'analyse visuelle est un composant avancé du système BerinIA qui utilise la vision par ordinateur et l'intelligence artificielle (GPT-4.1) pour:

1. Capturer des screenshots de sites web
2. Détecter et supprimer intelligemment les popups
3. Analyser visuellement la structure et le contenu des sites
4. Extraire des métriques et informations clés sur la qualité visuelle

## Fonctionnalités

- **Détection intelligente de popups**: Identifie les popups, bannières de cookies et autres éléments obstructifs
- **Gestion adaptative de consentement**: Ferme automatiquement les popups sans dépendre de sélecteurs spécifiques au site
- **Analyse HTML complète**: Utilise plusieurs stratégies complémentaires pour interagir avec les sites
- **Analyse visuelle du site**: Évalue la qualité du design, structure, et expérience utilisateur
- **Extraction de métadonnées**: Identifie type de site, forces, faiblesses, et niveau de professionnalisme

## Architecture

L'agent combine plusieurs approches:

1. **Vision par ordinateur** (GPT-4.1): Pour analyser visuellement les captures d'écran
2. **Analyse HTML**: Pour trouver et interagir avec les éléments de la page
3. **Stratégies multi-méthodes**: Pour maximiser les chances de succès
4. **Analyse comportementale**: Pour vérifier que les interactions ont réussi

## Intégration

L'agent s'intègre facilement au reste du système BerinIA:

```python
from agents.visual_analyzer import VisionPopupAnalyzer

# Créer une instance de l'analyseur
analyzer = VisionPopupAnalyzer()

# Analyser un site web
results = await analyzer.analyze_website("https://example.com")

# Accéder aux résultats
if results["has_popup"]:
    print(f"Popup détecté et {'supprimé' if results['popup_removed'] else 'non supprimé'}")

site_info = results["site_content"]
print(f"Type de site: {site_info['site_type']}")
print(f"Qualité visuelle: {site_info['visual_quality']}/10")
```

## Dépendances

- Python 3.9+
- OpenAI API (GPT-4.1)
- Playwright
- Pillow
- Colorama

## Fichiers de test

Les tests pour cet agent se trouvent dans `infra-ia/tests/vision_tests/`
