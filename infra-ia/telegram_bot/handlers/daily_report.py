"""
Handler pour le rapport quotidien Telegram
"""
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

# Import des fonctions de rapport
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE, chat_id: int = None):
    """
    Envoie le rapport quotidien automatiquement ou sur demande
    
    Args:
        context: Contexte Telegram
        chat_id: ID du chat (si None, envoi à tous les admins)
    """
    try:
        # Import ici pour éviter les erreurs circulaires
        from core.db import generate_daily_report
        
        # Génération du rapport
        report_data = generate_daily_report()
        
        if 'error' in report_data:
            error_message = f"❌ **Erreur génération rapport**\n\n`{report_data['error']}`"
            
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=error_message, 
                    parse_mode=ParseMode.MARKDOWN
                )
            return False
        
        # Formatage du rapport
        formatted_report = _format_daily_report(report_data)
        
        # Ajout des boutons d'action
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Détails campagnes", callback_data="daily_detail_campaigns"),
                InlineKeyboardButton("🚨 Voir alertes", callback_data="daily_detail_alerts")
            ],
            [
                InlineKeyboardButton("💡 Recommandations", callback_data="daily_detail_recommendations"),
                InlineKeyboardButton("🔄 Actualiser", callback_data="daily_refresh")
            ]
        ])
        
        # Envoi du rapport
        if chat_id:
            # Envoi à un chat spécifique
            await context.bot.send_message(
                chat_id=chat_id,
                text=formatted_report,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            # Envoi à tous les admins
            from config.settings import TELEGRAM_ADMIN_IDS
            
            for admin_id in TELEGRAM_ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=formatted_report,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    print(f"Erreur envoi rapport à {admin_id}: {e}")
        
        return True
        
    except Exception as e:
        error_msg = f"❌ **Erreur système rapport quotidien**\n\n`{str(e)}`"
        
        if chat_id:
            await context.bot.send_message(
                chat_id=chat_id,
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
        
        return False


def _format_daily_report(report_data: dict) -> str:
    """
    Formate le rapport quotidien pour Telegram
    
    Args:
        report_data: Données du rapport
        
    Returns:
        Rapport formaté en Markdown
    """
    report_date = datetime.now().strftime("%d/%m/%Y")
    
    # En-tête
    message = f"📊 **Rapport BerinIA - {report_date}**\n\n"
    
    # Résumé global
    summary = report_data.get('summary', 'Aucune activité')
    message += f"📋 **Résumé:** {summary}\n\n"
    
    # Métriques globales d'hier
    global_metrics = report_data.get('global_metrics', {})
    if global_metrics:
        sent_yesterday = global_metrics.get('total_sent_yesterday', 0)
        delivered_yesterday = global_metrics.get('delivered_yesterday', 0)
        opened_yesterday = global_metrics.get('opened_yesterday', 0)
        replied_yesterday = global_metrics.get('replied_yesterday', 0)
        
        message += f"📈 **Hier ({(datetime.now()).strftime('%d/%m')}):**\n"
        message += f"• Messages envoyés: {sent_yesterday}\n"
        message += f"• Livrés: {delivered_yesterday}\n"
        message += f"• Ouverts: {opened_yesterday}\n"
        message += f"• Réponses: {replied_yesterday}\n\n"
    
    # Campagnes actives
    campaigns = report_data.get('campaign_reports', [])
    if campaigns:
        message += f"🎯 **Campagnes actives ({len(campaigns)}):**\n"
        
        for campaign in campaigns:
            name = campaign.get('name', 'Inconnue')
            phase = campaign.get('phase', 'unknown')
            days_active = campaign.get('days_active', 0)
            should_wait = campaign.get('should_wait', True)
            sent_yesterday = campaign.get('sent_yesterday', 0)
            performance = campaign.get('performance_summary', {})
            
            # Emoji selon la phase
            phase_emoji = {
                'lancement': '🚀',
                'rodage': '⚙️',
                'mature': '✅'
            }.get(phase, '❓')
            
            # Emoji selon performance
            status = performance.get('status', 'unknown')
            status_emoji = {
                'good': '🟢',
                'average': '🟡',
                'concerning': '🔴',
                'no_activity': '⚪'
            }.get(status, '❓')
            
            message += f"{phase_emoji} **{name}**\n"
            message += f"   └ Phase: {phase} ({days_active}j) {status_emoji}\n"
            
            if sent_yesterday > 0:
                message += f"   └ Hier: {sent_yesterday} messages\n"
            
            if should_wait:
                message += f"   └ ⏳ *Trop récent pour décisions*\n"
            elif performance.get('message'):
                message += f"   └ {performance['message']}\n"
            
            message += "\n"
    
    # Alertes
    alerts = report_data.get('alerts', [])
    if alerts:
        message += f"🚨 **Alertes ({len(alerts)}):**\n"
        for alert in alerts:
            campaign = alert.get('campaign', 'Inconnue')
            issue = alert.get('issue', 'Problème non spécifié')
            message += f"• **{campaign}**: {issue}\n"
        message += "\n"
    
    # Recommandations du jour
    recommendations = report_data.get('daily_recommendations', [])
    if recommendations:
        message += f"💡 **Recommandations ({len(recommendations)}):**\n"
        for rec in recommendations[:3]:  # Max 3 pour pas surcharger
            campaign = rec.get('campaign', 'Global')
            action = rec.get('action', 'Action non spécifiée')
            priority = rec.get('priority', 'medium')
            
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(priority, '🔵')
            
            message += f"{priority_emoji} **{campaign}**: {action}\n"
        message += "\n"
    
    # Pied de page
    timestamp = datetime.now().strftime("%H:%M")
    message += f"🕐 *Généré à {timestamp}*"
    
    return message


async def cmd_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /rapport pour générer le rapport quotidien sur demande
    """
    chat_id = update.effective_chat.id
    
    # Vérification que c'est un admin
    from config.settings import TELEGRAM_ADMIN_IDS
    if chat_id not in TELEGRAM_ADMIN_IDS:
        await update.message.reply_text("❌ Accès non autorisé.")
        return
    
    # Message de chargement
    loading_msg = await update.message.reply_text("📊 Génération du rapport quotidien...")
    
    # Génération et envoi du rapport
    success = await send_daily_report(context, chat_id)
    
    # Supprimer le message de chargement
    await loading_msg.delete()
    
    if not success:
        await update.message.reply_text("❌ Erreur lors de la génération du rapport.")


async def callback_daily_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gère les callbacks des boutons du rapport quotidien
    """
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    callback_data = query.data
    
    try:
        from core.db import generate_daily_report
        report_data = generate_daily_report()
        
        if callback_data == "daily_detail_campaigns":
            # Détail des campagnes
            campaigns = report_data.get('campaign_reports', [])
            if campaigns:
                detail_msg = "📊 **Détail des campagnes:**\n\n"
                
                for campaign in campaigns:
                    name = campaign.get('name', 'Inconnue')
                    phase = campaign.get('phase', 'unknown')
                    days_active = campaign.get('days_active', 0)
                    performance = campaign.get('performance_summary', {})
                    
                    detail_msg += f"🎯 **{name}**\n"
                    detail_msg += f"• Phase: {phase} ({days_active} jours)\n"
                    detail_msg += f"• Status: {performance.get('message', 'N/A')}\n"
                    detail_msg += f"• Messages hier: {campaign.get('sent_yesterday', 0)}\n\n"
            else:
                detail_msg = "Aucune campagne active."
                
        elif callback_data == "daily_detail_alerts":
            # Détail des alertes
            alerts = report_data.get('alerts', [])
            if alerts:
                detail_msg = "🚨 **Alertes détaillées:**\n\n"
                
                for alert in alerts:
                    campaign = alert.get('campaign', 'Inconnue')
                    issue = alert.get('issue', 'Problème non spécifié')
                    detail_msg += f"⚠️ **{campaign}**\n"
                    detail_msg += f"• Problème: {issue}\n"
                    detail_msg += f"• Action: Attention requise\n\n"
            else:
                detail_msg = "✅ Aucune alerte aujourd'hui."
                
        elif callback_data == "daily_detail_recommendations":
            # Détail des recommandations
            recommendations = report_data.get('daily_recommendations', [])
            if recommendations:
                detail_msg = "💡 **Recommandations détaillées:**\n\n"
                
                for rec in recommendations:
                    campaign = rec.get('campaign', 'Global')
                    action = rec.get('action', 'Action non spécifiée')
                    reason = rec.get('reason', 'Raison non spécifiée')
                    priority = rec.get('priority', 'medium')
                    
                    detail_msg += f"💡 **{campaign}**\n"
                    detail_msg += f"• Action: {action}\n"
                    detail_msg += f"• Raison: {reason}\n"
                    detail_msg += f"• Priorité: {priority}\n\n"
            else:
                detail_msg = "✅ Aucune recommandation aujourd'hui."
                
        elif callback_data == "daily_refresh":
            # Actualiser le rapport
            await query.edit_message_text("🔄 Actualisation du rapport...")
            await send_daily_report(context, chat_id)
            return
        
        else:
            detail_msg = "❌ Action non reconnue."
        
        # Envoyer le détail
        await query.edit_message_text(
            text=detail_msg,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Erreur: {str(e)}")


def get_daily_report_handlers():
    """
    Retourne les handlers pour le rapport quotidien
    
    Returns:
        Liste des handlers Telegram
    """
    return [
        CommandHandler("rapport", cmd_daily_report),
        CommandHandler("daily", cmd_daily_report),
        CallbackQueryHandler(callback_daily_detail, pattern="^daily_")
    ]
