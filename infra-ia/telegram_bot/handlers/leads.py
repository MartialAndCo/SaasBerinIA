"""Handler pour les leads du bot Telegram"""
import logging
from telegram.constants import ParseMode

from services.api_client import BeriniaAPIClient
from utils.keyboards import get_back_keyboard
from utils.formatters import format_leads_summary, format_leads_list, format_error, format_loading

logger = logging.getLogger(__name__)

class LeadsHandler:
    """Gestionnaire des leads"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    async def handle_callback(self, query, callback_data: str):
        """Gère les callbacks des leads"""
        logger.info(f"🔍 LeadsHandler reçoit callback: '{callback_data}'")
        try:
            if callback_data == "leads_count":
                await self._show_leads_count(query)
            elif callback_data == "leads_qualification":
                await self._show_qualification_rate(query)
            elif callback_data == "leads_list":
                await self._show_leads_list(query)
            elif callback_data == "leads_meetings":
                await self._show_meetings_menu(query)
            elif callback_data == "leads_search":
                await self._show_search_info(query)
            elif callback_data == "leads_status":
                await self._show_status_distribution(query)
            elif callback_data == "leads_compensation":
                await self._show_compensation_info(query)
            # Gestion des callbacks de meetings
            elif callback_data.startswith("meetings_"):
                await self._handle_meetings_callback(query, callback_data)
            # Gestion des callbacks de conversion
            elif callback_data.startswith("meeting_convert_"):
                meeting_id = int(callback_data.split("_")[-1])
                await self._show_meeting_conversion(query, meeting_id)
            elif callback_data.startswith("convert_"):
                parts = callback_data.split("_")
                logger.info(f"🔧 Parsing convert callback. Parts: {parts}")
                if len(parts) >= 3:
                    meeting_id = int(parts[1])
                    outcome_type = parts[2]
                    await self._handle_meeting_outcome(query, meeting_id, outcome_type)
                else:
                    logger.error(f"❌ Format de callback convert incorrect: {callback_data}")
                    await query.edit_message_text(
                        text=f"❌ Format de callback incorrect: {callback_data}",
                        reply_markup=get_back_keyboard("leads_main")
                    )
            elif callback_data.startswith("refuse_"):
                await self._handle_refusal(query, callback_data)
            elif callback_data.startswith("thinking_"):
                await self._handle_thinking(query, callback_data)
            elif callback_data.startswith("select_service_"):
                await self._handle_service_selection(query, callback_data)
            elif callback_data.startswith("conversion_stats_"):
                await self._show_conversion_stats(query, callback_data)
            elif "bundles" in callback_data:
                # Handle bundle-related callbacks (may be legacy)
                if "showbundles" in callback_data:
                    # Extract meeting ID from callback like "showbundles17"
                    import re
                    match = re.search(r'showbundles(\d+)', callback_data)
                    if match:
                        meeting_id = int(match.group(1))
                        await self._show_services_selection(query, meeting_id)
                    else:
                        await query.edit_message_text(
                            text="❌ Format de callback bundles incorrect",
                            reply_markup=get_back_keyboard("leads_main")
                        )
        except Exception as e:
            logger.error(f"Erreur dans LeadsHandler: {e}")
            await query.edit_message_text(
                text=format_error(str(e)),
                reply_markup=get_back_keyboard("leads_main"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_leads_count(self, query):
        """Affiche le nombre total de leads"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        count_data = self.api_client.get_leads_count()
        
        if count_data:
            text = f"""🔢 **Nombre total de leads**

📊 **Total général :** {count_data.get('total', 0)}
📈 **Cette semaine :** {count_data.get('this_week', 0)}
📅 **Ce mois :** {count_data.get('this_month', 0)}
📆 **Hier :** {count_data.get('yesterday', 0)}
"""
        else:
            text = "❌ Impossible de récupérer le nombre de leads"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("leads_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_qualification_rate(self, query):
        """Affiche le taux de qualification"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        stats = self.api_client.get_leads_stats()
        
        if stats:
            text = format_leads_summary(stats)
        else:
            text = "❌ Impossible de récupérer les statistiques de qualification"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("leads_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_leads_list(self, query):
        """Affiche la liste des leads"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        leads = self.api_client.get_leads(limit=10)
        
        if leads:
            text = format_leads_list(leads)
        else:
            text = "ℹ️ Aucun lead trouvé"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("leads_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_search_info(self, query):
        """Info sur la recherche de leads"""
        text = """🔍 **Recherche de leads**

Fonctionnalité de recherche en cours de développement.

Vous pourrez bientôt rechercher par :
• Nom ou email
• Entreprise
• Statut
• Score de qualification
• Date d'ajout

Contactez l'administrateur pour une recherche spécifique.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("leads_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_status_distribution(self, query):
        """Affiche la répartition par statut"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        stats = self.api_client.get_leads_stats()
        
        if stats:
            text = f"""📊 **Répartition des leads par statut**

✅ **Qualifiés :** {stats.get('qualified_count', 0)}
📧 **Contactés :** {stats.get('contacted_count', 0)}
💬 **Ont répondu :** {stats.get('responded_count', 0)}
⏳ **En attente :** {stats.get('pending_count', 0)}
❌ **Rejetés :** {stats.get('rejected_count', 0)}

📈 **Évolution :** {stats.get('trend', 'stable')}
"""
        else:
            text = "❌ Impossible de récupérer la répartition des statuts"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("leads_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_compensation_info(self, query):
        """Info sur la compensation des leads"""
        text = """🧮 **Compensation des leads**

Fonctionnalité de calcul de compensation en cours de développement.

Vous pourrez bientôt voir :
• Compensation par lead
• Estimation de revenus
• Historique des gains
• Projections

Contactez l'administrateur pour plus d'informations.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("leads_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # === MÉTHODES POUR GESTION DES RENDEZ-VOUS ===
    
    async def _show_meetings_menu(self, query):
        """Affiche le menu principal des rendez-vous"""
        from utils.keyboards import get_meetings_menu_keyboard
        
        await query.edit_message_text(
            text="📅 **Menu Rendez-vous**\n\nGestion et suivi de vos rendez-vous clients :",
            reply_markup=get_meetings_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_meetings_callback(self, query, callback_data: str):
        """Gère tous les callbacks liés aux meetings"""
        try:
            if callback_data == "meetings_stats":
                await self._show_meetings_stats(query)
            elif callback_data == "meetings_upcoming":
                await self._show_upcoming_meetings(query)
            elif callback_data == "meetings_all":
                await self._show_all_meetings(query)
            elif callback_data == "meetings_today":
                await self._show_meetings_by_period(query, "today")
            elif callback_data == "meetings_week":
                await self._show_meetings_by_period(query, "week")
            elif callback_data == "meetings_month":
                await self._show_meetings_by_period(query, "month")
            elif callback_data == "meetings_filter":
                await self._show_meetings_filter(query)
            elif callback_data.startswith("meetings_filter_"):
                status = callback_data.replace("meetings_filter_", "")
                await self._show_meetings_by_status(query, status)
            elif callback_data.startswith("meeting_details_"):
                meeting_id = int(callback_data.replace("meeting_details_", ""))
                await self._show_meeting_details(query, meeting_id)
            elif callback_data.startswith("meeting_conversation_"):
                meeting_id = int(callback_data.replace("meeting_conversation_", ""))
                await self._show_meeting_conversation(query, meeting_id)
            elif callback_data.startswith("meeting_reschedule_"):
                meeting_id = int(callback_data.replace("meeting_reschedule_", ""))
                await self._show_reschedule_options(query, meeting_id)
            elif callback_data.startswith("meeting_cancel_"):
                meeting_id = int(callback_data.replace("meeting_cancel_", ""))
                await self._confirm_meeting_action(query, meeting_id, "cancel")
            elif callback_data.startswith("meeting_complete_"):
                meeting_id = int(callback_data.replace("meeting_complete_", ""))
                await self._confirm_meeting_action(query, meeting_id, "complete")
            elif callback_data.startswith("meeting_no_show_"):
                meeting_id = int(callback_data.replace("meeting_no_show_", ""))
                await self._confirm_meeting_action(query, meeting_id, "no_show")
            elif callback_data.startswith("confirm_meeting_"):
                parts = callback_data.split("_")
                action = parts[2]
                meeting_id = int(parts[3])
                await self._execute_meeting_action(query, meeting_id, action)
            elif callback_data.startswith("reschedule_"):
                await self._handle_reschedule_action(query, callback_data)
            else:
                await query.edit_message_text(
                    text=f"❌ Action de meeting non reconnue: {callback_data}",
                    reply_markup=get_back_keyboard("leads_meetings"),
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Erreur dans _handle_meetings_callback: {e}")
            await query.edit_message_text(
                text=format_error(str(e)),
                reply_markup=get_back_keyboard("leads_meetings"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_meetings_stats(self, query):
        """Affiche les statistiques des rendez-vous"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        stats = self.api_client.get_meetings_stats()
        
        if stats:
            text = f"""📊 **Statistiques Rendez-vous**

📈 **Total général :** {stats.get('total_meetings', 0)}
📅 **Programmés :** {stats.get('scheduled_meetings', 0)}
✅ **Terminés :** {stats.get('completed_meetings', 0)}
❌ **Annulés :** {stats.get('cancelled_meetings', 0)}
👻 **Absence :** {stats.get('no_show_meetings', 0)}

🗓️ **Aujourd'hui :** {stats.get('upcoming_today', 0)}
📆 **Cette semaine :** {stats.get('upcoming_week', 0)}
"""
        else:
            text = "❌ Impossible de récupérer les statistiques des rendez-vous"
        
        from utils.keyboards import get_meetings_menu_keyboard
        await query.edit_message_text(
            text=text,
            reply_markup=get_meetings_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_upcoming_meetings(self, query):
        """Affiche les rendez-vous à venir"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.get_upcoming_meetings(days=7)
        
        if result and result.get('upcoming_meetings'):
            meetings = result['upcoming_meetings']
            text = f"📅 **Rendez-vous à venir (7 jours)**\n\n"
            
            for meeting in meetings[:10]:  # Limite à 10
                start_time = meeting.get('heure_debut', meeting.get('start_time', ''))
                client_name = meeting.get('nom_client', meeting.get('client_name', 'Client inconnu'))
                status = meeting.get('statut', meeting.get('status', 'inconnu'))
                
                # Formatage de la date
                try:
                    from datetime import datetime
                    if start_time:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%d/%m à %H:%M')
                    else:
                        formatted_time = 'Date inconnue'
                except:
                    formatted_time = str(start_time)[:16] if start_time else 'Date inconnue'
                
                status_emoji = {'scheduled': '📅', 'confirmed': '✅', 'cancelled': '❌'}.get(status, '❓')
                
                text += f"• {status_emoji} **{client_name}**\n"
                text += f"  🕐 {formatted_time}\n"
                
                # Afficher l'entreprise si disponible
                company = meeting.get('lead_company')
                if not company and meeting.get('description'):
                    # Extraire l'entreprise de la description si possible
                    desc = meeting.get('description', '')
                    if ' de ' in desc and ' - ' in desc:
                        # Format: "Title avec Name de Company - Secteur"
                        parts = desc.split(' de ')
                        if len(parts) > 1:
                            company_part = parts[1].split(' - ')[0].strip()
                            company = company_part
                
                if company:
                    text += f"  🏢 {company}\n"
                text += "\n"
            
        else:
            text = "ℹ️ Aucun rendez-vous programmé dans les 7 prochains jours"
        
        from utils.keyboards import get_meetings_menu_keyboard
        await query.edit_message_text(
            text=text,
            reply_markup=get_meetings_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_meetings_by_period(self, query, period: str):
        """Affiche les rendez-vous par période"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.get_meetings_by_period(period)
        
        period_titles = {
            'today': "Aujourd'hui",
            'week': "Cette semaine", 
            'month': "Ce mois"
        }
        
        if result and result.get('meetings'):
            meetings = result['meetings']
            count = result.get('count', 0)
            text = f"📅 **Rendez-vous {period_titles.get(period, period)}** ({count})\n\n"
            
            for meeting in meetings[:15]:  # Limite à 15
                text += self._format_meeting_summary(meeting)
            
            if len(meetings) > 15:
                text += f"\n... et {len(meetings) - 15} autres rendez-vous"
                
        else:
            text = f"ℹ️ Aucun rendez-vous {period_titles.get(period, period).lower()}"
        
        from utils.keyboards import get_meetings_menu_keyboard
        await query.edit_message_text(
            text=text,
            reply_markup=get_meetings_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_all_meetings(self, query, status: str = None, page: int = 0):
        """Affiche tous les rendez-vous avec pagination"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        limit = 10
        offset = page * limit
        
        result = self.api_client.get_meetings(
            status=status, 
            limit=limit, 
            offset=offset
        )
        
        if result and result.get('meetings'):
            meetings = result['meetings']
            total = result.get('total', 0)
            current_page = (offset // limit) + 1
            total_pages = (total + limit - 1) // limit
            
            status_text = f" ({status})" if status else ""
            text = f"📋 **Tous les rendez-vous{status_text}**\n"
            text += f"Page {current_page}/{total_pages} - Total: {total}\n\n"
            
            for meeting in meetings:
                text += self._format_meeting_summary(meeting, with_actions=True)
            
            from utils.keyboards import get_meetings_pagination_keyboard
            keyboard = get_meetings_pagination_keyboard(current_page, total_pages, status or "all")
            
        else:
            text = "ℹ️ Aucun rendez-vous trouvé"
            from utils.keyboards import get_meetings_menu_keyboard
            keyboard = get_meetings_menu_keyboard()
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_meetings_filter(self, query):
        """Affiche les options de filtrage"""
        from utils.keyboards import get_meetings_filter_keyboard
        
        await query.edit_message_text(
            text="🔍 **Filtrer les rendez-vous**\n\nChoisissez le statut à afficher :",
            reply_markup=get_meetings_filter_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_meetings_by_status(self, query, status: str):
        """Affiche les rendez-vous filtrés par statut"""
        await self._show_all_meetings(query, status)
    
    async def _show_meeting_details(self, query, meeting_id: int):
        """Affiche les détails d'un rendez-vous"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        meeting = self.api_client.get_meeting_details(meeting_id)
        
        if meeting:
            text = self._format_meeting_details(meeting)
            
            from utils.keyboards import get_meeting_details_keyboard
            calendar_event_id = meeting.get('calendar_event_id')
            keyboard = get_meeting_details_keyboard(meeting_id, calendar_event_id)
            
        else:
            text = "❌ Rendez-vous non trouvé"
            from utils.keyboards import get_meetings_menu_keyboard
            keyboard = get_meetings_menu_keyboard()
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_meeting_conversation(self, query, meeting_id: int):
        """Affiche le résumé de conversation pour un rendez-vous"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        meeting = self.api_client.get_meeting_details(meeting_id)
        
        if meeting and meeting.get('lead_id'):
            # Récupérer le résumé de conversation du lead
            conversation_data = self.api_client.get_lead_conversation_summary(meeting['lead_id'])
            
            client_name = meeting.get('nom_client', meeting.get('client_name', 'Inconnu'))
            company = meeting.get('lead_company', 'Non renseignée')
            
            if conversation_data and conversation_data.get('summary'):
                summary = conversation_data['summary']
                interest_level = summary.get('interest_level', 'unknown')
                key_points = summary.get('key_points', [])
                conversations_count = conversation_data.get('conversations_count', 0)
                
                # Emoji selon le niveau d'intérêt
                interest_emojis = {
                    'high': '🔥 Très intéressé',
                    'medium': '🟡 Intérêt modéré', 
                    'low': '🔵 Peu d\'intérêt',
                    'unknown': '❓ Intérêt inconnu'
                }
                interest_text = interest_emojis.get(interest_level, '❓ Intérêt inconnu')
                
                text = f"""💬 **Résumé de la conversation**

👤 **Client :** {client_name}
🏢 **Entreprise :** {company}
📊 **Niveau d'intérêt :** {interest_text}
💬 **Conversations :** {conversations_count}

📝 **Résumé des échanges :**
{summary.get('summary', 'Aucun résumé disponible')}

🔑 **Points clés :**"""
                
                for point in key_points[:5]:  # Limite à 5 points
                    text += f"\n• {point}"
                
                if not key_points:
                    text += "\n• Aucun point clé identifié"
                
                # Ajouter les actions recommandées si disponibles
                next_actions = summary.get('next_actions', [])
                if next_actions:
                    text += f"\n\n🎯 **Actions recommandées :**"
                    for action in next_actions[:3]:  # Limite à 3 actions
                        text += f"\n• {action}"
            else:
                text = f"""💬 **Résumé de la conversation**
                
👤 **Client :** {client_name}
🏢 **Entreprise :** {company}

📝 **Résumé des échanges :**
Aucune conversation enregistrée avec ce lead ou erreur lors de la récupération du résumé.

🔍 Consultez l'interface web pour plus de détails.
"""
        else:
            text = "❌ Impossible de récupérer le résumé de conversation"
        
        from utils.keyboards import get_meeting_details_keyboard
        keyboard = get_meeting_details_keyboard(meeting_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _confirm_meeting_action(self, query, meeting_id: int, action: str):
        """Affiche la confirmation pour une action sur un meeting"""
        action_texts = {
            'cancel': 'Êtes-vous sûr de vouloir **annuler** ce rendez-vous ?',
            'complete': 'Marquer ce rendez-vous comme **terminé** ?',
            'no_show': 'Marquer ce rendez-vous comme **absence** du client ?'
        }
        
        text = f"⚠️ **Confirmation**\n\n{action_texts.get(action, 'Confirmer cette action ?')}"
        
        from utils.keyboards import get_meeting_action_confirmation_keyboard
        keyboard = get_meeting_action_confirmation_keyboard(action, meeting_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _execute_meeting_action(self, query, meeting_id: int, action: str):
        """Execute une action sur un meeting"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        if action == "cancel":
            result = self.api_client.cancel_meeting(meeting_id, reason="Annulé via Telegram")
        elif action == "complete":
            result = self.api_client.update_meeting_status(meeting_id, "completed", notes="Marqué terminé via Telegram")
        elif action == "no_show":
            result = self.api_client.update_meeting_status(meeting_id, "no_show", notes="Absence client via Telegram")
        else:
            result = None
        
        if result and result.get('success', True):
            action_texts = {
                'cancel': 'annulé',
                'complete': 'marqué comme terminé', 
                'no_show': 'marqué comme absence'
            }
            text = f"✅ Rendez-vous {action_texts.get(action, 'modifié')} avec succès"
        else:
            text = f"❌ Erreur lors de l'action: {result.get('message', 'Erreur inconnue') if result else 'Pas de réponse'}"
        
        from utils.keyboards import get_meetings_menu_keyboard
        await query.edit_message_text(
            text=text,
            reply_markup=get_meetings_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _format_meeting_summary(self, meeting: dict, with_actions: bool = False) -> str:
        """Formate un résumé de meeting pour l'affichage"""
        client_name = meeting.get('nom_client', meeting.get('client_name', 'Client inconnu'))
        start_time = meeting.get('heure_debut', meeting.get('start_time', ''))
        status = meeting.get('statut', meeting.get('status', 'inconnu'))
        company = meeting.get('lead_company', '')
        
        # Formatage de la date
        try:
            from datetime import datetime
            if start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%d/%m à %H:%M')
            else:
                formatted_time = 'Date inconnue'
        except:
            formatted_time = str(start_time)[:16] if start_time else 'Date inconnue'
        
        status_emojis = {
            'scheduled': '📅',
            'confirmed': '✅', 
            'completed': '🏁',
            'cancelled': '❌',
            'no_show': '👻'
        }
        status_emoji = status_emojis.get(status, '❓')
        
        # Si pas d'entreprise, essayer de l'extraire de la description
        if not company and meeting.get('description'):
            desc = meeting.get('description', '')
            if ' de ' in desc and ' - ' in desc:
                parts = desc.split(' de ')
                if len(parts) > 1:
                    company = parts[1].split(' - ')[0].strip()
        
        text = f"• {status_emoji} **{client_name}**\n"
        text += f"  🕐 {formatted_time}\n"
        if company:
            text += f"  🏢 {company}\n"
        
        if with_actions and meeting.get('id'):
            text += f"  📝 /meeting_{meeting['id']}\n"
        
        text += "\n"
        return text
    
    def _format_meeting_details(self, meeting: dict) -> str:
        """Formate les détails complets d'un meeting"""
        client_name = meeting.get('nom_client', meeting.get('client_name', 'Client inconnu'))
        client_email = meeting.get('email_client', meeting.get('client_email', ''))
        start_time = meeting.get('heure_debut', meeting.get('start_time', ''))
        end_time = meeting.get('heure_fin', meeting.get('end_time', ''))
        duration = meeting.get('duree', meeting.get('duration_minutes', 0))
        status = meeting.get('statut', meeting.get('status', 'inconnu'))
        description = meeting.get('description', '')
        meeting_link = meeting.get('lien_meeting', meeting.get('meeting_link', ''))
        
        # Informations du lead
        lead_company = meeting.get('lead_company', '')
        lead_phone = meeting.get('lead_phone', '')
        
        # Si pas d'entreprise, essayer de l'extraire de la description
        if not lead_company and description:
            if ' de ' in description and ' - ' in description:
                parts = description.split(' de ')
                if len(parts) > 1:
                    lead_company = parts[1].split(' - ')[0].strip()
        
        # Formatage des dates
        try:
            from datetime import datetime
            if start_time:
                dt_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                formatted_start = dt_start.strftime('%d/%m/%Y à %H:%M')
            else:
                formatted_start = 'Date inconnue'
                
            if end_time:
                dt_end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                formatted_end = dt_end.strftime('%H:%M')
            else:
                formatted_end = 'Heure inconnue'
        except:
            formatted_start = str(start_time)[:16] if start_time else 'Date inconnue'
            formatted_end = str(end_time)[:16] if end_time else 'Heure inconnue'
        
        status_emojis = {
            'scheduled': '📅 Programmé',
            'confirmed': '✅ Confirmé',
            'completed': '🏁 Terminé',
            'cancelled': '❌ Annulé',
            'no_show': '👻 Absence'
        }
        status_text = status_emojis.get(status, f'❓ {status}')
        
        text = f"""📅 **Détails du Rendez-vous**

👤 **Client :** {client_name}
📧 **Email :** {client_email}
🏢 **Entreprise :** {lead_company or 'Non renseignée'}
📞 **Téléphone :** {lead_phone or 'Non renseigné'}

🕐 **Horaires :**
📅 Début : {formatted_start}
🕐 Fin : {formatted_end}
⏱️ Durée : {duration} minutes

📋 **Statut :** {status_text}
"""
        
        if description:
            text += f"\n📝 **Description :**\n{description}"
        
        if meeting_link:
            text += f"\n\n🔗 **Lien de réunion :**\n{meeting_link}"
        
        # Ajouter des informations contextuelles sur le rendez-vous
        text += f"\n\n📋 **Informations complémentaires :**"
        
        # Extraire le type de rendez-vous de la description
        meeting_type = "Rendez-vous"
        if description:
            if "Présentation" in description:
                meeting_type = "Présentation commerciale"
            elif "Demo" in description:
                meeting_type = "Démonstration produit"
            elif "Call" in description:
                meeting_type = "Appel de découverte"
            elif "Réunion technique" in description:
                meeting_type = "Réunion technique"
            elif "Suivi" in description:
                meeting_type = "Suivi commercial"
            elif "Négociation" in description:
                meeting_type = "Négociation"
            elif "Kick-off" in description:
                meeting_type = "Lancement de projet"
            elif "Formation" in description:
                meeting_type = "Formation"
        
        text += f"\n🎯 **Type :** {meeting_type}"
        
        # Ajouter des conseils selon le statut
        if status == 'scheduled':
            text += f"\n\n💡 **Conseils pour le rendez-vous :**"
            text += f"\n• Préparer les documents de présentation"
            text += f"\n• Vérifier le lien de réunion avant le début"
            text += f"\n• Prévoir 5 minutes d'avance"
        elif status == 'completed':
            text += f"\n\n✅ **Rendez-vous terminé**"
            text += f"\n• N'oubliez pas de faire le suivi commercial"
            text += f"\n• Documentez les points clés discutés"
        elif status == 'no_show':
            text += f"\n\n👻 **Absence du client**"
            text += f"\n• Programmer un appel de suivi"
            text += f"\n• Proposer un nouveau créneau"
        elif status == 'cancelled':
            text += f"\n\n❌ **Rendez-vous annulé**"
            text += f"\n• Recontacter pour reprogrammer"
        
        # Ajouter un bouton pour voir les échanges si disponible
        if meeting.get('lead_id'):
            text += f"\n\n💬 Tapez /conversation_{meeting.get('lead_id')} pour voir l'historique des échanges"
        
        return text
    
    async def _show_meeting_conversion(self, query, meeting_id: int):
        """Affiche l'interface de conversion d'un rendez-vous"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        # Vérifier si le meeting a déjà un outcome
        outcome = self.api_client.get_meeting_outcome(meeting_id)
        
        if outcome:
            # Le meeting a déjà un résultat
            outcome_data = outcome.get('meeting_outcome', {})
            outcome_type = outcome_data.get('outcome_type', 'unknown')
            
            outcome_texts = {
                'accepted': '✅ Client converti',
                'refused': '❌ Client refusé',
                'thinking': '🤔 En réflexion',
                'no_show': '👻 Absence client'
            }
            
            text = f"📋 **Résultat du rendez-vous**\n\n"
            text += f"**Statut :** {outcome_texts.get(outcome_type, outcome_type)}\n"
            
            if outcome_type == 'refused' and outcome_data.get('refusal_reason'):
                refusal_texts = {
                    'price_too_high': 'Prix trop élevé',
                    'no_budget': 'Pas de budget',
                    'internal_solution': 'Préfère une solution interne',
                    'bad_timing': 'Mauvais timing',
                    'not_convinced': 'Pas convaincu',
                    'competitor': 'Concurrent choisi',
                    'other': 'Autre raison'
                }
                text += f"**Raison :** {refusal_texts.get(outcome_data['refusal_reason'], outcome_data['refusal_reason'])}\n"
                
                if outcome_data.get('refusal_details'):
                    text += f"**Détails :** {outcome_data['refusal_details']}\n"
            
            elif outcome_type == 'thinking' and outcome_data.get('follow_up_date'):
                text += f"**Rappel prévu :** {outcome_data['follow_up_date']}\n"
            
            elif outcome_type == 'accepted' and outcome.get('sale'):
                sale = outcome['sale']
                text += f"**CA généré :** {sale['total_setup_price']}€ + {sale['total_monthly_price']}€/mois\n"
                text += f"**Valeur annuelle :** {outcome.get('total_annual_value', 0)}€\n"
            
            if outcome_data.get('notes'):
                text += f"\n**Notes :** {outcome_data['notes']}"
            
            from utils.keyboards import get_back_keyboard
            keyboard = get_back_keyboard(f"meeting_details_{meeting_id}")
            
        else:
            # Afficher l'interface de conversion
            meeting = self.api_client.get_meeting_details(meeting_id)
            client_name = meeting.get('client_name', 'Client') if meeting else 'Client'
            
            text = f"✅ **Rendez-vous terminé avec {client_name}**\n\n"
            text += "Le client a-t-il accepté de devenir client ?\n\n"
            text += "Choisissez le résultat du rendez-vous :"
            
            from utils.keyboards import get_meeting_conversion_keyboard
            keyboard = get_meeting_conversion_keyboard(meeting_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_meeting_outcome(self, query, meeting_id: int, outcome_type: str):
        """Gère la sélection du résultat d'un rendez-vous"""
        
        if outcome_type == "accepted":
            await self._show_services_selection(query, meeting_id)
        elif outcome_type == "refused":
            await self._show_refusal_reasons(query, meeting_id)
        elif outcome_type == "thinking":
            await self._show_thinking_options(query, meeting_id)
        elif outcome_type == "no_show":
            # Enregistrer directement l'absence
            result = self.api_client.convert_meeting(
                meeting_id=meeting_id,
                outcome_type="no_show",
                notes="Client absent au rendez-vous"
            )
            
            if result:
                text = f"👻 **Absence client enregistrée**\n\nLe rendez-vous a été marqué comme 'absence client'."
            else:
                text = "❌ Erreur lors de l'enregistrement"
            
            from utils.keyboards import get_back_keyboard
            await query.edit_message_text(
                text=text,
                reply_markup=get_back_keyboard("leads_meetings"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_services_selection(self, query, meeting_id: int):
        """Affiche la sélection des services pour un client accepté"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        services = self.api_client.get_services()
        
        if not services:
            text = "❌ Impossible de récupérer la liste des services"
            from utils.keyboards import get_back_keyboard
            keyboard = get_back_keyboard(f"meeting_convert_{meeting_id}")
        else:
            text = f"💰 **Services disponibles**\n\n"
            text += "Quels services le client a-t-il choisis ?\n\n"
            
            for service in services:
                setup = service['setup_price']
                monthly = service['monthly_price']
                text += f"**{service['name']}**\n"
                text += f"• {setup}€ + {monthly}€/mois\n"
                if service.get('description'):
                    text += f"• {service['description']}\n"
                text += "\n"
            
            from utils.keyboards import get_services_selection_keyboard
            keyboard = get_services_selection_keyboard(meeting_id, services)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_refusal_reasons(self, query, meeting_id: int):
        """Affiche les raisons de refus"""
        text = f"❌ **Client refusé**\n\n"
        text += "Quelle est la raison du refus ?"
        
        from utils.keyboards import get_refusal_reasons_keyboard
        keyboard = get_refusal_reasons_keyboard(meeting_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_thinking_options(self, query, meeting_id: int):
        """Affiche les options pour 'en réflexion'"""
        text = f"🤔 **Client en réflexion**\n\n"
        text += "Quand faut-il le recontacter ?"
        
        from utils.keyboards import get_thinking_options_keyboard
        keyboard = get_thinking_options_keyboard(meeting_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_refusal(self, query, callback_data: str):
        """Gère la sélection d'une raison de refus"""
        parts = callback_data.split("_")  # refuse_MEETING_ID_REASON
        meeting_id = int(parts[1])
        reason = parts[2]
        
        # Vérifier si le meeting a déjà un outcome
        existing_outcome = self.api_client.get_meeting_outcome(meeting_id)
        if existing_outcome and existing_outcome.get("meeting_outcome"):
            outcome = existing_outcome["meeting_outcome"]
            existing_reason = outcome.get("refusal_reason", "Non spécifiée")
            text = f"ℹ️ **Conversion déjà enregistrée**\n\n"
            text += f"**Statut actuel :** {outcome['outcome_type']}\n"
            if outcome['outcome_type'] == 'refused':
                reason_texts = {
                    'price_too_high': 'Prix trop élevé',
                    'no_budget': 'Pas de budget',
                    'internal_solution': 'Préfère une solution interne',
                    'bad_timing': 'Mauvais timing',
                    'not_convinced': 'Pas convaincu',
                    'competitor': 'Concurrent choisi'
                }
                text += f"**Raison :** {reason_texts.get(existing_reason, existing_reason)}"
            
            from utils.keyboards import get_back_keyboard
            keyboard = get_back_keyboard("leads_meetings")
        
        # Si c'est "other", demander des détails
        elif reason == "other":
            text = "📝 **Autre raison de refus**\n\nVeuillez préciser la raison du refus en écrivant votre message."
            from utils.keyboards import get_back_keyboard
            keyboard = get_back_keyboard(f"refuse_{meeting_id}")
        else:
            # Enregistrer le refus
            result = self.api_client.convert_meeting(
                meeting_id=meeting_id,
                outcome_type="refused",
                refusal_reason=reason
            )
            
            if result:
                reason_texts = {
                    'price_too_high': 'Prix trop élevé',
                    'no_budget': 'Pas de budget',
                    'internal_solution': 'Préfère une solution interne',
                    'bad_timing': 'Mauvais timing',
                    'not_convinced': 'Pas convaincu',
                    'competitor': 'Concurrent choisi'
                }
                
                text = f"❌ **Refus enregistré**\n\n**Raison :** {reason_texts.get(reason, reason)}\n\nCette information sera utilisée pour améliorer notre approche commerciale."
            else:
                text = "❌ Erreur lors de l'enregistrement du refus"
            
            from utils.keyboards import get_back_keyboard
            keyboard = get_back_keyboard("leads_meetings")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_thinking(self, query, callback_data: str):
        """Gère les options 'en réflexion'"""
        parts = callback_data.split("_")  # thinking_MEETING_ID_DAYS
        meeting_id = int(parts[1])
        
        if parts[2] == "custom":
            text = "📅 **Date personnalisée**\n\nFonctionnalité en cours de développement.\nUtilisez les options prédéfinies pour le moment."
            from utils.keyboards import get_thinking_options_keyboard
            keyboard = get_thinking_options_keyboard(meeting_id)
        else:
            days = int(parts[2])
            from datetime import date, timedelta
            follow_up_date = date.today() + timedelta(days=days)
            
            # Enregistrer en réflexion
            result = self.api_client.convert_meeting(
                meeting_id=meeting_id,
                outcome_type="thinking",
                follow_up_date=follow_up_date.isoformat(),
                notes=f"Rappel prévu dans {days} jours"
            )
            
            if result:
                date_text = follow_up_date.strftime("%d/%m/%Y")
                text = f"🤔 **En réflexion enregistré**\n\n**Rappel prévu :** {date_text}\n\nUn suivi sera programmé automatiquement."
            else:
                text = "❌ Erreur lors de l'enregistrement"
            
            from utils.keyboards import get_back_keyboard
            keyboard = get_back_keyboard("leads_meetings")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_service_selection(self, query, callback_data: str):
        """Gère la sélection de services"""
        # TODO: Implémenter la logique de sélection multiple de services
        # Pour l'instant, redirection simple
        parts = callback_data.split("_")  # select_service_MEETING_ID_SERVICE_ID
        meeting_id = int(parts[2])
        service_id = int(parts[3])
        
        text = "💰 **Sélection de services**\n\nFonctionnalité en cours de développement.\nLe service sera enregistré directement."
        
        # Pour l'instant, on enregistre un service simple
        services = self.api_client.get_services()
        selected_service = next((s for s in services if s['id'] == service_id), None)
        
        if selected_service:
            # Simuler l'achat d'un service
            result = self.api_client.convert_meeting(
                meeting_id=meeting_id,
                outcome_type="accepted",
                services=[{
                    'service_id': service_id,
                    'setup_price': selected_service['setup_price'],
                    'monthly_price': selected_service['monthly_price']
                }]
            )
            
            if result:
                setup = selected_service['setup_price']
                monthly = selected_service['monthly_price']
                annual = setup + (monthly * 12)
                
                text = f"✅ **Vente enregistrée !**\n\n"
                text += f"**Service :** {selected_service['name']}\n"
                text += f"**Prix :** {setup}€ + {monthly}€/mois\n"
                text += f"**Valeur annuelle :** {annual}€\n\n"
                text += "🎉 Félicitations pour cette conversion !"
            else:
                text = "❌ Erreur lors de l'enregistrement de la vente"
        
        from utils.keyboards import get_back_keyboard
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("leads_meetings"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_conversion_stats(self, query, callback_data: str):
        """Affiche les statistiques de conversion"""
        stat_type = callback_data.replace("conversion_stats_", "")
        
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        if stat_type == "main":
            from utils.keyboards import get_conversion_stats_keyboard
            text = "📊 **Statistiques de conversion**\n\nChoisissez le type de statistiques à consulter :"
            keyboard = get_conversion_stats_keyboard()
            
        elif stat_type == "rates":
            stats = self.api_client.get_conversion_stats()
            if stats:
                text = "📊 **Taux de conversion par mois**\n\n"
                for stat in stats[:6]:  # 6 derniers mois
                    month = stat['month'][:7]  # YYYY-MM
                    rate = stat.get('conversion_rate', 0)
                    total = stat.get('total_meetings', 0)
                    conversions = stat.get('conversions', 0)
                    text += f"**{month} :** {rate:.1f}% ({conversions}/{total})\n"
            else:
                text = "❌ Aucune donnée de conversion disponible"
            
            from utils.keyboards import get_conversion_stats_keyboard
            keyboard = get_conversion_stats_keyboard()
            
        elif stat_type == "refusals":
            stats = self.api_client.get_refusal_stats()
            if stats:
                text = "❌ **Raisons de refus**\n\n"
                refusal_texts = {
                    'price_too_high': '💰 Prix trop élevé',
                    'no_budget': '💸 Pas de budget',
                    'internal_solution': '🏠 Solution interne',
                    'bad_timing': '⏰ Mauvais timing',
                    'not_convinced': '🤷 Pas convaincu',
                    'competitor': '🏆 Concurrent choisi',
                    'other': '📝 Autre raison'
                }
                
                for stat in stats:
                    reason = stat['refusal_reason']
                    count = stat['count']
                    percentage = stat.get('percentage', 0)
                    reason_text = refusal_texts.get(reason, reason)
                    text += f"{reason_text}: {count} ({percentage:.1f}%)\n"
            else:
                text = "❌ Aucune donnée de refus disponible"
            
            from utils.keyboards import get_conversion_stats_keyboard
            keyboard = get_conversion_stats_keyboard()
            
        elif stat_type == "revenue":
            stats = self.api_client.get_revenue_stats()
            if stats:
                text = "💰 **Revenus générés**\n\n"
                for stat in stats[:6]:  # 6 derniers mois
                    month = stat['month'][:7]  # YYYY-MM
                    setup = stat.get('total_setup_revenue', 0)
                    monthly = stat.get('monthly_recurring_revenue', 0)
                    sales = stat.get('sales_count', 0)
                    text += f"**{month} :** {setup}€ + {monthly}€/mois ({sales} ventes)\n"
            else:
                text = "❌ Aucune donnée de revenus disponible"
            
            from utils.keyboards import get_conversion_stats_keyboard
            keyboard = get_conversion_stats_keyboard()
        
        else:
            text = "❌ Type de statistique non reconnu"
            from utils.keyboards import get_back_keyboard
            keyboard = get_back_keyboard("stats_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
