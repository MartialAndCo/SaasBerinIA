from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime
from app.schemas.campaign import Campaign

class NicheBase(BaseModel):
    nom: str = Field(..., alias="name")  # ✅ Alias pour compatibilité
    description: Optional[str] = None
    statut: Optional[str] = Field(default="active", alias="status")  # ✅ Alias pour compatibilité
    keywords: Optional[Union[str, List[str]]] = None  # ✅ CORRECTION: accepte string OU array

class NicheCreate(NicheBase):
    pass

class NicheUpdate(NicheBase):
    nom: Optional[str] = Field(default=None, alias="name")

class NicheResponse(NicheBase):
    id: int
    date_creation: Optional[datetime] = Field(default=None, alias="created_at")  # ✅ Alias pour compatibilité
    updated_at: Optional[datetime] = None
    exploration_depth: Optional[int] = 1
    
    # Propriétés calculées pour compatibilité complète
    taux_conversion: Optional[float] = 0.0
    cout_par_lead: Optional[float] = 0.0
    recommandation: Optional[str] = "Continuer"
    
    class Config:
        from_attributes = True
        populate_by_name = True  # ✅ Permet d'utiliser les alias
