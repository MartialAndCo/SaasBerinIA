"""
Module du LoggerAgent - Agent central de traçage des communications entre agents
"""
import os
import json
import logging
import datetime
import uuid
import time
from typing import Dict, Any, Optional, List, Union

from core.agent_base import Agent
from core.db import DatabaseService
from utils.logger import get_logger, agent_message

class LoggerAgent(Agent):
    """
    LoggerAgent - Agent responsable de la centralisation des logs et communications
    
    Cet agent est responsable de:
    - Enregistrer toutes les interactions entre agents
    - Fournir un historique des actions et décisions
    - Permettre la visualisation sous forme de chat des échanges
    - Assurer la traçabilité du système
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du LoggerAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("LoggerAgent", config_path)
        
        # S'assurer que le dossier de logs existe
        self.logs_dir = self.config.get("logs_dir", "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Configuration du logging
        self._setup_logging()
        
        # État de l'agent
        self.log_stats = {
            "total_logs": 0,
            "agent_messages": 0,
            "admin_messages": 0,
            "system_logs": 0,
            "campaigns": {}
        }
        
        # Cache des messages récents
        self.messages_cache = []
        self.max_cache_size = self.config.get("max_cache_size", 1000)
        
        # Connexion à la base de données pour la persistance
        self.db = DatabaseService()
        
        # Mode test
        self.test_mode = self.config.get("test_mode", True)
        
        # Fichier jsonl pour les logs
        self.jsonl_path = os.path.join(self.logs_dir, "agent_interactions.jsonl")
    
    def _setup_logging(self):
        """Configure le logging pour le LoggerAgent."""
        log_level = getattr(logging, self.config.get("log_level", "INFO"))
        log_format = self.config.get(
            "log_format", 
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Création du logger avec un nom unique (singleton)
        self.logger = logging.getLogger("BerinIA-Logger")
        
        # IMPORTANT: Si le logger a déjà des handlers, nous ne les ajoutons pas à nouveau
        # C'est crucial pour éviter les messages en double
        if self.logger.handlers:
            return
            
        self.logger.setLevel(log_level)
        
        # Handler pour la console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)
        
        # Handler pour le fichier
        file_handler = logging.FileHandler(os.path.join(self.logs_dir, "berinia.log"))
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        
        # Ajout des handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "")
        
        if action == "log_interaction":
            return self.log_interaction(
                from_agent=input_data.get("from_agent", ""),
                to_agent=input_data.get("to_agent", ""),
                message=input_data.get("message", ""),
                context_id=input_data.get("context_id", ""),
                metadata=input_data.get("metadata", {})
            )
        
        elif action == "get_logs":
            return self.get_logs(
                filters=input_data.get("filters", {}),
                limit=input_data.get("limit", 100),
                offset=input_data.get("offset", 0)
            )
        
        elif action == "get_conversation":
            return self.get_conversation(
                context_id=input_data.get("context_id", ""),
                from_agent=input_data.get("from_agent", None),
                to_agent=input_data.get("to_agent", None),
                limit=input_data.get("limit", 100),
                offset=input_data.get("offset", 0)
            )
        
        elif action == "get_stats":
            return {
                "status": "success",
                "stats": self.log_stats
            }
        
        elif action == "clear_cache":
            self.messages_cache = []
            return {
                "status": "success",
                "message": "Cache cleared"
            }
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }
    
    def log_interaction(
        self, 
        from_agent: str, 
        to_agent: Optional[str], 
        message: str,
        context_id: str = "",
        metadata: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Enregistre une interaction entre agents
        
        Args:
            from_agent: Agent source du message
            to_agent: Agent destinataire du message (optionnel)
            message: Contenu du message
            context_id: ID du contexte (campagne, conversation, etc.)
            metadata: Métadonnées supplémentaires
            
        Returns:
            Résultat de l'enregistrement
        """
        # Création du log
        timestamp = datetime.datetime.now().isoformat()
        log_id = str(uuid.uuid4())
        
        log_entry = {
            "id": log_id,
            "timestamp": timestamp,
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "context_id": context_id,
            "metadata": metadata
        }
        
        # Mise à jour des statistiques
        self.log_stats["total_logs"] += 1
        
        if from_agent.lower().startswith("admin"):
            self.log_stats["admin_messages"] += 1
        else:
            self.log_stats["agent_messages"] += 1
        
        # Mise à jour des stats par campagne si applicable
        if context_id and context_id.startswith("campaign_"):
            if context_id not in self.log_stats["campaigns"]:
                self.log_stats["campaigns"][context_id] = 0
            self.log_stats["campaigns"][context_id] += 1
        
        # Ajout au cache
        self.messages_cache.append(log_entry)
        
        # Limitation de la taille du cache
        if len(self.messages_cache) > self.max_cache_size:
            self.messages_cache = self.messages_cache[-self.max_cache_size:]
        
        # Enregistrement en base de données
        if not self.test_mode:
            try:
                self._save_to_database(log_entry)
            except Exception as e:
                self.logger.error(f"Erreur lors de l'enregistrement en base de données: {e}")
        
        # Enregistrement dans un fichier jsonl
        self._save_to_jsonl(log_entry)
        
        # Log dans le logger standard
        log_message = f"{from_agent} → {to_agent or 'broadcast'}: {message[:100]}..."
        self.logger.info(log_message)
        
        return {
            "status": "success",
            "log_id": log_id,
            "timestamp": timestamp
        }
    
    def get_logs(
        self, 
        filters: Dict[str, Any] = {}, 
        limit: int = 100, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Récupère les logs selon des filtres
        
        Args:
            filters: Filtres à appliquer
            limit: Nombre maximum de logs à retourner
            offset: Décalage pour la pagination
            
        Returns:
            Logs correspondants aux filtres
        """
        # Récupération depuis le cache si possible
        if not filters and offset == 0 and limit <= len(self.messages_cache):
            logs = self.messages_cache[-limit:]
            logs.reverse()  # Plus récents en premier
            return {
                "status": "success",
                "count": len(logs),
                "total": len(self.messages_cache),
                "logs": logs
            }
        
        # Sinon, récupération depuis la base de données ou le fichier jsonl
        if self.test_mode:
            logs = self._get_logs_from_jsonl(filters, limit, offset)
        else:
            logs = self._get_logs_from_database(filters, limit, offset)
        
        return {
            "status": "success",
            "count": len(logs),
            "total": self._count_logs(filters),
            "logs": logs
        }
    
    def get_conversation(
        self, 
        context_id: str = "", 
        from_agent: Optional[str] = None, 
        to_agent: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Récupère une conversation entre agents
        
        Args:
            context_id: ID du contexte (campagne, conversation, etc.)
            from_agent: Filtrer par agent source
            to_agent: Filtrer par agent destinataire
            limit: Nombre maximum de messages à retourner
            offset: Décalage pour la pagination
            
        Returns:
            Messages de la conversation
        """
        filters = {}
        
        if context_id:
            filters["context_id"] = context_id
        
        if from_agent:
            filters["from"] = from_agent
        
        if to_agent:
            filters["to"] = to_agent
        
        return self.get_logs(filters, limit, offset)
    
    def _save_to_database(self, log_entry: Dict[str, Any]) -> None:
        """
        Sauvegarde un log en base de données
        
        Args:
            log_entry: Entrée de log à sauvegarder
        """
        try:
            query = """
            INSERT INTO agent_logs (
                id, timestamp, from_agent, to_agent, message, 
                context_id, metadata
            ) VALUES (
                :id, :timestamp, :from, :to, :message, 
                :context_id, :metadata
            )
            """
            
            params = {
                "id": log_entry["id"],
                "timestamp": log_entry["timestamp"],
                "from": log_entry["from"],
                "to": log_entry["to"],
                "message": log_entry["message"],
                "context_id": log_entry["context_id"],
                "metadata": json.dumps(log_entry["metadata"])
            }
            
            self.db.execute(query, params)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement en base de données: {e}")
            raise
    
    def _save_to_jsonl(self, log_entry: Dict[str, Any]) -> None:
        """
        Sauvegarde un log dans un fichier jsonl
        
        Args:
            log_entry: Entrée de log à sauvegarder
        """
        try:
            with open(self.jsonl_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement dans le fichier jsonl: {e}")
    
    def _get_logs_from_database(
        self, 
        filters: Dict[str, Any],
        limit: int, 
        offset: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère des logs depuis la base de données
        
        Args:
            filters: Filtres à appliquer
            limit: Nombre maximum de logs à retourner
            offset: Décalage pour la pagination
            
        Returns:
            Logs correspondants aux filtres
        """
        try:
            # Construction de la clause WHERE
            where_clauses = []
            params = {}
            
            for key, value in filters.items():
                column_name = key
                if key == "from":
                    column_name = "from_agent"
                elif key == "to":
                    column_name = "to_agent"
                
                where_clauses.append(f"{column_name} = :{key}")
                params[key] = value
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Requête
            query = f"""
            SELECT id, timestamp, from_agent, to_agent, message, 
                   context_id, metadata
            FROM agent_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
            """
            
            params["limit"] = limit
            params["offset"] = offset
            
            # Exécution de la requête
            results = self.db.fetch_all(query, params)
            
            # Transformation des résultats
            logs = []
            for row in results:
                log = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "from": row["from_agent"],
                    "to": row["to_agent"],
                    "message": row["message"],
                    "context_id": row["context_id"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }
                logs.append(log)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération depuis la base de données: {e}")
            return []
    
    def _get_logs_from_jsonl(
        self, 
        filters: Dict[str, Any],
        limit: int, 
        offset: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère des logs depuis un fichier jsonl
        
        Args:
            filters: Filtres à appliquer
            limit: Nombre maximum de logs à retourner
            offset: Décalage pour la pagination
            
        Returns:
            Logs correspondants aux filtres
        """
        try:
            if not os.path.exists(self.jsonl_path):
                return []
            
            # Lecture du fichier jsonl
            logs = []
            with open(self.jsonl_path, "r") as f:
                for line in f:
                    if line.strip():
                        log = json.loads(line)
                        logs.append(log)
            
            # Application des filtres
            filtered_logs = []
            for log in logs:
                match = True
                for key, value in filters.items():
                    if log.get(key) != value:
                        match = False
                        break
                
                if match:
                    filtered_logs.append(log)
            
            # Tri par timestamp (du plus récent au plus ancien)
            filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Application de la pagination
            paginated_logs = filtered_logs[offset:offset+limit]
            
            return paginated_logs
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération depuis le fichier jsonl: {e}")
            return []
    
    def _count_logs(self, filters: Dict[str, Any]) -> int:
        """
        Compte le nombre de logs correspondant aux filtres
        
        Args:
            filters: Filtres à appliquer
            
        Returns:
            Nombre de logs
        """
        if self.test_mode:
            # Comptage depuis le fichier jsonl
            try:
                if not os.path.exists(self.jsonl_path):
                    return 0
                
                count = 0
                with open(self.jsonl_path, "r") as f:
                    for line in f:
                        if line.strip():
                            log = json.loads(line)
                            
                            match = True
                            for key, value in filters.items():
                                if log.get(key) != value:
                                    match = False
                                    break
                            
                            if match:
                                count += 1
                
                return count
                
            except Exception as e:
                self.logger.error(f"Erreur lors du comptage depuis le fichier jsonl: {e}")
                return 0
        else:
            # Comptage depuis la base de données
            try:
                # Construction de la clause WHERE
                where_clauses = []
                params = {}
                
                for key, value in filters.items():
                    column_name = key
                    if key == "from":
                        column_name = "from_agent"
                    elif key == "to":
                        column_name = "to_agent"
                    
                    where_clauses.append(f"{column_name} = :{key}")
                    params[key] = value
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                # Requête
                query = f"""
                SELECT COUNT(*) as count
                FROM agent_logs
                WHERE {where_clause}
                """
                
                # Exécution de la requête
                result = self.db.fetch_one(query, params)
                
                return result.get("count", 0) if result else 0
                
            except Exception as e:
                self.logger.error(f"Erreur lors du comptage depuis la base de données: {e}")
                return 0
    
    # Stockage de l'instance unique (singleton pattern)
    _instance = None
    
    @classmethod
    def log_interaction(
        cls, 
        from_agent: str, 
        to_agent: Optional[str], 
        message: str,
        context_id: str = "",
        metadata: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Méthode de classe pour enregistrer une interaction
        
        Cette méthode est utilisée par les autres agents pour enregistrer
        leurs interactions sans avoir à instancier le LoggerAgent
        
        Args:
            from_agent: Agent source du message
            to_agent: Agent destinataire du message (optionnel)
            message: Contenu du message
            context_id: ID du contexte (campagne, conversation, etc.)
            metadata: Métadonnées supplémentaires
            
        Returns:
            Résultat de l'enregistrement
        """
        # Chemin de configuration par défaut
        config_path = os.path.join("agents", "logger", "config.json")
        
        # Tentative de récupération de l'instance unique
        if cls._instance is None:
            cls._instance = cls(config_path)
        
        # Création du log directement (évite la récursion infinie)
        timestamp = datetime.datetime.now().isoformat()
        log_id = str(uuid.uuid4())
        
        log_entry = {
            "id": log_id,
            "timestamp": timestamp,
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "context_id": context_id,
            "metadata": metadata
        }
        
        # Mise à jour des statistiques
        cls._instance.log_stats["total_logs"] += 1
        
        if from_agent and from_agent.lower().startswith("admin"):
            cls._instance.log_stats["admin_messages"] += 1
        else:
            cls._instance.log_stats["agent_messages"] += 1
        
        # Mise à jour des stats par campagne si applicable
        if context_id and context_id.startswith("campaign_"):
            if context_id not in cls._instance.log_stats["campaigns"]:
                cls._instance.log_stats["campaigns"][context_id] = 0
            cls._instance.log_stats["campaigns"][context_id] += 1
        
        # Ajout au cache
        cls._instance.messages_cache.append(log_entry)
        
        # Limitation de la taille du cache
        if len(cls._instance.messages_cache) > cls._instance.max_cache_size:
            cls._instance.messages_cache = cls._instance.messages_cache[-cls._instance.max_cache_size:]
        
        # Enregistrement en base de données
        if not cls._instance.test_mode:
            try:
                cls._instance._save_to_database(log_entry)
            except Exception as e:
                print(f"Erreur lors de l'enregistrement en base de données: {e}")
        
        # Enregistrement dans un fichier jsonl
        try:
            with open(cls._instance.jsonl_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Erreur lors de l'enregistrement dans le fichier jsonl: {e}")
        
        # Utilisation du nouveau système de logs
        try:
            # Log l'interaction via le nouveau système de logs
            level = "INFO"
            if metadata.get("level"):
                level = metadata.get("level")
                
            agent_message(from_agent, message, to_agent, level)
        except Exception as e:
            print(f"Erreur lors du logging via le nouveau système: {e}")
        
        return {
            "status": "success",
            "log_id": log_id,
            "timestamp": timestamp
        }
    
    def format_messages_as_chat(
        self, 
        messages: List[Dict[str, Any]],
        include_timestamp: bool = False,
        include_context: bool = False
    ) -> str:
        """
        Formate les messages sous forme de chat
        
        Args:
            messages: Liste des messages à formater
            include_timestamp: Inclure l'horodatage dans la sortie
            include_context: Inclure l'ID de contexte dans la sortie
            
        Returns:
            Messages formatés sous forme de chat
        """
        chat_lines = []
        
        for msg in messages:
            from_agent = msg.get("from", "Unknown")
            to_agent = msg.get("to", "all")
            message = msg.get("message", "")
            timestamp = msg.get("timestamp", "")
            context_id = msg.get("context_id", "")
            
            # Formatage du timestamp si demandé
            timestamp_str = ""
            if include_timestamp and timestamp:
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                    timestamp_str = f"[{dt.strftime('%Y-%m-%d %H:%M:%S')}] "
                except:
                    timestamp_str = f"[{timestamp}] "
            
            # Formatage du contexte si demandé
            context_str = ""
            if include_context and context_id:
                context_str = f"({context_id}) "
            
            # Formatage de la ligne
            if to_agent:
                line = f"{timestamp_str}{context_str}🧠 {from_agent} → {to_agent} :\n    {message}"
            else:
                line = f"{timestamp_str}{context_str}🧠 {from_agent} :\n    {message}"
            
            chat_lines.append(line)
        
        return "\n\n".join(chat_lines)
