"""
Utilitaires de gestion des conversations - Interface simple pour les agents
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.persistence_service import persistence_service


class ConversationHelper:
    """
    Helper pour faciliter l'accès à l'historique conversationnel dans les agents
    """
    
    @staticmethod
    def get_lead_conversation_history(lead_identifier: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de conversation d'un lead
        
        Args:
            lead_identifier: Email ou autre identifiant du lead
            limit: Nombre maximum de messages
            
        Returns:
            Liste des messages ordonnés chronologiquement (plus récent en premier)
        """
        return persistence_service.conversation_manager.get_conversation_history(
            lead_identifier, limit
        )
    
    @staticmethod
    def get_conversation_context(lead_identifier: str, days_back: int = 30) -> str:
        """
        Génère un contexte conversationnel formaté pour les agents
        
        Args:
            lead_identifier: Email ou autre identifiant du lead
            days_back: Nombre de jours d'historique à inclure
            
        Returns:
            Contexte formaté prêt pour l'IA
        """
        try:
            # Calcul de la date limite
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Récupération de l'historique
            messages = ConversationHelper.get_lead_conversation_history(lead_identifier, 50)
            
            if not messages:
                return f"Aucun historique de conversation trouvé pour {lead_identifier}."
            
            # Filtrage par date
            recent_messages = [
                msg for msg in messages 
                if msg.get('sent_date') and msg['sent_date'] >= cutoff_date
            ]
            
            if not recent_messages:
                return f"Aucune conversation récente (derniers {days_back} jours) pour {lead_identifier}."
            
            # Formatage du contexte
            context_parts = [
                f"=== HISTORIQUE DE CONVERSATION - {lead_identifier} ===",
                f"Période: {days_back} derniers jours",
                f"Nombre de messages: {len(recent_messages)}",
                ""
            ]
            
            for msg in reversed(recent_messages):  # Ordre chronologique
                sender = "LEAD" if msg.get('status') == 'received' else "NOUS"
                date = msg.get('sent_date', 'Date inconnue')
                content = msg.get('content', '').strip()
                subject = msg.get('subject', '')
                
                context_parts.append(f"[{date}] {sender}:")
                if subject and sender == "LEAD":
                    context_parts.append(f"Sujet: {subject}")
                context_parts.append(f"{content}")
                context_parts.append("")
            
            context_parts.append("=== FIN HISTORIQUE ===")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"Erreur lors de la récupération du contexte: {e}"
    
    @staticmethod
    def get_lead_profile(lead_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le profil complet d'un lead
        
        Args:
            lead_identifier: Email ou autre identifiant du lead
            
        Returns:
            Données du lead ou None
        """
        return persistence_service.conversation_manager._find_lead_by_identifier(lead_identifier)
    
    @staticmethod
    def get_enhanced_conversation_context(lead_identifier: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Génère un contexte conversationnel enrichi avec profil lead
        
        Args:
            lead_identifier: Email ou autre identifiant du lead
            days_back: Nombre de jours d'historique
            
        Returns:
            Contexte enrichi avec profil et historique
        """
        try:
            # Profil du lead
            lead_profile = ConversationHelper.get_lead_profile(lead_identifier)
            
            # Historique des messages
            conversation_history = ConversationHelper.get_conversation_context(lead_identifier, days_back)
            
            # Messages récents
            recent_messages = ConversationHelper.get_lead_conversation_history(lead_identifier, 10)
            
            # Analyse rapide
            total_messages = len(recent_messages) if recent_messages else 0
            last_message_date = None
            last_message_from_lead = None
            
            if recent_messages:
                last_message = recent_messages[0]  # Plus récent
                last_message_date = last_message.get('sent_date')
                last_message_from_lead = last_message.get('status') == 'received'
            
            return {
                'lead_profile': lead_profile,
                'conversation_text': conversation_history,
                'recent_messages': recent_messages,
                'stats': {
                    'total_messages': total_messages,
                    'last_message_date': last_message_date,
                    'last_message_from_lead': last_message_from_lead,
                    'days_searched': days_back
                },
                'formatted_for_ai': ConversationHelper._format_for_ai_context(
                    lead_profile, conversation_history, recent_messages
                )
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'lead_profile': None,
                'conversation_text': f"Erreur: {e}",
                'recent_messages': [],
                'stats': {},
                'formatted_for_ai': f"Erreur lors de la récupération du contexte: {e}"
            }
    
    @staticmethod
    def _format_for_ai_context(lead_profile: Optional[Dict], conversation_text: str, 
                              recent_messages: List[Dict]) -> str:
        """
        Formate le contexte pour l'utilisation par l'IA
        
        Args:
            lead_profile: Profil du lead
            conversation_text: Historique formaté
            recent_messages: Messages récents
            
        Returns:
            Contexte formaté pour l'IA
        """
        context_parts = []
        
        # Profil du lead
        if lead_profile:
            context_parts.append("=== PROFIL DU LEAD ===")
            
            name = f"{lead_profile.get('first_name', '')} {lead_profile.get('last_name', '')}".strip()
            if name:
                context_parts.append(f"Nom: {name}")
            
            if lead_profile.get('company'):
                context_parts.append(f"Entreprise: {lead_profile['company']}")
            
            if lead_profile.get('position'):
                context_parts.append(f"Poste: {lead_profile['position']}")
            
            if lead_profile.get('industry'):
                context_parts.append(f"Secteur: {lead_profile['industry']}")
            
            if lead_profile.get('website'):
                context_parts.append(f"Site web: {lead_profile['website']}")
            
            # Données d'analyse visuelle si disponibles
            if lead_profile.get('visual_score'):
                context_parts.append(f"Score maturité digitale: {lead_profile['visual_score']}/10")
            
            if lead_profile.get('website_maturity'):
                context_parts.append(f"Niveau maturité: {lead_profile['website_maturity']}")
            
            context_parts.append("")
        
        # Résumé de l'activité récente
        if recent_messages:
            last_msg = recent_messages[0]
            context_parts.append("=== ACTIVITÉ RÉCENTE ===")
            context_parts.append(f"Dernier message: {last_msg.get('sent_date', 'Date inconnue')}")
            
            from_lead = last_msg.get('status') == 'received'
            context_parts.append(f"Dernière interaction: {'Le lead nous a écrit' if from_lead else 'Nous avons écrit au lead'}")
            context_parts.append(f"Total messages dans l'historique: {len(recent_messages)}")
            context_parts.append("")
        
        # Historique complet
        context_parts.append(conversation_text)
        
        return "\n".join(context_parts)
    
    @staticmethod
    def search_conversations_by_keyword(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche dans les conversations par mot-clé
        
        Args:
            keyword: Mot-clé à rechercher
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des messages contenant le mot-clé
        """
        try:
            query = """
            SELECT m.*, l.first_name, l.last_name, l.company
            FROM messages m
            LEFT JOIN leads l ON m.lead_id = l.id
            WHERE LOWER(m.content) LIKE LOWER(:keyword)
            ORDER BY m.sent_date DESC
            LIMIT :limit
            """
            
            return persistence_service.db.fetch_all(query, {
                'keyword': f'%{keyword}%',
                'limit': limit
            })
            
        except Exception as e:
            return []


# Fonctions utilitaires pour les agents
def get_conversation_for_response(lead_email: str, include_lead_profile: bool = True) -> str:
    """
    Fonction simple pour récupérer le contexte conversationnel dans un agent de réponse
    
    Args:
        lead_email: Email du lead
        include_lead_profile: Inclure le profil du lead
        
    Returns:
        Contexte formaté prêt pour l'IA
    """
    if include_lead_profile:
        context = ConversationHelper.get_enhanced_conversation_context(lead_email)
        return context['formatted_for_ai']
    else:
        return ConversationHelper.get_conversation_context(lead_email)


def has_recent_conversation(lead_email: str, hours: int = 24) -> bool:
    """
    Vérifie s'il y a eu une conversation récente avec un lead
    
    Args:
        lead_email: Email du lead
        hours: Nombre d'heures à vérifier
        
    Returns:
        True s'il y a eu une conversation récente
    """
    try:
        messages = ConversationHelper.get_lead_conversation_history(lead_email, 5)
        if not messages:
            return False
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_messages = [
            msg for msg in messages
            if msg.get('sent_date') and msg['sent_date'] >= cutoff_time
        ]
        
        return len(recent_messages) > 0
        
    except Exception:
        return False


def get_last_message_from_lead(lead_email: str) -> Optional[Dict[str, Any]]:
    """
    Récupère le dernier message reçu d'un lead
    
    Args:
        lead_email: Email du lead
        
    Returns:
        Dernier message du lead ou None
    """
    try:
        messages = ConversationHelper.get_lead_conversation_history(lead_email, 20)
        
        # Recherche du dernier message reçu (status = 'received')
        for msg in messages:
            if msg.get('status') == 'received':
                return msg
        
        return None
        
    except Exception:
        return None


def save_outgoing_message(lead_email: str, content: str, subject: str = "", 
                         campaign_id: Optional[str] = None) -> bool:
    """
    Sauvegarde un message sortant dans l'historique
    
    Args:
        lead_email: Email du destinataire
        content: Contenu du message
        subject: Sujet du message
        campaign_id: ID de campagne (optionnel)
        
    Returns:
        True si sauvegardé avec succès
    """
    try:
        message_data = {
            'status': 'success',
            'source': 'email',
            'sender': 'berinia@system',  # Système BerinIA
            'content': content,
            'subject': subject,
            'received_at': datetime.utcnow().isoformat(),
            'lead_email': lead_email,
            'campaign_id': campaign_id
        }
        
        # Mapping pour message sortant
        from core.persistence_service import DataMapper
        mapped_data = DataMapper.map_message_data(message_data)
        mapped_data['status'] = 'sent'  # Override pour message sortant
        mapped_data['lead_email'] = lead_email
        
        # Sauvegarde
        message_id = persistence_service.conversation_manager.save_message_with_context(
            mapped_data, lead_email
        )
        
        return message_id is not None
        
    except Exception as e:
        logging.error(f"Erreur sauvegarde message sortant: {e}")
        return False
