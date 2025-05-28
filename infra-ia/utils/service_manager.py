#!/usr/bin/env python3
"""
Module utilitaire pour gérer les services systemd dans BerinIA.

Ce module permet de:
- Obtenir le statut des services systemd
- Démarrer, arrêter et redémarrer des services 
- Récupérer les logs des services
"""

import subprocess
import logging
import datetime
import os
from typing import Dict, List, Any, Optional, Tuple

# Configuration du logger
logger = logging.getLogger("berinia.utils.service_manager")

class ServiceManager:
    """Gestionnaire de services systemd pour BerinIA."""
    
    # Liste des services gérés par BerinIA
    SERVICES = [
        "berinia-api.service",
        "berinia-next.service",
        "berinia-webhook.service",
        "berinia-whatsapp.service",
        "berinia-qdrant.service",
        "berinia-agents.service",
        "berinia-scheduler.service"
    ]
    
    # Description des services
    SERVICE_DESCRIPTIONS = {
        "berinia-api.service": "API backend principale",
        "berinia-next.service": "Frontend Next.js",
        "berinia-webhook.service": "Serveur webhook pour réception d'événements externes",
        "berinia-whatsapp.service": "Intégration WhatsApp",
        "berinia-qdrant.service": "Base de données vectorielle Qdrant",
        "berinia-agents.service": "Environnement d'exécution des agents IA",
        "berinia-scheduler.service": "Planificateur de tâches"
    }
    
    def __init__(self):
        """Initialise le gestionnaire de services."""
        self._check_systemctl()
    
    def _check_systemctl(self) -> bool:
        """Vérifie que systemctl est disponible."""
        try:
            subprocess.run(["systemctl", "--version"], 
                           check=True, capture_output=True, text=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("systemctl n'est pas disponible. Impossible de gérer les services.")
            return False
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un service systemd.
        
        Args:
            service_name: Nom du service
            
        Returns:
            Dictionnaire contenant les informations de statut du service
        """
        if service_name not in self.SERVICES:
            logger.warning(f"Service inconnu: {service_name}")
            return {
                'name': service_name,
                'display_name': service_name.replace('.service', ''),
                'description': "Service non géré par BerinIA",
                'status': 'unknown',
                'is_active': False,
                'is_enabled': False,
                'error': "Service non géré par BerinIA"
            }
            
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
                    # Calculer l'uptime à partir du timestamp
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
        return [self.get_service_status(service) for service in self.SERVICES]
    
    def execute_action(self, service_name: str, action: str) -> Dict[str, Any]:
        """
        Exécute une action sur un service systemd.
        
        Args:
            service_name: Nom du service
            action: Action à effectuer (start, stop, restart, enable, disable)
            
        Returns:
            Résultat de l'action
        """
        if service_name not in self.SERVICES:
            logger.warning(f"Service inconnu: {service_name}")
            return {
                'success': False,
                'message': f"Service {service_name} non géré par BerinIA",
                'service': {
                    'name': service_name,
                    'status': 'unknown'
                }
            }
            
        if action not in ["start", "stop", "restart", "enable", "disable"]:
            logger.warning(f"Action non valide: {action}")
            return {
                'success': False,
                'message': f"Action {action} non valide",
                'service': self.get_service_status(service_name)
            }
        
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
        if service_name not in self.SERVICES:
            logger.warning(f"Service inconnu: {service_name}")
            return {
                'success': False,
                'message': f"Service {service_name} non géré par BerinIA",
                'service': service_name
            }
            
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
            # Les timestamps systemd sont au format: "Day YYYY-MM-DD HH:MM:SS UTC"
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


# Instance singleton pour usage simple
service_manager = ServiceManager()

def get_service_status(service_name: str) -> Dict[str, Any]:
    """Fonction helper pour obtenir le statut d'un service."""
    return service_manager.get_service_status(service_name)

def get_all_services() -> List[Dict[str, Any]]:
    """Fonction helper pour obtenir le statut de tous les services."""
    return service_manager.get_all_services()

def execute_action(service_name: str, action: str) -> Dict[str, Any]:
    """Fonction helper pour exécuter une action sur un service."""
    return service_manager.execute_action(service_name, action)

def get_service_logs(service_name: str, lines: int = 50) -> Dict[str, Any]:
    """Fonction helper pour obtenir les logs d'un service."""
    return service_manager.get_service_logs(service_name, lines)
