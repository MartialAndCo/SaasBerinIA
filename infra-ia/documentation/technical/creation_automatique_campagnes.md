# Création Automatique de Campagnes - Documentation Technique

## 📋 Vue d'ensemble

Ce document décrit l'implémentation complète du système de création automatique de campagnes dans BerinIA, permettant de créer automatiquement des campagnes lors de la détection de nouvelles niches pendant le scraping de leads.

## 🎯 Problème Initial

### Erreurs Identifiées
1. **Erreur 500 API `/api/niches/`** : Incompatibilité entre schémas Pydantic et modèles DB
2. **Absence de campagnes** : Aucune campagne créée automatiquement lors du scraping
3. **Keywords mal formatés** : PostgreSQL attendait un array mais recevait du texte

## 🛠️ Solutions Implémentées

### 1. Correction API Niches

#### **Problème** : Format keywords incompatible
```python
# ❌ Avant : Format texte
keywords_text = f"{industry},{location}"

# ✅ Après : Format PostgreSQL array
keywords_text = f"{{{industry},{location}}}"
```

#### **Problème** : Schémas Pydantic incompatibles
```python
# ❌ Avant : Champs manquants
class NicheResponse(BaseModel):
    name: str  # DB retourne 'name' mais API attend 'nom'
    
# ✅ Après : Alias Pydantic
class NicheResponse(BaseModel):
    nom: str = Field(..., alias="name")  # Compatibilité DB ↔ API
    statut: str = Field(default="active", alias="status")
    keywords: Optional[Union[str, List[str]]] = None  # Support array ET string
```

### 2. Système de Création Automatique de Campagnes

#### **Architecture**
```
Scraping Lead → Détection Niche → Création Campagne → Liaison Lead
     ↓              ↓                    ↓              ↓
Agent Data    industry + ville    Auto-nommage    campagne_id
```

#### **Implémentation** : Service de Persistance Enhanced

**Fichier** : `infra-ia/core/persistence_service.py`

##### **A. Modification Mapper de Données**
```python
def map_lead_data(self, agent_data: Dict[str, Any], input_data: Dict[str, Any] = None):
    # 🎯 GESTION INTELLIGENTE DES NICHES ET CAMPAGNES
    niche_result = self._handle_niche_assignment(agent_data, input_data)
    if niche_result and len(niche_result) == 2:
        niche_id, is_new_niche = niche_result
        mapped_data['niche_id'] = niche_id
        
        # 📢 NOUVEAU : Création automatique de campagne pour nouvelle niche
        if is_new_niche:
            campaign_id = self._create_campaign_for_niche(niche_id, agent_data, input_data)
            if campaign_id:
                mapped_data['campagne_id'] = campaign_id
```

##### **B. Gestion Intelligente des Niches**
```python
def _handle_niche_assignment(self, agent_data, input_data) -> Optional[Tuple[int, bool]]:
    """
    Retourne : (niche_id, is_new_niche)
    Logique : niche = industry + lieu
    """
    # Extraction industry (métier)
    industry = agent_data.get('industry') or agent_data.get('niche', '')
    
    # Extraction lieu (plusieurs sources)
    location = (input_data.get('city') or 
               input_data.get('location') or 
               agent_data.get('city'))
    
    # Construction nom niche
    niche_name = f"{industry} {location}".strip()
    
    # Recherche niche existante
    existing_niche = self.db.fetch_one("SELECT id FROM niches WHERE name = :name", {"name": niche_name})
    
    if existing_niche:
        return (existing_niche['id'], False)  # Existante
    
    # Création nouvelle niche
    niche_id = self.db.insert('niches', niche_data)
    return (niche_id, True)  # Nouvelle
```

##### **C. Création Automatique de Campagne**
```python
def _create_campaign_for_niche(self, niche_id: int, agent_data, input_data) -> Optional[int]:
    """Crée automatiquement une campagne pour une nouvelle niche"""
    
    # Récupération infos niche
    niche = self.db.fetch_one("SELECT name, description FROM niches WHERE id = :id", {"id": niche_id})
    
    # Construction nom campagne
    today = datetime.utcnow().strftime("%Y-%m-%d")
    campaign_name = f"Campagne {niche['name']} - {today}"
    
    # Détection agent source
    agent_source = input_data.get('agent_name') or agent_data.get('source', 'Scraper Agent')
    
    # Données campagne
    campaign_data = {
        'name': campaign_name,
        'description': f"Campagne automatique pour {niche['description']}",
        'status': 'active',
        'niche_id': niche_id,
        'agent': agent_source,
        'target_leads': 50,  # Objectif par défaut
        'created_at': datetime.utcnow()
    }
    
    campaign_id = self.db.insert('campaigns', campaign_data)
    return campaign_id
```

### 3. Modifications Base de Données

#### **Ajout Colonne campagne_id**
```sql
-- Ajout de la relation Lead → Campaign
ALTER TABLE leads ADD COLUMN campagne_id INTEGER REFERENCES campaigns(id);
```

