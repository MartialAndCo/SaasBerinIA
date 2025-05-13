from sqlalchemy.orm import Session
from app.models.system_settings import SystemIntegrations, SystemScheduling

class SystemSettingsService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_integrations(self, **kwargs):
        integration = self.db.query(SystemIntegrations).first()
        if not integration:
            integration = SystemIntegrations()
            self.db.add(integration)
        
        for key, value in kwargs.items():
            setattr(integration, key, value)
        
        self.db.commit()
        self.db.refresh(integration)
        return integration
    
    def update_scheduling(self, **kwargs):
        scheduling = self.db.query(SystemScheduling).first()
        if not scheduling:
            scheduling = SystemScheduling()
            self.db.add(scheduling)
        
        for key, value in kwargs.items():
            setattr(scheduling, key, value)
        
        self.db.commit()
        self.db.refresh(scheduling)
        return scheduling
    
    def get_integrations(self):
        return self.db.query(SystemIntegrations).first()
    
    def get_scheduling(self):
        return self.db.query(SystemScheduling).first()
