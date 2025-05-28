"""
Service Central de Persistance Amélioré - Gestion intelligente des niches et campaigns
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


class EnhancedDataMapper:
    """Mapper intelligent avec gestion automatique des niches et campaigns"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.logger = logging.getLogger("BerinIA-EnhancedMapper")
    
    def map_lead_data(self, agent_data: Dict[str, Any], input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Mappe les données de lead avec gestion intelligente des niches et campaigns
        
        Args:
            agent_data: Données brutes du lead depuis l'agent
            input_data: Données d'entrée de l'agent (pour contexte niche/campagne)
            
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
            'company_website': 'website',
            'website': 'website',
            'industry': 'industry',  # ✅ Garde industry pour le métier
            'source': 'source',
            'country': 'country',
            'address': 'address',
            'description': 'notes',
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
        
        # 🎯 GESTION INTELLIGENTE DES NICHES
        niche_id = self._handle_niche_assignment(agent_data, input_data)
        if niche_id:
            mapped_data['niche_id'] = niche_id
        
        # 🎯 GESTION INTELLIGENTE DES CAMPAIGNS  
        campaign_id = self._handle_campaign_assignment(agent_data, input_data, niche_id)
        if campaign_id:
            mapped_data['campaign_id'] = campaign_id
        
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
        mapped_keys = set(field_mapping.keys()) | set(visual_fields.keys()) | {'scrape_date', 'status', 'score', 'validation_status', 'niche', 'campaign'}
        for key, value in agent_data.items():
            if key not in mapped_keys and value is not None:
                unmapped_data[key] = value
        
        if unmapped_data:
            score_details['raw_agent_data'] = unmapped_data
        
        if score_details:
            mapped_data['score_details'] = score_details
        
        return mapped_data
    
    def _handle_niche_assignment(self, agent_data: Dict[str, Any], input_data: Dict[str, Any] = None) -> Optional[int]:
        """
        Gère l'assignation intelligente des niches
        
        Logique: niche = industry + lieu
        Ex: "coiffeur" + "Toulouse" = "coiffeur Toulouse"
        
        Args:
            agent_data: Données du lead
            input_data: Données d'entrée de l'agent
            
        Returns:
            ID de la niche ou None
        """
        try:
            # Extraction de l'industry (métier)
            industry = agent_data.get('industry') or agent_data.get('niche', '')
            if not industry:
                self.logger.warning("Aucune industry trouvée pour créer la niche")
                return None
            
            # Extraction du lieu (plusieurs sources possibles)
            location = None
            
            # 1. Depuis input_data (paramètres du scraper)
            if input_data:
                location = (input_data.get('city') or 
                           input_data.get('location') or 
                           input_data.get('parameters', {}).get('city') or
                           input_data.get('parameters', {}).get('location'))
            
            # 2. Depuis agent_data
            if not location:
                location = (agent_data.get('city') or 
                           agent_data.get('location') or 
                           agent_data.get('country', ''))
            
            # Construction du nom de niche
            if location:
                niche_name = f"{industry} {location}".strip()
            else:
                niche_name = industry
                self.logger.warning(f"Pas de lieu trouvé, niche = industry seule: {niche_name}")
            
            # Recherche de la niche existante
            existing_niche = self.db.fetch_one(
                "SELECT id FROM niches WHERE name = :name",
                {"name": niche_name}
            )
            
            if existing_niche:
                self.logger.info(f"Niche existante trouvée: {niche_name} (ID: {existing_niche['id']})")
                return existing_niche['id']
            
            # Création de la nouvelle niche
            niche_data = {
                'name': niche_name,
                'description': f"Niche {industry} dans {location}" if location else f"Niche {industry}",
                'keywords': f"{industry},{location}" if location else industry,
                'status': 'active',
                'exploration_depth': 1,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            niche_id = self.db.insert('niches', niche_data)
            self.logger.info(f"Nouvelle niche créée: {niche_name} (ID: {niche_id})")
            
            return niche_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'assignation de niche: {e}")
            return None
    
    def _handle_campaign_assignment(self, agent_data: Dict[str, Any], input_data: Dict[str, Any] = None, 
                                  niche_id: Optional[int] = None) -> Optional[int]:
        """
        Gère l'assignation intelligente des campaigns
        
        Logique: campaign = niche + date ou contexte
        Ex: "coiffeur Toulouse" + "27mai" = "coiffeur Toulouse 27mai"
        
        Args:
            agent_data: Données du lead
            input_data: Données d'entrée de l'agent  
            niche_id: ID de la niche associée
            
        Returns:
            ID de la campaign ou None
        """
        try:
            # Vérifier si campaign_id existe dans la table
            try:
                self.db.fetch_one("SELECT campaign_id FROM leads LIMIT 1")
            except:
                self.logger.warning("Colonne campaign_id n'existe pas dans la table leads")
                return None
            
            # Construction du nom de campaign
            campaign_name = None
            
            # 1. Depuis input_data si fourni explicitement
            if input_data and input_data.get('campaign'):
                campaign_name = input_data['campaign']
            
            # 2. Construction automatique basée sur la niche + date
            elif niche_id:
                # Récupérer le nom de la niche
                niche_result = self.db.fetch_one(
                    "SELECT name FROM niches WHERE id = :id",
                    {"id": niche_id}
                )
                
                if niche_result:
                    niche_name = niche_result['name']
                    # Ajouter la date du jour
                    date_suffix = datetime.now().strftime("%d%b").lower()
                    campaign_name = f"{niche_name} {date_suffix}"
            
            if not campaign_name:
                self.logger.warning("Impossible de construire le nom de campaign")
                return None
            
            # Recherche de la campaign existante
            existing_campaign = self.db.fetch_one(
                "SELECT id FROM campaigns WHERE name = :name",
                {"name": campaign_name}
            )
            
            if existing_campaign:
                self.logger.info(f"Campaign existante trouvée: {campaign_name} (ID: {existing_campaign['id']})")
                return existing_campaign['id']
            
            # Création de la nouvelle campaign
            campaign_data = {
                'name': campaign_name,
                'description': f"Campaign automatique pour {campaign_name}",
                'status': 'active',
                'target_leads': 0,
                'agent': 'ScraperAgent',
                'niche_id': niche_id,
                'created_at': datetime.utcnow()
            }
            
            campaign_id = self.db.insert('campaigns', campaign_data)
            self.logger.info(f"Nouvelle campaign créée: {campaign_name} (ID: {campaign_id})")
            
            return campaign_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'assignation de campaign: {e}")
            return None
    
    def map_message_data(self, agent_data: Dict[str, Any], lead_id: Optional[int] = None) -> Dict[str, Any]:
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


class EnhancedPersistenceService:
    """Service Central de Persistance Amélioré"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.enhanced_mapper = EnhancedDataMapper(self.db)
        self.logger = logging.getLogger("BerinIA-EnhancedPersistence")
        
        # Statistiques du service
        self.stats = {
            'leads_saved': 0,
            'messages_saved': 0,
            'niches_created': 0,
            'campaigns_created': 0,
            'errors': 0,
            'last_activity': None
        }
    
    def persist_agent_data(self, agent_name: str, action: str, input_data: Dict[str, Any], 
                          result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal avec gestion améliorée des niches/campaigns
        
        Args:
            agent_name: Nom de l'agent source
            action: Action effectuée
            input_data: Données d'entrée de l'agent (IMPORTANT pour contexte)
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
                persistence_result = self._persist_leads_enhanced(result_data, agent_name, input_data)
            
            elif data_type == 'message':
                persistence_result = self._persist_message(result_data, agent_name)
            
            elif data_type == 'conversation':
                persistence_result = self._persist_conversation(result_data, agent_name)
            
            # Sauvegarde dans la mémoire vectorielle si pertinent
            if data_type in ['message', 'conversation', 'leads']:
                self._persist_to_vector_memory_fixed(result_data, data_type, agent_name)
            
            # Enrichissement du résultat original
            enriched_result = result_data.copy()
            enriched_result['persistence'] = persistence_result
            
            return enriched_result
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Erreur dans persist_agent_data: {e}")
            
            # Retour du résultat original en cas d'erreur
            return result_data
    
    def _persist_leads_enhanced(self, data: Dict[str, Any], agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persiste une liste de leads avec gestion améliorée des niches/campaigns
        
        Args:
            data: Données contenant les leads
            agent_name: Nom de l'agent source
            input_data: Données d'entrée de l'agent
            
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
                    # Mapping des données avec contexte input_data
                    mapped_data = self.enhanced_mapper.map_lead_data(lead_data, input_data)
                    
                    # Vérification des doublons
                    if self._is_duplicate_lead(mapped_data):
                        duplicates.append(mapped_data.get('email', 'unknown'))
                        continue
                    
                    # Sauvegarde
                    lead_id = self.db.insert('leads', mapped_data)
                    saved_ids.append(lead_id)
                    
                    # Log détaillé
                    niche_id = mapped_data.get('niche_id')
                    campaign_id = mapped_data.get('campaign_id')
                    self.logger.info(f"Lead sauvegardé: ID={lead_id}, Niche_ID={niche_id}, Campaign_ID={campaign_id}")
                    
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
            self.logger.error(f"Erreur _persist_leads_enhanced: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _persist_to_vector_memory_fixed(self, data: Dict[str, Any], data_type: str, agent_name: str) -> None:
        """
        Sauvegarde dans la mémoire vectorielle (Qdrant) avec IDs corrigés
        
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
            
            # Métadonnées
            metadata = {
                'agent_source': agent_name,
                'data_type': data_type,
                'timestamp': datetime.utcnow().isoformat(),
                'content_preview': content[:200]
            }
            
            # Ajout à la collection appropriée avec UUID correct
            collection_name = f"{data_type}_memory"
            add_to_collection(
                collection_name=collection_name,
                text=content,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Erreur vectorisation: {e}")
    
    def _detect_data_type(self, agent_name: str, action: str, data: Dict[str, Any]) -> str:
        """Détecte automatiquement le type de données à persister"""
        if 'scraper' in agent_name.lower() or 'scraping' in action.lower():
            if 'leads' in data and isinstance(data['leads'], list):
                return 'leads'
        
        if 'response_listener' in agent_name.lower() or 'listener' in agent_name.lower():
            if 'source' in data and data['source'] in ['email', 'sms', 'whatsapp']:
                return 'message'
        
        if 'messaging' in agent_name.lower() or 'message' in action.lower():
            return 'conversation'
        
        if 'leads' in data and isinstance(data['leads'], list):
            return 'leads'
        
        if 'content' in data and 'sender' in data:
            return 'message'
        
        if 'messages' in data and isinstance(data['messages'], list):
            return 'conversation'
        
        return 'unknown'
    
    def _persist_message(self, data: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Persiste un message"""
        try:
            mapped_data = self.enhanced_mapper.map_message_data(data)
            
            lead_identifier = data.get('sender', '')
            # Note: ConversationManager doit être adapté aussi
            # Pour l'instant, utilisation simple
            message_id = self.db.insert('messages', mapped_data)
            
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
        """Persiste une conversation complète"""
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
    
    def _prepare_content_for_embedding(self, data: Dict[str, Any], data_type: str) -> str:
        """Prépare le contenu pour la vectorisation"""
        if data_type == 'message':
            content = data.get('content', '')
            sender = data.get('sender', '')
            return f"Message de {sender}: {content}"
        
        elif data_type == 'leads':
            leads = data.get('leads', [])
            if leads:
                lead = leads[0]
                company = lead.get('company', '')
                industry = lead.get('industry', '')
                return f"Lead: {company} dans {industry}"
        
        return ''
    
    def _is_duplicate_lead(self, mapped_data: Dict[str, Any]) -> bool:
        """Vérifie si un lead existe déjà"""
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


# Instance singleton du service amélioré
enhanced_persistence_service = EnhancedPersistenceService()
