"""
Service Central de Persistance - Sauvegarde automatique et intelligente des données des agents
"""
import os
import json
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from core.db import DatabaseService, get_db
from utils.qdrant import create_embedding, add_to_collection


class DataMapper:
    """Mapper intelligent entre les structures d'agents et les modèles de base de données"""
    
    @staticmethod
    def map_lead_data(agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mappe les données de lead des agents vers le modèle Lead de la base de données
        
        Args:
            agent_data: Données brutes du lead depuis l'agent
            
        Returns:
            Données mappées pour la table leads
        """
        mapped_data = {}
        
        # Mapping des champs standards
        field_mapping = {
            # Agent field -> DB field
            'first_name': 'first_name',
            'last_name': 'last_name', 
            'email': 'email',
            'phone': 'phone',
            'company': 'company',
            'position': 'position',
            'linkedin_url': 'linkedin_url',
            'company_website': 'website',  # Mapping spécial
            'website': 'website',
            'industry': 'industry',
            'source': 'source',
            'niche': 'industry',  # Backup mapping
            'country': 'country',
            'address': 'address',
            'description': 'notes',  # Mapping vers notes
        }
        
        # Application du mapping basique
        for agent_field, db_field in field_mapping.items():
            if agent_field in agent_data and agent_data[agent_field]:
                mapped_data[db_field] = agent_data[agent_field]
        
        # Traitement des champs spéciaux
        
        # Entreprise (plusieurs sources possibles)
        if not mapped_data.get('company'):
            mapped_data['company'] = agent_data.get('entreprise', '')
        
        # Score et validation
        if 'score' in agent_data:
            mapped_data['score'] = agent_data['score']
        
        if 'validation_status' in agent_data:
            mapped_data['validation_status'] = agent_data['validation_status']
        else:
            mapped_data['validation_status'] = 'unvalidated'
        
        # Status par défaut
        mapped_data['status'] = agent_data.get('status', 'new')
        
        # Données d'analyse visuelle
        visual_fields = {
            'visual_score': 'visual_score',
            'visual_analysis_data': 'visual_analysis_data',
            'has_popup': 'has_popup',
            'popup_removed': 'popup_removed',
            'screenshot_path': 'screenshot_path',
            'enhanced_screenshot_path': 'enhanced_screenshot_path',
            'visual_analysis_date': 'visual_analysis_date',
            'site_type': 'site_type',
            'visual_quality': 'visual_quality',
            'website_maturity': 'website_maturity',
            'design_strengths': 'design_strengths',
            'design_weaknesses': 'design_weaknesses'
        }
        
        for agent_field, db_field in visual_fields.items():
            if agent_field in agent_data and agent_data[agent_field] is not None:
                mapped_data[db_field] = agent_data[agent_field]
        
        # Gestion des timestamps
        if 'scrape_date' in agent_data:
            try:
                if isinstance(agent_data['scrape_date'], str):
                    mapped_data['created_at'] = datetime.fromisoformat(agent_data['scrape_date'].replace('Z', '+00:00'))
                else:
                    mapped_data['created_at'] = agent_data['scrape_date']
            except:
                mapped_data['created_at'] = datetime.utcnow()
        else:
            mapped_data['created_at'] = datetime.utcnow()
        
        mapped_data['updated_at'] = datetime.utcnow()
        
        # Stockage des données complètes en JSONB pour préservation
        score_details = {}
        if 'lead_id' in agent_data:
            score_details['original_lead_id'] = agent_data['lead_id']
        if 'rating' in agent_data:
            score_details['rating'] = agent_data['rating']
        if 'company_size' in agent_data:
            score_details['company_size'] = agent_data['company_size']
        
        # Ajout de toutes les données non mappées dans score_details
        unmapped_data = {}
        mapped_keys = set(field_mapping.keys()) | set(visual_fields.keys()) | {'scrape_date', 'status', 'score', 'validation_status'}
        for key, value in agent_data.items():
            if key not in mapped_keys and value is not None:
                unmapped_data[key] = value
        
        if unmapped_data:
            score_details['raw_agent_data'] = unmapped_data
        
        if score_details:
            mapped_data['score_details'] = score_details
        
        return mapped_data
    
    @staticmethod
    def map_message_data(agent_data: Dict[str, Any], lead_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Mappe les données de message des agents vers le modèle Message
        
        Args:
            agent_data: Données brutes du message depuis l'agent
            lead_id: ID du lead associé (si connu)
            
        Returns:
            Données mappées pour la table messages
        """
        mapped_data = {}
        
        # Mapping des champs standards
        field_mapping = {
            'sender': 'lead_email',
            'content': 'content',
            'subject': 'subject',
            'campaign_id': 'campaign_id',
            'status': 'status'
        }
        
        for agent_field, db_field in field_mapping.items():
            if agent_field in agent_data and agent_data[agent_field]:
                mapped_data[db_field] = agent_data[agent_field]
        
        # Lead information
        if lead_id:
            mapped_data['lead_id'] = lead_id
        
        # Extraction du nom depuis l'email si pas fourni
        if 'sender' in agent_data and not mapped_data.get('lead_name'):
            email = agent_data['sender']
            if '@' in email:
                local_part = email.split('@')[0]
                mapped_data['lead_name'] = local_part.replace('.', ' ').replace('_', ' ').title()
            else:
                mapped_data['lead_name'] = email
        
        # Gestion des timestamps
        if 'received_at' in agent_data:
            try:
                if isinstance(agent_data['received_at'], str):
                    mapped_data['sent_date'] = datetime.fromisoformat(agent_data['received_at'].replace('Z', '+00:00'))
                else:
                    mapped_data['sent_date'] = agent_data['received_at']
            except:
                mapped_data['sent_date'] = datetime.utcnow()
        else:
            mapped_data['sent_date'] = datetime.utcnow()
        
        # Status par défaut
        if not mapped_data.get('status'):
            mapped_data['status'] = 'received'
        
        return mapped_data


class ConversationManager:
    """Gestionnaire de conversations avec historique ordonné"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def save_message_with_context(self, message_data: Dict[str, Any], lead_identifier: str) -> Optional[int]:
        """
        Sauvegarde un message avec son contexte conversationnel
        
        Args:
            message_data: Données du message mappées
            lead_identifier: Email ou autre identifiant du lead
            
        Returns:
            ID du message sauvegardé ou None en cas d'erreur
        """
        try:
            # Recherche du lead existant
            lead = self._find_lead_by_identifier(lead_identifier)
            
            if lead:
                message_data['lead_id'] = lead['id']
                message_data['lead_name'] = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
                if not message_data['lead_name']:
                    message_data['lead_name'] = lead.get('email', lead_identifier)
            
            # Sauvegarde du message
            message_id = self.db.insert('messages', message_data)
            
            # Mise à jour de la date de dernier contact du lead
            if lead:
                self.db.update('leads', lead['id'], {
                    'last_contact': message_data['sent_date'],
                    'updated_at': datetime.utcnow()
                })
            
            return message_id
            
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde du message: {e}")
            return None
    
    def _find_lead_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Trouve un lead par email ou LinkedIn
        
        Args:
            identifier: Email ou URL LinkedIn
            
        Returns:
            Données du lead ou None
        """
        try:
            # Recherche par email d'abord
            query = "SELECT * FROM leads WHERE email = :identifier LIMIT 1"
            result = self.db.fetch_one(query, {"identifier": identifier})
            
            if result:
                return result
            
            # Recherche par LinkedIn si c'est une URL
            if 'linkedin.com' in identifier.lower():
                query = "SELECT * FROM leads WHERE linkedin_url = :identifier LIMIT 1"
                result = self.db.fetch_one(query, {"identifier": identifier})
                
            return result
            
        except Exception as e:
            logging.error(f"Erreur lors de la recherche du lead: {e}")
            return None
    
    def get_conversation_history(self, lead_identifier: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de conversation d'un lead
        
        Args:
            lead_identifier: Email ou identifiant du lead
            limit: Nombre maximum de messages
            
        Returns:
            Liste des messages ordonnés par date
        """
        try:
            query = """
            SELECT m.*, l.first_name, l.last_name, l.company
            FROM messages m
            LEFT JOIN leads l ON m.lead_id = l.id
            WHERE m.lead_email = :identifier OR l.email = :identifier
            ORDER BY m.sent_date DESC
            LIMIT :limit
            """
            
            return self.db.fetch_all(query, {
                "identifier": lead_identifier,
                "limit": limit
            })
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []


class PersistenceService:
    """Service Central de Persistance - Coeur du système de sauvegarde automatique"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.conversation_manager = ConversationManager(self.db)
        self.logger = logging.getLogger("BerinIA-Persistence")
        
        # Statistiques du service
        self.stats = {
            'leads_saved': 0,
            'messages_saved': 0,
            'errors': 0,
            'last_activity': None
        }
    
    def persist_agent_data(self, agent_name: str, action: str, input_data: Dict[str, Any], 
                          result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal - Persiste automatiquement les données selon leur type
        
        Args:
            agent_name: Nom de l'agent source
            action: Action effectuée
            input_data: Données d'entrée de l'agent
            result_data: Données de sortie de l'agent
            
        Returns:
            Résultat enrichi avec les IDs de sauvegarde
        """
        self.stats['last_activity'] = datetime.utcnow().isoformat()
        
        try:
            # Détection automatique du type de données
            data_type = self._detect_data_type(agent_name, action, result_data)
            
            persistence_result = {}
            
            if data_type == 'leads':
                persistence_result = self._persist_leads(result_data, agent_name)
            
            elif data_type == 'message':
                persistence_result = self._persist_message(result_data, agent_name)
            
            elif data_type == 'conversation':
                persistence_result = self._persist_conversation(result_data, agent_name)
            
            # Sauvegarde dans la mémoire vectorielle si pertinent
            if data_type in ['message', 'conversation', 'leads']:
                self._persist_to_vector_memory(result_data, data_type, agent_name)
            
            # Enrichissement du résultat original
            enriched_result = result_data.copy()
            enriched_result['persistence'] = persistence_result
            
            return enriched_result
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Erreur dans persist_agent_data: {e}")
            
            # Retour du résultat original en cas d'erreur
            return result_data
    
    def _detect_data_type(self, agent_name: str, action: str, data: Dict[str, Any]) -> str:
        """
        Détecte automatiquement le type de données à persister
        
        Args:
            agent_name: Nom de l'agent
            action: Action effectuée  
            data: Données à analyser
            
        Returns:
            Type de données détecté
        """
        # Détection basée sur l'agent et l'action
        if 'scraper' in agent_name.lower() or 'scraping' in action.lower():
            if 'leads' in data and isinstance(data['leads'], list):
                return 'leads'
        
        if 'response_listener' in agent_name.lower() or 'listener' in agent_name.lower():
            if 'source' in data and data['source'] in ['email', 'sms', 'whatsapp']:
                return 'message'
        
        if 'messaging' in agent_name.lower() or 'message' in action.lower():
            return 'conversation'
        
        # Détection basée sur la structure des données
        if 'leads' in data and isinstance(data['leads'], list):
            return 'leads'
        
        if 'content' in data and 'sender' in data:
            return 'message'
        
        if 'messages' in data and isinstance(data['messages'], list):
            return 'conversation'
        
        return 'unknown'
    
    def _persist_leads(self, data: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """
        Persiste une liste de leads
        
        Args:
            data: Données contenant les leads
            agent_name: Nom de l'agent source
            
        Returns:
            Résultat de la persistance
        """
        try:
            leads = data.get('leads', [])
            if not leads:
                return {'status': 'no_data', 'count': 0}
            
            saved_ids = []
            duplicates = []
            errors = []
            
            for lead_data in leads:
                try:
                    # Mapping des données
                    mapped_data = DataMapper.map_lead_data(lead_data)
                    
                    # Vérification des doublons
                    if self._is_duplicate_lead(mapped_data):
                        duplicates.append(mapped_data.get('email', 'unknown'))
                        continue
                    
                    # Sauvegarde
                    lead_id = self.db.insert('leads', mapped_data)
                    saved_ids.append(lead_id)
                    
                except Exception as e:
                    errors.append(str(e))
                    self.logger.error(f"Erreur sauvegarde lead: {e}")
            
            self.stats['leads_saved'] += len(saved_ids)
            
            return {
                'status': 'success',
                'count': len(saved_ids),
                'saved_ids': saved_ids,
                'duplicates': len(duplicates),
                'errors': len(errors),
                'agent_source': agent_name
            }
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Erreur _persist_leads: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _persist_message(self, data: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """
        Persiste un message avec son contexte conversationnel
        
        Args:
            data: Données du message
            agent_name: Nom de l'agent source
            
        Returns:
            Résultat de la persistance
        """
        try:
            # Mapping des données
            mapped_data = DataMapper.map_message_data(data)
            
            # Sauvegarde avec contexte conversationnel
            lead_identifier = data.get('sender', '')
            message_id = self.conversation_manager.save_message_with_context(
                mapped_data, lead_identifier
            )
            
            if message_id:
                self.stats['messages_saved'] += 1
                return {
                    'status': 'success',
                    'message_id': message_id,
                    'agent_source': agent_name
                }
            else:
                return {'status': 'error', 'message': 'Failed to save message'}
                
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Erreur _persist_message: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _persist_conversation(self, data: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """
        Persiste une conversation complète
        
        Args:
            data: Données de la conversation
            agent_name: Nom de l'agent source
            
        Returns:
            Résultat de la persistance
        """
        try:
            messages = data.get('messages', [])
            if not messages:
                return {'status': 'no_data', 'count': 0}
            
            saved_ids = []
            errors = []
            
            for message_data in messages:
                try:
                    result = self._persist_message(message_data, agent_name)
                    if result['status'] == 'success':
                        saved_ids.append(result['message_id'])
                    else:
                        errors.append(result.get('message', 'Unknown error'))
                except Exception as e:
                    errors.append(str(e))
            
            return {
                'status': 'success',
                'count': len(saved_ids),
                'saved_ids': saved_ids,
                'errors': len(errors),
                'agent_source': agent_name
            }
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Erreur _persist_conversation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _persist_to_vector_memory(self, data: Dict[str, Any], data_type: str, agent_name: str) -> None:
        """
        Sauvegarde dans la mémoire vectorielle (Qdrant)
        
        Args:
            data: Données à vectoriser
            data_type: Type de données
            agent_name: Nom de l'agent source
        """
        try:
            # Préparation du contenu pour l'embedding
            content = self._prepare_content_for_embedding(data, data_type)
            
            if not content:
                return
            
            # Création de l'embedding
            embedding = create_embedding(content)
            
            # Métadonnées
            metadata = {
                'agent_source': agent_name,
                'data_type': data_type,
                'timestamp': datetime.utcnow().isoformat(),
                'content_preview': content[:200]
            }
            
            # Ajout à la collection appropriée
            collection_name = f"{data_type}_memory"
            add_to_collection(
                collection_name=collection_name,
                vector=embedding,
                payload=metadata,
                point_id=str(uuid.uuid4())
            )
            
        except Exception as e:
            self.logger.error(f"Erreur vectorisation: {e}")
    
    def _prepare_content_for_embedding(self, data: Dict[str, Any], data_type: str) -> str:
        """
        Prépare le contenu pour la vectorisation
        
        Args:
            data: Données source
            data_type: Type de données
            
        Returns:
            Contenu texte pour l'embedding
        """
        if data_type == 'message':
            content = data.get('content', '')
            sender = data.get('sender', '')
            return f"Message de {sender}: {content}"
        
        elif data_type == 'leads':
            leads = data.get('leads', [])
            if leads:
                lead = leads[0]  # Premier lead pour l'exemple
                company = lead.get('company', '')
                industry = lead.get('industry', '')
                return f"Lead: {company} dans {industry}"
        
        return ''
    
    def _is_duplicate_lead(self, mapped_data: Dict[str, Any]) -> bool:
        """
        Vérifie si un lead existe déjà
        
        Args:
            mapped_data: Données mappées du lead
            
        Returns:
            True si duplicata
        """
        try:
            email = mapped_data.get('email')
            linkedin = mapped_data.get('linkedin_url')
            
            if email:
                query = "SELECT id FROM leads WHERE email = :email LIMIT 1"
                result = self.db.fetch_one(query, {'email': email})
                if result:
                    return True
            
            if linkedin:
                query = "SELECT id FROM leads WHERE linkedin_url = :linkedin LIMIT 1"
                result = self.db.fetch_one(query, {'linkedin': linkedin})
                if result:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service"""
        return self.stats.copy()


# Instance singleton du service
persistence_service = PersistenceService()
