from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.sql import expression
from app.database.base_class import Base

class SystemSetting(Base):
    """Modèle pour la table system_settings avec structure key-value."""

    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    data_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_editable = Column(Boolean, default=True, server_default=expression.true())
    created_at = Column(DateTime, default=func.now(), server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemSetting(name='{self.name}', category='{self.category}')>"
    
    @property
    def typed_value(self):
        """Renvoie la valeur convertie selon son type."""
        if not self.value:
            return None
        
        if self.data_type == 'boolean':
            return self.value.lower() == 'true'
        elif self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'json':
            import json
            try:
                return json.loads(self.value)
            except:
                return {}
        else:  # string ou autre
            return self.value