#### **Correction Modèles SQLAlchemy**

**Lead Model** : `backend/app/models/lead.py`
```python
class Lead(Base):
    # ... autres champs ...
    
    # ✅ ACTIVÉ: colonne campagne_id (cohérent avec système backend)
    campagne_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
```

**Campaign Model** : `backend/app/models/campaign.py`
```python
class Campaign(Base):
    # ... autres champs ...
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Attributs calculés assignables (évite erreur "can't set attribute")
        self.progress = 0
        self.conversion = 0.0
```

### 4. Correction Schémas API

#### **Niche Schema** : `backend/app/schemas/niche.py`
```python
class NicheResponse(NicheBase):
    id: int
    date_creation: Optional[datetime] = Field(default=None, alias="created_at")
    keywords: Optional[Union[str, List[str]]] = None  # Support array PostgreSQL
    
    class Config:
        from_attributes = True
        populate_by_name = True  # Permet d'utiliser les alias
```

#### **Campaign Schema** : `backend/app/schemas/campaign.py`
```python
class Campaign(CampaignBase):
    id: int
    statut: str = Field(..., alias="status")
    date_creation: datetime = Field(..., alias="created_at")
    progress: Optional[int] = 0
    
    class Config:
        from_attributes = True
        populate_by_name = True
```

## 🔄 Workflow Complet

### 1. Déclenchement
```python
# Agent scraping détecte nouveau lead
test_input_data = {
    'niche': 'kinésithérapeute', 
    'city': 'Bordeaux',
    'action': 'scrape'
}

test_lead_data = {
    'leads': [{
        'industry': 'kinésithérapeute',
        'company': 'Cabinet Kiné',
        'email': 'contact@kine-bordeaux.com'
    }]
}
```

### 2. Persistance Intelligente
```python
result = persistence_service.persist_agent_data(
    agent_name='ScraperAgent',
    action='scrape', 
    input_data=test_input_data,
    result_data=test_lead_data
)
```

### 3. Création Automatique
1. **Détection niche** : `"kinésithérapeute Bordeaux"`
2. **Niche nouvelle** → Création niche ID=4
3. **Campagne auto** → `"Campagne kinésithérapeute Bordeaux - 2025-05-27"` ID=1
4. **Lead lié** → `niche_id=4, campagne_id=1`

### 4. Résultat API
```json
{
  "persistence": {
    "status": "success",
    "count": 1,
    "campaigns_created": 1,
    "saved_ids": [8]
  }
}
```

## 📊 Tests et Validation

### Test Complet Réalisé
```python
# 🚀 TEST FINAL - CRÉATION AUTOMATIQUE CAMPAGNES
# Lead: psychologue Lille
# Résultat: 
# - Niche ID=5 "psychologue Lille"  
# - Campagne ID=2 "Campagne psychologue Lille - 2025-05-27"
# - Lead ID=8 avec niche_id=5, campagne_id=2
# ✅ SUCCESS COMPLET
```

### Validation API
```bash
curl -X GET http://localhost:8000/api/campaigns/
# ✅ Retourne 2 campagnes auto-créées avec métadonnées correctes
```

## 🎯 Bénéfices

### 1. Automatisation Complète
- **0 intervention manuelle** pour création campagnes
- **Nommage intelligent** basé sur niche + date
- **Relations automatiques** Lead ↔ Niche ↔ Campagne

### 2. Cohérence Données
- **Format PostgreSQL** : Arrays natifs pour keywords
- **Schémas compatibles** : Alias Pydantic pour mapping DB ↔ API  
- **Modèles cohérents** : SQLAlchemy sans erreurs attributs

### 3. Métriques Automatiques
- **Progress calculé** : Basé sur leads vs target_leads
- **Conversion trackée** : Prêt pour analytics
- **Agent source** : Traçabilité complète

## 🔧 Configuration

### Variables Importantes
```python
# Target leads par défaut pour nouvelles campagnes
'target_leads': 50

# Format nom campagne
campaign_name = f"Campagne {niche['name']} - {today}"

# Agent source detection
agent_source = input_data.get('agent_name') or agent_data.get('source', 'Scraper Agent')
```

### Extensibilité
Le système peut être étendu pour :
- **Règles métier** : Différents target_leads selon niche
- **Templates campagne** : Descriptions personnalisées
- **Conditions création** : Créer campagne seulement si X leads
- **Intégrations** : Notifications, analytics, etc.

## 📝 Notes Techniques

### Compatibilité Nommage
- **Base de données** : `campagne_id`, `name`, `status`, `created_at`
- **API française** : `nom`, `statut`, `date_creation`
- **Solution** : Alias Pydantic bidirectionnels

### Gestion Erreurs
- **Niches existantes** : Pas de création campagne duplicate
- **Mapping robuste** : Fallbacks pour champs manquants
- **Logs détaillés** : Traçabilité complète des créations

Cette implémentation fournit un système robuste et automatisé de gestion des campagnes, éliminant le besoin de création manuelle tout en maintenant la cohérence des données.
