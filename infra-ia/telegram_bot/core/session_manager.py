"""Gestionnaire de sessions par utilisateur pour éviter les conflits d'état"""
import time
from typing import Dict, Any, Optional
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class UserSessionManager:
    """Gestionnaire de sessions par utilisateur avec nettoyage automatique"""
    
    def __init__(self, session_timeout: int = 1800):  # 30 minutes
        self.sessions: Dict[int, Dict[str, Any]] = {}  # user_id -> session_data
        self.timestamps: Dict[int, float] = {}  # user_id -> last_activity
        self.session_timeout = session_timeout
        self.lock = Lock()  # Protection contre la concurrence
    
    def get_session(self, user_id: int) -> Dict[str, Any]:
        """
        Récupère ou crée une session pour un utilisateur
        
        Args:
            user_id: ID de l'utilisateur Telegram
            
        Returns:
            Dictionnaire de session pour cet utilisateur
        """
        with self.lock:
            self._cleanup_expired_sessions()
            
            if user_id not in self.sessions:
                self.sessions[user_id] = {}
                logger.debug(f"Nouvelle session créée pour utilisateur {user_id}")
            
            self.timestamps[user_id] = time.time()
            return self.sessions[user_id]
    
    def set_session_data(self, user_id: int, key: str, value: Any):
        """
        Stocke une donnée dans la session utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            key: Clé de la donnée
            value: Valeur à stocker
        """
        with self.lock:
            session = self.get_session(user_id)
            session[key] = value
            logger.debug(f"Session data set for user {user_id}: {key}")
    
    def get_session_data(self, user_id: int, key: str, default: Any = None) -> Any:
        """
        Récupère une donnée de la session utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            key: Clé de la donnée
            default: Valeur par défaut si non trouvée
            
        Returns:
            Valeur stockée ou default
        """
        with self.lock:
            session = self.get_session(user_id)
            return session.get(key, default)
    
    def clear_session(self, user_id: int):
        """
        Vide complètement la session d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
        """
        with self.lock:
            if user_id in self.sessions:
                del self.sessions[user_id]
            if user_id in self.timestamps:
                del self.timestamps[user_id]
            logger.debug(f"Session cleared for user {user_id}")
    
    def clear_session_key(self, user_id: int, key: str):
        """
        Supprime une clé spécifique de la session utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            key: Clé à supprimer
        """
        with self.lock:
            session = self.get_session(user_id)
            if key in session:
                del session[key]
                logger.debug(f"Session key '{key}' cleared for user {user_id}")
    
    def _cleanup_expired_sessions(self):
        """Nettoie les sessions expirées"""
        now = time.time()
        expired_users = []
        
        for user_id, last_activity in self.timestamps.items():
            if now - last_activity > self.session_timeout:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self.clear_session(user_id)
            logger.info(f"Session expirée nettoyée pour utilisateur {user_id}")
    
    def get_active_sessions_count(self) -> int:
        """Retourne le nombre de sessions actives"""
        with self.lock:
            self._cleanup_expired_sessions()
            return len(self.sessions)
    
    def force_cleanup_all(self):
        """Force le nettoyage de toutes les sessions (pour debugging)"""
        with self.lock:
            user_count = len(self.sessions)
            self.sessions.clear()
            self.timestamps.clear()
            logger.info(f"Toutes les sessions ont été forcées au nettoyage ({user_count} sessions)")

# Instance globale partagée
session_manager = UserSessionManager()
