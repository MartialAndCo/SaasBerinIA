"""
Module pour la gestion de la connexion à la base de données PostgreSQL
"""
import os
import datetime
from typing import Any, Dict, List, Optional, Union
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis le fichier .env spécifique
load_dotenv("/root/berinia/infra-ia/.env")

# Configuration de la connexion à la base de données
DB_USER = os.getenv("DB_USER", "berinia_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "berinia_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "berinia")

# Création de l'URL de connexion
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Création de la base pour les modèles SQLAlchemy
Base = declarative_base()

# Création de l'engine SQLAlchemy
engine = sa.create_engine(DATABASE_URL)

# Création du sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Fonction utilitaire pour obtenir une session de base de données
    
    Returns:
        Une session SQLAlchemy
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

class DatabaseService:
    """Service pour les interactions avec la base de données PostgreSQL"""
    
    @staticmethod
    def execute_query(query: str, params: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None) -> List[Dict[str, Any]]:
        """
        Exécute une requête SQL et retourne les résultats
        
        Args:
            query: La requête SQL à exécuter
            params: Les paramètres de la requête (dict ou liste de dicts)
            
        Returns:
            Liste des résultats (liste de dictionnaires)
        """
        with engine.connect() as connection:
            # Convertir la requête en TextClause
            sql = sa.text(query)
            
            # Exécuter la requête avec les paramètres
            if params is None:
                result = connection.execute(sql)
            else:
                result = connection.execute(sql, params)
                
            # Convertir les résultats en liste de dictionnaires
            return [dict(row._mapping) for row in result]
    
    @staticmethod
    def fetch_one(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Exécute une requête SQL et retourne le premier résultat

        Args:
            query: La requête SQL à exécuter
            params: Les paramètres de la requête

        Returns:
            Le premier résultat ou None
        """
        results = DatabaseService.execute_query(query, params)
        return results[0] if results else None
        
    @staticmethod
    def fetch_all(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Exécute une requête SQL et retourne tous les résultats
        
        Args:
            query: La requête SQL à exécuter
            params: Les paramètres de la requête
            
        Returns:
            Liste des résultats (liste de dictionnaires)
        """
        return DatabaseService.execute_query(query, params)
    
    @staticmethod
    def insert(table: str, data: Dict[str, Any]) -> int:
        """
        Insère des données dans une table
        
        Args:
            table: Le nom de la table
            data: Les données à insérer
            
        Returns:
            L'ID de la ligne insérée
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{key}" for key in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        
        with engine.connect() as connection:
            sql = sa.text(query)
            result = connection.execute(sql, data)
            connection.commit()
            return result.scalar_one()
    
    @staticmethod
    def update(table: str, id_: int, data: Dict[str, Any]) -> bool:
        """
        Met à jour des données dans une table
        
        Args:
            table: Le nom de la table
            id_: L'ID de la ligne à mettre à jour
            data: Les données à mettre à jour
            
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = :id"
        
        with engine.connect() as connection:
            params = {**data, "id": id_}
            sql = sa.text(query)
            result = connection.execute(sql, params)
            connection.commit()
            return result.rowcount > 0
    
    @staticmethod
    def delete(table: str, id_: int) -> bool:
        """
        Supprime une ligne d'une table
        
        Args:
            table: Le nom de la table
            id_: L'ID de la ligne à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        query = f"DELETE FROM {table} WHERE id = :id"
        
        with engine.connect() as connection:
            sql = sa.text(query)
            result = connection.execute(sql, {"id": id_})
            connection.commit()
            return result.rowcount > 0

# Fonctions utilitaires pour l'accès à la base de données
def query_db(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour exécuter une requête SQL
    
    Args:
        query: La requête SQL
        params: Les paramètres
        
    Returns:
        Liste des résultats
    """
    return DatabaseService.execute_query(query, params)

def get_one(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Fonction utilitaire pour récupérer un seul résultat
    
    Args:
        query: La requête SQL
        params: Les paramètres
        
    Returns:
        Le résultat ou None
    """
    return DatabaseService.fetch_one(query, params)


# Fonctions spécialisées pour le PivotStrategyAgent
def get_global_metrics() -> Dict[str, Any]:
    """
    Récupère les métriques globales du système
    
    Returns:
        Dictionnaire contenant les métriques globales
    """
    try:
        # Récupération du nombre total de campagnes
        campaigns_query = """
        SELECT 
            COUNT(*) as total_campaigns,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_campaigns,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_campaigns,
            COUNT(CASE WHEN status = 'paused' THEN 1 END) as paused_campaigns
        FROM campaigns
        """
        campaigns_data = DatabaseService.fetch_one(campaigns_query) or {}
        
        # Récupération du nombre total de leads
        leads_query = """
        SELECT 
            COUNT(*) as total_leads,
            COUNT(CASE WHEN status = 'qualified' THEN 1 END) as qualified_leads,
            COUNT(CASE WHEN status = 'contacted' THEN 1 END) as contacted_leads,
            COUNT(CASE WHEN status = 'responded' THEN 1 END) as responded_leads
        FROM leads
        """
        leads_data = DatabaseService.fetch_one(leads_query) or {}
        
        # Récupération des métriques des messages
        messages_query = """
        SELECT 
            COUNT(*) as total_messages,
            COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent_messages,
            COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_messages,
            COUNT(CASE WHEN status = 'opened' THEN 1 END) as opened_messages,
            COUNT(CASE WHEN status = 'replied' THEN 1 END) as replied_messages,
            COUNT(CASE WHEN status = 'bounced' THEN 1 END) as bounced_messages
        FROM messages
        """
        messages_data = DatabaseService.fetch_one(messages_query) or {}
        
        # Calcul des taux globaux
        total_sent = messages_data.get('sent_messages', 0)
        total_delivered = messages_data.get('delivered_messages', 0)
        
        global_metrics = {
            # Données de base
            **campaigns_data,
            **leads_data,
            **messages_data,
            
            # Taux calculés
            'overall_delivery_rate': total_delivered / max(total_sent, 1),
            'overall_open_rate': messages_data.get('opened_messages', 0) / max(total_delivered, 1),
            'overall_response_rate': messages_data.get('replied_messages', 0) / max(total_delivered, 1),
            'overall_bounce_rate': messages_data.get('bounced_messages', 0) / max(total_sent, 1),
            
            # Métriques timestamp
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return global_metrics
        
    except Exception as e:
        # Retourner des métriques par défaut en cas d'erreur
        return {
            'total_campaigns': 0,
            'active_campaigns': 0,
            'total_leads': 0,
            'total_messages': 0,
            'overall_delivery_rate': 0,
            'overall_open_rate': 0,
            'overall_response_rate': 0,
            'overall_bounce_rate': 0,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }


def get_campaign_metrics(campaign_id: str) -> Dict[str, Any]:
    """
    Récupère les métriques d'une campagne spécifique
    
    Args:
        campaign_id: Identifiant de la campagne
        
    Returns:
        Dictionnaire contenant les métriques de la campagne
    """
    try:
        # Récupération des informations de base de la campagne
        campaign_query = """
        SELECT id, name, status, niche_id, target_leads, created_at
        FROM campaigns 
        WHERE id = :campaign_id OR name = :campaign_id
        """
        campaign_info = DatabaseService.fetch_one(campaign_query, {'campaign_id': campaign_id}) or {}
        
        if not campaign_info:
            return {'error': f'Campagne {campaign_id} non trouvée'}
        
        # Récupération des métriques des messages de cette campagne
        messages_query = """
        SELECT 
            COUNT(*) as sent_count,
            COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_count,
            COUNT(CASE WHEN status = 'opened' THEN 1 END) as open_count,
            COUNT(CASE WHEN status = 'clicked' THEN 1 END) as click_count,
            COUNT(CASE WHEN status = 'replied' THEN 1 END) as response_count,
            COUNT(CASE WHEN status = 'bounced' THEN 1 END) as bounce_count,
            COUNT(CASE WHEN status = 'unsubscribed' THEN 1 END) as unsubscribe_count
        FROM messages 
        WHERE campaign_id = :campaign_id OR campaign_name = :campaign_id
        """
        messages_metrics = DatabaseService.fetch_one(messages_query, {'campaign_id': campaign_id}) or {}
        
        # Récupération des leads associés à cette campagne
        leads_query = """
        SELECT COUNT(*) as leads_count
        FROM leads l
        JOIN campaigns c ON l.niche_id = c.niche_id
        WHERE c.id = :campaign_id OR c.name = :campaign_id
        """
        leads_data = DatabaseService.fetch_one(leads_query, {'campaign_id': campaign_id}) or {}
        
        # Combinaison des métriques
        metrics = {
            **campaign_info,
            **messages_metrics,
            **leads_data,
            'conversion_count': 0,  # À implémenter selon votre logique métier
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        return {
            'error': str(e),
            'campaign_id': campaign_id,
            'timestamp': datetime.datetime.now().isoformat()
        }


def get_campaign_responses(campaign_id: str) -> List[Dict[str, Any]]:
    """
    Récupère les réponses reçues pour une campagne spécifique
    
    Args:
        campaign_id: Identifiant de la campagne
        
    Returns:
        Liste des réponses avec analyse de sentiment
    """
    try:
        responses_query = """
        SELECT 
            m.id,
            m.lead_email,
            m.content,
            m.created_at,
            m.status,
            l.company_name,
            l.first_name,
            l.last_name
        FROM messages m
        LEFT JOIN leads l ON m.lead_email = l.email
        WHERE (m.campaign_id = :campaign_id OR m.campaign_name = :campaign_id)
        AND m.status = 'replied'
        ORDER BY m.created_at DESC
        """
        
        responses = DatabaseService.fetch_all(responses_query, {'campaign_id': campaign_id})
        
        # Ajout d'une analyse de sentiment basique pour chaque réponse
        for response in responses:
            content = (response.get('content', '') or '').lower()
            
            # Analyse de sentiment simple basée sur des mots-clés
            positive_keywords = ['intéressé', 'oui', 'merci', 'contact', 'rdv', 'rencontre', 'discussion']
            negative_keywords = ['non', 'pas intéressé', 'stop', 'remove', 'unsubscribe', 'ne pas']
            
            positive_score = sum(1 for keyword in positive_keywords if keyword in content)
            negative_score = sum(1 for keyword in negative_keywords if keyword in content)
            
            if positive_score > negative_score:
                response['sentiment'] = 'positive'
            elif negative_score > positive_score:
                response['sentiment'] = 'negative'
            else:
                response['sentiment'] = 'neutral'
            
            response['sentiment_score'] = positive_score - negative_score
        
        return responses
        
    except Exception as e:
        return []


def get_niche_campaigns(niche: str, time_period: str = "all") -> List[str]:
    """
    Récupère les campagnes associées à une niche
    
    Args:
        niche: Nom de la niche
        time_period: Période de temps (all, last_month, last_week, etc.)
        
    Returns:
        Liste des identifiants de campagnes
    """
    try:
        base_query = """
        SELECT c.id, c.name
        FROM campaigns c
        JOIN niches n ON c.niche_id = n.id
        WHERE n.name = :niche OR n.name ILIKE :niche_pattern
        """
        
        params = {
            'niche': niche,
            'niche_pattern': f'%{niche}%'
        }
        
        # Ajout de filtre temporel si nécessaire
        if time_period == "last_month":
            base_query += " AND c.created_at >= NOW() - INTERVAL '1 month'"
        elif time_period == "last_week":
            base_query += " AND c.created_at >= NOW() - INTERVAL '1 week'"
        elif time_period == "last_day":
            base_query += " AND c.created_at >= NOW() - INTERVAL '1 day'"
        
        base_query += " ORDER BY c.created_at DESC"
        
        campaigns = DatabaseService.fetch_all(base_query, params)
        
        # Retourner les IDs des campagnes
        return [str(campaign['id']) for campaign in campaigns]
        
    except Exception as e:
        return []


def get_all_niches() -> List[str]:
    """
    Récupère toutes les niches disponibles
    
    Returns:
        Liste des noms de niches
    """
    try:
        query = "SELECT DISTINCT name FROM niches WHERE name IS NOT NULL ORDER BY name"
        niches = DatabaseService.fetch_all(query)
        return [niche['name'] for niche in niches if niche.get('name')]
        
    except Exception as e:
        return []


def get_niche_performance_summary(niche: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un résumé des performances d'une niche
    
    Args:
        niche: Nom de la niche
        
    Returns:
        Dictionnaire avec le résumé des performances ou None
    """
    try:
        # Récupération des campagnes de la niche
        campaigns = get_niche_campaigns(niche)
        
        if not campaigns:
            return None
        
        # Agrégation des métriques de toutes les campagnes de la niche
        total_metrics = {
            'sent_count': 0,
            'delivered_count': 0,
            'open_count': 0,
            'response_count': 0,
            'bounce_count': 0,
            'campaigns_count': len(campaigns)
        }
        
        for campaign_id in campaigns:
            campaign_metrics = get_campaign_metrics(campaign_id)
            
            total_metrics['sent_count'] += campaign_metrics.get('sent_count', 0)
            total_metrics['delivered_count'] += campaign_metrics.get('delivered_count', 0)
            total_metrics['open_count'] += campaign_metrics.get('open_count', 0)
            total_metrics['response_count'] += campaign_metrics.get('response_count', 0)
            total_metrics['bounce_count'] += campaign_metrics.get('bounce_count', 0)
        
        # Calcul des taux
        sent_count = total_metrics['sent_count']
        delivered_count = total_metrics['delivered_count']
        
        performance_summary = {
            'niche': niche,
            **total_metrics,
            'delivery_rate': delivered_count / max(sent_count, 1),
            'open_rate': total_metrics['open_count'] / max(delivered_count, 1),
            'response_rate': total_metrics['response_count'] / max(delivered_count, 1),
            'bounce_rate': total_metrics['bounce_count'] / max(sent_count, 1),
            'conversion_rate': 0,  # À implémenter selon votre logique métier
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return performance_summary
        
    except Exception as e:
        return {
            'niche': niche,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }


def get_campaign_temporal_context(campaign_id: str) -> Dict[str, Any]:
    """
    Récupère le contexte temporel détaillé d'une campagne
    
    Args:
        campaign_id: Identifiant de la campagne
        
    Returns:
        Contexte temporel de la campagne pour prise de décision intelligente
    """
    try:
        # Informations temporelles de la campagne
        temporal_query = """
        SELECT 
            c.id, c.name, c.status, c.niche_id, c.created_at, c.start_date, c.end_date,
            n.name as niche_name,
            EXTRACT(DAYS FROM NOW() - c.created_at) as days_since_creation,
            EXTRACT(DAYS FROM NOW() - COALESCE(c.start_date, c.created_at)) as days_since_start,
            CASE 
                WHEN EXTRACT(DAYS FROM NOW() - COALESCE(c.start_date, c.created_at)) < 5 THEN 'lancement'
                WHEN EXTRACT(DAYS FROM NOW() - COALESCE(c.start_date, c.created_at)) < 10 THEN 'rodage'
                ELSE 'mature'
            END as campaign_phase,
            CASE 
                WHEN EXTRACT(DAYS FROM NOW() - COALESCE(c.start_date, c.created_at)) < 5 THEN 'Trop récent pour décisions drastiques'
                WHEN EXTRACT(DAYS FROM NOW() - COALESCE(c.start_date, c.created_at)) < 10 THEN 'Optimisations légères possibles'
                ELSE 'Analyse complète recommandée'
            END as decision_readiness
        FROM campaigns c
        LEFT JOIN niches n ON c.niche_id = n.id
        WHERE c.id = :campaign_id OR c.name = :campaign_id
        """
        temporal_info = DatabaseService.fetch_one(temporal_query, {'campaign_id': campaign_id}) or {}
        
        if not temporal_info:
            return {'error': f'Campagne {campaign_id} non trouvée'}
        
        # Évolution des métriques par jour (derniers 14 jours)
        daily_evolution_query = """
        SELECT 
            DATE(created_at) as message_date,
            COUNT(*) as daily_sent,
            COUNT(CASE WHEN status = 'delivered' THEN 1 END) as daily_delivered,
            COUNT(CASE WHEN status = 'opened' THEN 1 END) as daily_opened,
            COUNT(CASE WHEN status = 'replied' THEN 1 END) as daily_replied
        FROM messages 
        WHERE (campaign_id = :campaign_id OR campaign_name = :campaign_id)
        AND created_at >= NOW() - INTERVAL '14 days'
        GROUP BY DATE(created_at)
        ORDER BY message_date DESC
        """
        daily_evolution = DatabaseService.fetch_all(daily_evolution_query, {'campaign_id': campaign_id})
        
        # Calcul des tendances
        trends = _calculate_trends(daily_evolution)
        
        # Métriques de benchmark par phase
        benchmark_metrics = _get_phase_benchmarks(temporal_info.get('campaign_phase', 'mature'))
        
        return {
            'campaign_info': temporal_info,
            'daily_evolution': daily_evolution,
            'trends': trends,
            'phase_benchmarks': benchmark_metrics,
            'recommendation_confidence': _get_recommendation_confidence(temporal_info),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'campaign_id': campaign_id,
            'timestamp': datetime.datetime.now().isoformat()
        }


def get_enhanced_campaign_metrics(campaign_id: str) -> Dict[str, Any]:
    """
    Version enrichie de get_campaign_metrics avec intelligence temporelle
    
    Args:
        campaign_id: Identifiant de la campagne
        
    Returns:
        Métriques enrichies avec contexte temporel
    """
    try:
        # Métriques de base
        base_metrics = get_campaign_metrics(campaign_id)
        
        # Contexte temporel
        temporal_context = get_campaign_temporal_context(campaign_id)
        
        # Fusion des données
        enhanced_metrics = {
            **base_metrics,
            'temporal_context': temporal_context,
            'should_wait_before_decisions': temporal_context.get('campaign_info', {}).get('campaign_phase') in ['lancement', 'rodage'],
            'decision_readiness': temporal_context.get('campaign_info', {}).get('decision_readiness', 'unknown')
        }
        
        return enhanced_metrics
        
    except Exception as e:
        return {
            'error': str(e),
            'campaign_id': campaign_id,
            'timestamp': datetime.datetime.now().isoformat()
        }


def _calculate_trends(daily_evolution: List[Dict[str, Any]]) -> Dict[str, str]:
    """Calcule les tendances sur les métriques quotidiennes"""
    if len(daily_evolution) < 3:
        return {'trend': 'insufficient_data'}
    
    trends = {}
    
    # Derniers 3 jours vs 3 jours précédents
    recent_3_days = daily_evolution[:3]
    previous_3_days = daily_evolution[3:6] if len(daily_evolution) >= 6 else daily_evolution[3:]
    
    if previous_3_days:
        recent_avg_sent = sum(day.get('daily_sent', 0) for day in recent_3_days) / len(recent_3_days)
        previous_avg_sent = sum(day.get('daily_sent', 0) for day in previous_3_days) / len(previous_3_days)
        
        recent_avg_opened = sum(day.get('daily_opened', 0) for day in recent_3_days) / len(recent_3_days)
        previous_avg_opened = sum(day.get('daily_opened', 0) for day in previous_3_days) / len(previous_3_days)
        
        # Calcul des tendances
        if recent_avg_sent > previous_avg_sent * 1.1:
            trends['sending_volume'] = 'increasing'
        elif recent_avg_sent < previous_avg_sent * 0.9:
            trends['sending_volume'] = 'decreasing'
        else:
            trends['sending_volume'] = 'stable'
            
        if previous_avg_sent > 0:
            if recent_avg_opened / max(recent_avg_sent, 1) > previous_avg_opened / max(previous_avg_sent, 1) * 1.1:
                trends['engagement'] = 'improving'
            elif recent_avg_opened / max(recent_avg_sent, 1) < previous_avg_opened / max(previous_avg_sent, 1) * 0.9:
                trends['engagement'] = 'declining'
            else:
                trends['engagement'] = 'stable'
    
    return trends


def _get_phase_benchmarks(phase: str) -> Dict[str, float]:
    """Retourne les benchmarks attendus selon la phase de campagne"""
    benchmarks = {
        'lancement': {
            'expected_open_rate': 0.15,  # Plus bas les premiers jours
            'expected_response_rate': 0.03,
            'message': 'Phase de lancement - performances attendues plus faibles'
        },
        'rodage': {
            'expected_open_rate': 0.25,
            'expected_response_rate': 0.05,
            'message': 'Phase de rodage - optimisations en cours'
        },
        'mature': {
            'expected_open_rate': 0.30,
            'expected_response_rate': 0.08,
            'message': 'Campagne mature - performances stabilisées attendues'
        }
    }
    
    return benchmarks.get(phase, benchmarks['mature'])


def _get_recommendation_confidence(campaign_info: Dict[str, Any]) -> str:
    """Détermine le niveau de confiance pour les recommandations"""
    days_since_start = campaign_info.get('days_since_start', 0)
    
    if days_since_start < 3:
        return 'low'  # Trop tôt pour des recommandations fiables
    elif days_since_start < 7:
        return 'medium'  # Recommandations prudentes
    else:
        return 'high'  # Recommandations complètes possibles


def generate_daily_report() -> Dict[str, Any]:
    """
    Génère le rapport quotidien pour le bot Telegram
    
    Returns:
        Rapport structuré avec métriques et recommandations
    """
    try:
        # Récupération de toutes les campagnes actives
        active_campaigns_query = """
        SELECT id, name, status, created_at, start_date
        FROM campaigns 
        WHERE status = 'active'
        ORDER BY created_at DESC
        """
        active_campaigns = DatabaseService.fetch_all(active_campaigns_query)
        
        # Analyse de chaque campagne
        campaign_reports = []
        alerts = []
        recommendations = []
        
        for campaign in active_campaigns:
            campaign_id = str(campaign['id'])
            
            # Métriques enrichies
            metrics = get_enhanced_campaign_metrics(campaign_id)
            
            # Rapport par campagne
            campaign_report = {
                'id': campaign_id,
                'name': campaign['name'],
                'phase': metrics.get('temporal_context', {}).get('campaign_info', {}).get('campaign_phase', 'unknown'),
                'days_active': metrics.get('temporal_context', {}).get('campaign_info', {}).get('days_since_start', 0),
                'should_wait': metrics.get('should_wait_before_decisions', True),
                'sent_yesterday': _get_yesterday_messages(campaign_id),
                'performance_summary': _get_performance_summary(metrics)
            }
            
            campaign_reports.append(campaign_report)
            
            # Détection d'alertes
            if campaign_report['days_active'] >= 7:  # Seulement après 7 jours
                if campaign_report['performance_summary'].get('status') == 'concerning':
                    alerts.append({
                        'campaign': campaign['name'],
                        'issue': campaign_report['performance_summary'].get('message', 'Performance préoccupante'),
                        'action_needed': True
                    })
            
            # Recommandations quotidiennes
            if campaign_report['days_active'] >= 5:  # Après 5 jours
                daily_recs = _get_daily_recommendations(metrics)
                if daily_recs:
                    recommendations.extend([{**rec, 'campaign': campaign['name']} for rec in daily_recs])
        
        # Métriques globales d'hier
        global_yesterday = _get_global_yesterday_metrics()
        
        return {
            'report_date': datetime.datetime.now().isoformat(),
            'global_metrics': global_yesterday,
            'active_campaigns_count': len(active_campaigns),
            'campaign_reports': campaign_reports,
            'alerts': alerts,
            'daily_recommendations': recommendations,
            'summary': _generate_summary(campaign_reports, alerts)
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'report_date': datetime.datetime.now().isoformat()
        }


def _get_yesterday_messages(campaign_id: str) -> int:
    """Compte les messages envoyés hier pour une campagne"""
    query = """
    SELECT COUNT(*) as count
    FROM messages 
    WHERE (campaign_id = :campaign_id OR campaign_name = :campaign_id)
    AND DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
    """
    result = DatabaseService.fetch_one(query, {'campaign_id': campaign_id})
    return result.get('count', 0) if result else 0


def _get_performance_summary(metrics: Dict[str, Any]) -> Dict[str, str]:
    """Résume les performances d'une campagne"""
    sent_count = metrics.get('sent_count', 0)
    delivered_count = metrics.get('delivered_count', 0)
    response_count = metrics.get('response_count', 0)
    
    if sent_count == 0:
        return {'status': 'no_activity', 'message': 'Aucun message envoyé'}
    
    response_rate = response_count / max(delivered_count, 1)
    phase = metrics.get('temporal_context', {}).get('campaign_info', {}).get('campaign_phase', 'unknown')
    
    # Benchmarks selon la phase
    expected_rates = _get_phase_benchmarks(phase)
    expected_response = expected_rates.get('expected_response_rate', 0.05)
    
    if response_rate >= expected_response:
        return {'status': 'good', 'message': f'Performance conforme (réponses: {response_rate:.1%})'}
    elif response_rate >= expected_response * 0.5:
        return {'status': 'average', 'message': f'Performance moyenne (réponses: {response_rate:.1%})'}
    else:
        return {'status': 'concerning', 'message': f'Performance faible (réponses: {response_rate:.1%})'}


def _get_daily_recommendations(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """Génère les recommandations quotidiennes pour une campagne"""
    recommendations = []
    
    confidence = metrics.get('temporal_context', {}).get('recommendation_confidence', 'low')
    trends = metrics.get('temporal_context', {}).get('trends', {})
    
    if confidence == 'low':
        return []  # Pas de recommandations si confiance faible
    
    # Recommandations basées sur les tendances
    if trends.get('engagement') == 'declining':
        recommendations.append({
            'type': 'content',
            'priority': 'medium',
            'action': 'Tester de nouveaux sujets d\'email',
            'reason': 'Engagement en baisse détecté'
        })
    
    if trends.get('sending_volume') == 'decreasing':
        recommendations.append({
            'type': 'volume',
            'priority': 'low',
            'action': 'Vérifier la cadence d\'envoi',
            'reason': 'Volume d\'envoi en diminution'
        })
    
    return recommendations


def _get_global_yesterday_metrics() -> Dict[str, Any]:
    """Récupère les métriques globales d'hier"""
    query = """
    SELECT 
        COUNT(*) as total_sent_yesterday,
        COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_yesterday,
        COUNT(CASE WHEN status = 'opened' THEN 1 END) as opened_yesterday,
        COUNT(CASE WHEN status = 'replied' THEN 1 END) as replied_yesterday
    FROM messages 
    WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
    """
    result = DatabaseService.fetch_one(query)
    return result if result else {}


def _generate_summary(campaign_reports: List[Dict], alerts: List[Dict]) -> str:
    """Génère un résumé textuel du rapport"""
    total_campaigns = len(campaign_reports)
    
    if not campaign_reports:
        return "Aucune campagne active aujourd'hui."
    
    phases = {}
    for report in campaign_reports:
        phase = report.get('phase', 'unknown')
        phases[phase] = phases.get(phase, 0) + 1
    
    summary = f"{total_campaigns} campagne(s) active(s): "
    phase_desc = []
    if phases.get('lancement', 0) > 0:
        phase_desc.append(f"{phases['lancement']} en lancement")
    if phases.get('rodage', 0) > 0:
        phase_desc.append(f"{phases['rodage']} en rodage")
    if phases.get('mature', 0) > 0:
        phase_desc.append(f"{phases['mature']} matures")
    
    summary += ", ".join(phase_desc)
    
    if alerts:
        summary += f". {len(alerts)} alerte(s) nécessitant attention."
    else:
        summary += ". Toutes les campagnes fonctionnent normalement."
    
    return summary

