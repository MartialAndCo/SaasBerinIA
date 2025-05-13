# DatabaseQueryAgent

## Description
Le DatabaseQueryAgent est un agent spécialisé qui permet d'interroger la base de données en langage naturel. Il traduit les questions en requêtes SQL et renvoie les résultats formatés.

## Fonctionnalités principales
- Traduction automatique des questions en requêtes SQL
- Préchargement du schéma de la base de données pour des réponses plus rapides
- Gestion de requêtes prédéfinies pour les questions courantes
- Support de différents formats d'entrée pour plus de flexibilité

## Utilisation
### Format d'entrée standard
```json
{
  "message": "Combien de leads avons-nous dans la base de données?",
  "parameters": {}
}
```

### Format d'entrée avec action directe
```json
{
  "action": "count_leads",
  "parameters": {}
}
```

### Actions directes supportées
- `count_leads` : Compte le nombre total de leads dans la base de données
- `active_conversations` : Récupère les conversations actives des derniers jours
- `conversion_rate` : Calcule le taux de conversion pour les dernières campagnes

## Intégration avec les autres agents
### Appel depuis le MetaAgent
Lorsque le MetaAgent détecte une requête liée à la base de données, il doit inclure le message original ou préciser une action.

```json
{
  "target_agent": "DatabaseQueryAgent",
  "input_data": {
    "message": "Combien de leads avons-nous dans la base de données?",
    "parameters": {}
  }
}
```
OU
```json
{
  "target_agent": "DatabaseQueryAgent",
  "input_data": {
    "action": "count_leads",
    "parameters": {}
  }
}
```

### Appel depuis l'AdminInterpreterAgent
L'AdminInterpreterAgent doit transmettre le message ou l'action à l'OverseerAgent dans le format suivant :

```json
{
  "source": "AdminInterpreterAgent",
  "action": "execute_agent",
  "target_agent": "DatabaseQueryAgent",
  "input_data": {
    "message": "Combien de leads avons-nous dans la base de données?"
  }
}
```
OU
```json
{
  "source": "AdminInterpreterAgent",
  "action": "execute_agent",
  "target_agent": "DatabaseQueryAgent",
  "input_data": {
    "action": "count_leads"
  }
}
```

## Dépannage
Si vous recevez l'erreur "Aucune question ou requête fournie", vérifiez que :
1. Le message est bien inclus dans le champ "message" ou "question" de l'entrée
2. OU une action reconnue est fournie dans le champ "action"
3. Le format JSON est correct et complet
