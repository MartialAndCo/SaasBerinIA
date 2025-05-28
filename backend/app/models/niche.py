from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base_class import Base

class Niche(Base):
    __tablename__ = "niches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    status = Column(String, default='active')
    exploration_depth = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Propriétés calculées pour compatibilité frontend
    @property
    def nom(self):
        return self.name
    
    @property
    def statut(self):
        return self.status
        
    @property
    def date_creation(self):
        return self.created_at
    
    @property
    def taux_conversion(self):
        return 0.0  # Valeur par défaut
    
    @property
    def cout_par_lead(self):
        return 0.0  # Valeur par défaut
    
    @property
    def recommandation(self):
        return 'Continuer'  # Valeur par défaut

    # Relations temporairement supprimées pour éviter les erreurs
    # campaigns = relationship("Campaign", back_populates="niche")
