"""Gestionnaire universel des callback_data pour éviter les dépassements de limite"""
import hashlib
import json
import time
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CallbackManager:
    """Gestionnaire centralisé des callback_data avec mapping court et persistance"""
    
    def __init__(self):
        self.storage_file = "/tmp/berinia_callbacks.json"
        self.callbacks: Dict[str, Dict[str, Any]] = {}  # mapping id -> data complet
        self.reverse_map: Dict[str, str] = {}  # mapping hash(data) -> id
        self.counter = 0
        self.cleanup_interval = 3600  # 1 heure
        self.last_cleanup = time.time()
        
        # Charger depuis le fichier persistant
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Charge les callbacks depuis le fichier persistant"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.callbacks = data.get('callbacks', {})
                    self.reverse_map = data.get('reverse_map', {})
                    self.counter = data.get('counter', 0)
                logger.debug(f"Callbacks chargés: {len(self.callbacks)} éléments")
        except Exception as e:
            logger.warning(f"Erreur chargement callbacks: {e}")
            self.callbacks = {}
            self.reverse_map = {}
            self.counter = 0
    
    def _save_to_disk(self):
        """Sauvegarde les callbacks sur disque"""
        try:
            data = {
                'callbacks': self.callbacks,
                'reverse_map': self.reverse_map,
                'counter': self.counter,
                'timestamp': time.time()
            }
            with open(self.storage_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Erreur sauvegarde callbacks: {e}")
    
    def _generate_short_id(self) -> str:
        """Génère un ID court unique"""
        self.counter += 1
        return f"cb_{self.counter:04d}"
    
    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Génère un hash stable des données"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()[:16]
    
    def register(self, action: str, **kwargs) -> str:
        """
        Enregistre des données et retourne un callback_data court
        
        Args:
            action: Action à exécuter
            **kwargs: Paramètres additionnels
            
        Returns:
            Callback_data court (< 64 bytes)
        """
        # Nettoyer périodiquement
        self._cleanup_if_needed()
        
        data = {"action": action, **kwargs}
        data_hash = self._hash_data(data)
        
        # Réutiliser si déjà existant
        if data_hash in self.reverse_map:
            return self.reverse_map[data_hash]
        
        # Créer nouveau mapping
        short_id = self._generate_short_id()
        
        # Sécurité : vérifier la longueur
        if len(short_id) >= 64:
            logger.error(f"Callback ID trop long: {short_id}")
            short_id = short_id[:63]  # Truncate en dernier recours
        
        self.callbacks[short_id] = data
        self.reverse_map[data_hash] = short_id
        
        # Sauvegarder immédiatement
        self._save_to_disk()
        
        logger.debug(f"Registered callback: {short_id} -> {data}")
        return short_id
    
    def resolve(self, callback_id: str) -> Optional[Dict[str, Any]]:
        """
        Résout un callback_id vers les données complètes
        
        Args:
            callback_id: ID court à résoudre
            
        Returns:
            Données complètes ou None si non trouvé
        """
        # Recharger depuis le disque pour avoir la version la plus récente
        self._load_from_disk()
        
        data = self.callbacks.get(callback_id)
        if not data:
            logger.warning(f"Callback ID non trouvé: {callback_id}")
        return data
    
    def _cleanup_if_needed(self):
        """Nettoie périodiquement les anciens callbacks"""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_callbacks()
            self.last_cleanup = now
    
    def _cleanup_old_callbacks(self):
        """Nettoie les callbacks anciens (plus de 2 heures)"""
        try:
            # Charger le timestamp de création
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    file_timestamp = data.get('timestamp', 0)
                    
                    # Si le fichier a plus de 2 heures, le nettoyer
                    if time.time() - file_timestamp > 7200:  # 2 heures
                        self.callbacks.clear()
                        self.reverse_map.clear()
                        self.counter = 0
                        self._save_to_disk()
                        logger.info("Nettoyage automatique des callbacks anciens")
        except Exception as e:
            logger.error(f"Erreur nettoyage callbacks: {e}")
    
    def clear_all(self):
        """Vide tous les callbacks (pour debugging/reset)"""
        self.callbacks.clear()
        self.reverse_map.clear()
        self.counter = 0
        
        # Supprimer le fichier
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
        except Exception as e:
            logger.error(f"Erreur suppression fichier callbacks: {e}")
        
        logger.info("Tous les callbacks ont été supprimés")

# Instance globale partagée
callback_manager = CallbackManager()