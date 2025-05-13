# VisualAnalyzerAgent - Analyse Visuelle des Sites Web

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Fonctionnalités principales](#fonctionnalités-principales)
- [Architecture technique](#architecture-technique)
- [Flux de travail](#flux-de-travail)
- [Intégration avec la base de données](#intégration-avec-la-base-de-données)
- [Utilisation](#utilisation)
- [Exemples](#exemples)

## Vue d'ensemble

Le VisualAnalyzerAgent est un agent spécialisé qui analyse visuellement les sites web des leads pour évaluer leur maturité digitale, identifier leurs forces et faiblesses, et enrichir les données des leads avec des métriques visuelles. Ces informations sont ensuite utilisées par d'autres agents, notamment le NicheClassifierAgent, pour personnaliser les approches de prospection.

## Fonctionnalités principales

1. **Capture d'écran automatique**
   - Génération automatique de captures d'écran des sites web
   - Détection et contournement des obstacles (popups, cookies, etc.)
   - Création d'images haute résolution pour analyse

2. **Analyse de maturité digitale**
   - Évaluation de la qualité visuelle du site (score de 1 à 10)
   - Classification du niveau de maturité (basic, intermediate, advanced)
   - Identification du type de site (vitrine, e-commerce, blog, etc.)

3. **Analyse avancée des composants**
   - Détection des éléments UI/UX (navigation, CTA, formulaires)
   - Analyse de la cohérence visuelle
   - Évaluation de l'adaptation mobile

4. **Enrichissement des leads**
   - Ajout de métadonnées visuelles aux leads
   - Calcul d'un score global de qualité visuelle
   - Génération de recommandations basées sur l'analyse

## Architecture technique

### Composants principaux

Le VisualAnalyzerAgent utilise plusieurs technologies :

1. **Playwright** - Pour la navigation web headless et les captures d'écran
2. **OpenAI Vision API** - Pour l'analyse visuelle des captures d'écran
3. **Base de données PostgreSQL** - Pour stocker les résultats d'analyse

### Structure du code

```
agents/visual_analyzer/
├── visual_analyzer_agent.py    # Classe principale de l'agent
├── config.json                 # Configuration de l'agent
├── prompt.txt                  # Prompt pour la vision API
└── modules/
    ├── screenshot_generator.py # Génération de captures d'écran
    ├── popup_remover.py        # Détection et fermeture de popups
    └── image_analyzer.py       # Analyse des images
```

## Flux de travail

### 1. Génération de captures d'écran

```python
async def capture_screenshot(self, url: str) -> str:
    """
    Capture une capture d'écran d'un site web.
    
    Args:
        url: URL du site web à capturer
        
    Returns:
        Chemin vers la capture d'écran générée
    """
    # Configuration de Playwright
    browser = await playwright.chromium.launch()
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    
    # Navigation et capture
    await page.goto(url, wait_until="networkidle")
    screenshot_path = f"screenshots/{uuid.uuid4()}.png"
    await page.screenshot(path=screenshot_path)
    
    return screenshot_path
```

### 2. Détection et fermeture des popups

```python
async def remove_popups(self, page) -> bool:
    """
    Détecte et ferme les popups, bandeaux de cookies, etc.
    
    Args:
        page: Page Playwright
        
    Returns:
        True si des popups ont été détectés et fermés, False sinon
    """
    # Détection de popups communs
    selectors = [
        "button[aria-label='Close']",
        "button.cookie-consent__button",
        "div.popup button.close",
        "div.modal button.close",
        # etc.
    ]
    
    popups_removed = False
    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=1000)
            await page.click(selector)
            popups_removed = True
        except:
            pass
            
    return popups_removed
```

### 3. Analyse visuelle

```python
async def analyze_screenshot(self, screenshot_path: str) -> Dict:
    """
    Analyse une capture d'écran en utilisant Vision API.
    
    Args:
        screenshot_path: Chemin vers la capture d'écran
        
    Returns:
        Dictionnaire contenant les résultats de l'analyse
    """
    # Lecture du prompt template
    with open("prompt.txt", "r") as f:
        prompt_template = f.read()
    
    # Encodage de l'image en base64
    with open(screenshot_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Appel à l'API Vision
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": prompt_template
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyse this website screenshot:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=1000
    )
    
    # Extraction et parsing des résultats
    analysis_text = response.choices[0].message.content
    analysis_json = json.loads(self._extract_json(analysis_text))
    
    return analysis_json
```

## Intégration avec la base de données

Les champs suivants ont été ajoutés à la table `leads` pour stocker les données d'analyse visuelle :

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

## Utilisation

### Via l'OverseerAgent

```python
# Analyse d'un site web spécifique
result = overseer.execute_agent("VisualAnalyzerAgent", {
    "action": "analyze_website",
    "url": "https://example.com",
    "lead_id": 123
})

# Analyse d'un lot de leads
result = overseer.execute_agent("VisualAnalyzerAgent", {
    "action": "batch_analyze",
    "lead_ids": [123, 124, 125],
    "max_concurrent": 5  # Nombre d'analyses simultanées
})
```

### Via appel direct

```python
# Initialisation de l'agent
agent = VisualAnalyzerAgent()

# Analyse simple
analysis = await agent.run({
    "action": "analyze_website",
    "url": "https://example.com"
})

# Analyse avec identifiant de lead pour stockage en base
analysis_with_storage = await agent.run({
    "action": "analyze_website",
    "url": "https://example.com",
    "lead_id": 123,
    "store_results": True
})
```

## Exemples

### Format de résultat d'analyse

```json
{
  "visual_score": 7.5,
  "site_type": "e-commerce",
  "website_maturity": "intermediate",
  "visual_quality": 8,
  "has_popup": true,
  "popup_removed": true,
  "design_strengths": [
    "Bonne cohérence des couleurs",
    "Navigation claire",
    "Images de produits de haute qualité"
  ],
  "design_weaknesses": [
    "Texte parfois peu lisible sur mobile",
    "Trop d'éléments sur la page d'accueil"
  ],
  "ui_components": {
    "navigation": {
      "type": "horizontal menu",
      "quality": "good",
      "mobile_friendly": true
    },
    "cta": {
      "presence": true,
      "visibility": "high",
      "effectiveness": "medium"
    },
    "forms": {
      "presence": true,
      "usability": "medium"
    }
  },
  "recommendations": [
    "Améliorer la lisibilité du texte sur mobile",
    "Simplifier la page d'accueil",
    "Ajouter des témoignages clients plus visibles"
  ]
}
```

### Intégration avec le NicheClassifierAgent

Le VisualAnalyzerAgent est souvent utilisé en tandem avec le NicheClassifierAgent pour personnaliser les approches :

```python
# Workflow complet
analysis = await visual_analyzer.run({
    "action": "analyze_website",
    "url": lead.website,
    "lead_id": lead.id
})

approach = await niche_classifier.run({
    "action": "generate_approach",
    "niche": lead.niche,
    "visual_analysis": analysis
})

message = await messaging_agent.run({
    "action": "generate_message",
    "lead_id": lead.id,
    "approach": approach
})
```

---

[Retour à l'accueil](../index.md) | [NicheClassifierAgent →](niche-classifier.md)
