from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NicheBase(BaseModel):
    nom: str
    description: Optional[str] = None
    statut: str
    taux_conversion: float
    cout_par_lead: float
    recommandation: str


class NicheCreate(NicheBase):
    pass


class NicheUpdate(NicheBase):
    nom: Optional[str] = None
    statut: Optional[str] = None
    taux_conversion: Optional[float] = None
    cout_par_lead: Optional[float] = None
    recommandation: Optional[str] = None


class NicheInDB(NicheBase):
    id: int
    date_creation: datetime
    
    class Config:
        orm_mode = True


class Niche(NicheInDB):
    campagnes: int = 0
    leads: int = 0 