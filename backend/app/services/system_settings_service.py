from sqlalchemy.orm import Session
from app.models.system_setting import SystemSetting

class SystemSettingsService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_integrations(self, **kwargs):
        """
        Met à jour les paramètres d'intégration dans la table system_settings.
        Retourne un dictionnaire des paramètres mis à jour.
        """
        result = {}
        for key, value in kwargs.items():
            # Rechercher le paramètre existant
            setting = self.db.query(SystemSetting).filter(
                SystemSetting.name == key,
                SystemSetting.category == 'integrations'
            ).first()
            
            # Si le paramètre n'existe pas, on l'ignore (sécurité)
            if setting:
                # Convertir la valeur en string pour le stockage
                if value is None:
                    setting.value = None
                elif isinstance(value, bool):
                    setting.value = str(value).lower()
                else:
                    setting.value = str(value)
                    
                # Ajouter au dictionnaire de résultat
                result[key] = setting.typed_value
        
        self.db.commit()
        return result
    
    def update_scheduling(self, **kwargs):
        """
        Met à jour les paramètres de planification dans la table system_settings.
        Retourne un dictionnaire des paramètres mis à jour.
        """
        result = {}
        for key, value in kwargs.items():
            # Rechercher le paramètre existant
            setting = self.db.query(SystemSetting).filter(
                SystemSetting.name == key,
                SystemSetting.category == 'scheduling'
            ).first()
            
            # Si le paramètre n'existe pas, on l'ignore (sécurité)
            if setting:
                # Convertir la valeur en string pour le stockage
                if value is None:
                    setting.value = None
                elif isinstance(value, bool):
                    setting.value = str(value).lower()
                else:
                    setting.value = str(value)
                    
                # Ajouter au dictionnaire de résultat
                result[key] = setting.typed_value
        
        self.db.commit()
        return result
    
    def get_integrations(self):
        """
        Récupère tous les paramètres d'intégration et les retourne en format dictionnaire.
        """
        settings = self.db.query(SystemSetting).filter(
            SystemSetting.category == 'integrations'
        ).all()
        
        # Convertir la liste de paramètres en dictionnaire
        result = {}
        for setting in settings:
            result[setting.name] = setting.typed_value
            
        return result
    
    def get_scheduling(self):
        """
        Récupère tous les paramètres de planification et les retourne en format dictionnaire.
        """
        settings = self.db.query(SystemSetting).filter(
            SystemSetting.category == 'scheduling'
        ).all()
        
        # Convertir la liste de paramètres en dictionnaire
        result = {}
        for setting in settings:
            result[setting.name] = setting.typed_value
            
        return result
    
    def get_setting(self, name):
        """
        Récupère un paramètre spécifique par son nom.
        """
        setting = self.db.query(SystemSetting).filter(SystemSetting.name == name).first()
        return setting.typed_value if setting else None
    
    def update_setting(self, name, value, data_type=None, category=None, description=None):
        """
        Met à jour ou crée un paramètre système.
        """
        setting = self.db.query(SystemSetting).filter(SystemSetting.name == name).first()
        
        if not setting:
            # Créer un nouveau paramètre
            setting = SystemSetting(
                name=name,
                data_type=data_type or 'string',
                category=category,
                description=description
            )
            self.db.add(setting)
        
        # Mettre à jour la valeur
        if value is None:
            setting.value = None
        elif isinstance(value, bool):
            setting.value = str(value).lower()
        else:
            setting.value = str(value)
            
        # Mettre à jour les autres champs si fournis
        if data_type:
            setting.data_type = data_type
        if category:
            setting.category = category
        if description:
            setting.description = description
            
        self.db.commit()
        self.db.refresh(setting)
        return setting.typed_value
