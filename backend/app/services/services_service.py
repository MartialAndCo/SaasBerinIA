import subprocess
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
import datetime

logger = logging.getLogger(__name__)

class ServicesService:
    """Service pour gérer les services systemd de BerinIA"""
    
    # Liste des services gérés
    MANAGED_SERVICES = [
        "berinia.service",
        "berinia-next.service",
        "berinia-webhook.service",
        "berinia-whatsapp.service",
        "berinia-qdrant.service",
        "berinia-agents.service",
        "berinia-scheduler.service"
    ]
    
    # Descriptions des services
    SERVICE_DESCRIPTIONS = {
        "berinia.service": "API backend principale",
        "berinia-next.service": "Frontend Next.js",
        "berinia-webhook.service": "Serveur webhook pour réception d'événements externes",
        "berinia-whatsapp.service": "Intégration WhatsApp",
        "berinia-qdrant.service": "Base de données vectorielle Qdrant",
        "berinia-agents.service": "Environnement d'exécution des agents IA",
        "berinia-scheduler.service": "Planificateur de tâches"
    }
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un service systemd.
        
        Args:
            service_name: Nom du service
            
        Returns:
            Dictionnaire contenant les informations de statut du service
        """
        if service_name not in self.MANAGED_SERVICES:
            raise ValueError(f"Service non géré: {service_name}")
            
        try:
            # Vérifier si le service est actif
            status_cmd = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True, text=True, check=False
            )
            status = status_cmd.stdout.strip()
            is_active = status == 'active'
            
            # Vérifier si le service est activé au démarrage
            enabled_cmd = subprocess.run(
                ['systemctl', 'is-enabled', service_name],
                capture_output=True, text=True, check=False
            )
            enabled_status = enabled_cmd.stdout.strip()
            is_enabled = enabled_status == 'enabled'
            
            # Récupérer le temps d'exécution (uptime) pour les services actifs
            uptime = None
            if is_active:
                uptime_cmd = subprocess.run(
                    ['systemctl', 'show', service_name, '--property=ActiveEnterTimestamp'],
                    capture_output=True, text=True, check=False
                )
                
                # Extraire le timestamp d'activation
                if uptime_cmd.returncode == 0:
                    timestamp_str = uptime_cmd.stdout.strip().split('=')[1]
                    # On pourrait calculer l'uptime à partir du timestamp
                    uptime = self._calculate_uptime_from_timestamp(timestamp_str)
            
            # Récupérer des informations supplémentaires sur le service
            description = self.SERVICE_DESCRIPTIONS.get(service_name, "")
            
            return {
                'name': service_name,
                'display_name': service_name.replace('.service', ''),
                'description': description,
                'status': status,
                'is_active': is_active,
                'is_enabled': is_enabled,
                'uptime': uptime
            }
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du service {service_name}: {str(e)}")
            return {
                'name': service_name,
                'display_name': service_name.replace('.service', ''),
                'description': self.SERVICE_DESCRIPTIONS.get(service_name, ""),
                'status': 'error',
                'is_active': False,
                'is_enabled': False,
                'error': str(e)
            }
    
    def get_all_services(self) -> List[Dict[str, Any]]:
        """
        Récupère le statut de tous les services gérés.
        
        Returns:
            Liste des informations de statut pour tous les services
        """
        return [self.get_service_status(service) for service in self.MANAGED_SERVICES]
    
    def execute_action(self, service_name: str, action: str) -> Dict[str, Any]:
        """
        Exécute une action sur un service systemd.
        
        Args:
            service_name: Nom du service
            action: Action à effectuer (start, stop, restart, enable, disable)
            
        Returns:
            Résultat de l'action
        """
        if service_name not in self.MANAGED_SERVICES:
            raise ValueError(f"Service non géré: {service_name}")
            
        if action not in ["start", "stop", "restart", "enable", "disable"]:
            raise ValueError(f"Action non valide: {action}")
        
        try:
            # Utiliser sudo pour les opérations systemctl qui nécessitent des privilèges élevés
            result = subprocess.run(
                ['sudo', 'systemctl', action, service_name],
                capture_output=True, text=True, check=True
            )
            
            # Attendre un court instant pour que systemd mette à jour le statut
            import time
            time.sleep(1)
            
            # Récupérer le nouveau statut du service
            new_status = self.get_service_status(service_name)
            
            return {
                'success': True,
                'message': f"Action {action} exécutée avec succès sur {service_name}",
                'stdout': result.stdout,
                'stderr': result.stderr,
                'service': new_status
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de l'exécution de {action} sur {service_name}: {e.stderr}")
            return {
                'success': False,
                'message': f"Erreur lors de l'exécution de {action} sur {service_name}",
                'stdout': e.stdout,
                'stderr': e.stderr,
                'service': self.get_service_status(service_name)
            }
    
    def get_service_logs(self, service_name: str, lines: int = 50) -> Dict[str, Any]:
        """
        Récupère les logs d'un service systemd.
        
        Args:
            service_name: Nom du service
            lines: Nombre de lignes à récupérer
            
        Returns:
            Logs du service
        """
        if service_name not in self.MANAGED_SERVICES:
            raise ValueError(f"Service non géré: {service_name}")
            
        try:
            result = subprocess.run(
                ['journalctl', '-u', service_name, '-n', str(lines), '--no-pager'],
                capture_output=True, text=True, check=True
            )
            
            return {
                'success': True,
                'logs': result.stdout.splitlines(),
                'service': service_name
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de la récupération des logs de {service_name}: {e.stderr}")
            return {
                'success': False,
                'message': f"Erreur lors de la récupération des logs: {e.stderr}",
                'service': service_name
            }
    
    def _calculate_uptime_from_timestamp(self, timestamp_str: str) -> str:
        """
        Calcule l'uptime à partir d'un timestamp.
        
        Args:
            timestamp_str: Timestamp au format systemd
            
        Returns:
            Uptime formaté
        """
        try:
            # Les timestamps systemd sont généralement au format: "Day YYYY-MM-DD HH:MM:SS UTC"
            # Nous allons extraire la date et l'heure
            import dateutil.parser
            
            # Analyser le timestamp
            start_time = dateutil.parser.parse(timestamp_str)
            
            # Calculer la durée depuis le démarrage
            now = datetime.datetime.now(start_time.tzinfo)
            uptime_delta = now - start_time
            
            # Formater l'uptime
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m {seconds}s"
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'uptime: {str(e)}")
            return "inconnu"
