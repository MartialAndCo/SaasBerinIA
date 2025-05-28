from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta

from app.models.system_log import SystemLog
from app.schemas.system_log import SystemLogCreate, SystemLogUpdate

class SystemLogCRUD:
    def create(self, db: Session, *, obj_in: SystemLogCreate) -> SystemLog:
        """Créer un nouveau log système"""
        db_obj = SystemLog(
            level=obj_in.level,
            source=obj_in.source,
            agent_name=obj_in.agent_name,
            module=obj_in.module,
            message=obj_in.message,
            details=obj_in.details,
            context_id=obj_in.context_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        level: Optional[str] = None,
        source: Optional[str] = None,
        agent_name: Optional[str] = None,
        module: Optional[str] = None,
        context_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> List[SystemLog]:
        """Récupérer plusieurs logs avec filtres"""
        query = db.query(SystemLog)
        
        # Filtres
        if level:
            query = query.filter(SystemLog.level == level)
        if source:
            query = query.filter(SystemLog.source == source)
        if agent_name:
            query = query.filter(SystemLog.agent_name == agent_name)
        if module:
            query = query.filter(SystemLog.module == module)
        if context_id:
            query = query.filter(SystemLog.context_id == context_id)
        if start_date:
            query = query.filter(SystemLog.timestamp >= start_date)
        if end_date:
            query = query.filter(SystemLog.timestamp <= end_date)
        if search:
            query = query.filter(SystemLog.message.ilike(f"%{search}%"))
        
        return query.order_by(desc(SystemLog.timestamp)).offset(skip).limit(limit).all()

    def count(
        self,
        db: Session,
        *,
        level: Optional[str] = None,
        source: Optional[str] = None,
        agent_name: Optional[str] = None,
        module: Optional[str] = None,
        context_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> int:
        """Compter les logs avec filtres"""
        query = db.query(SystemLog)
        
        # Mêmes filtres que get_multi
        if level:
            query = query.filter(SystemLog.level == level)
        if source:
            query = query.filter(SystemLog.source == source)
        if agent_name:
            query = query.filter(SystemLog.agent_name == agent_name)
        if module:
            query = query.filter(SystemLog.module == module)
        if context_id:
            query = query.filter(SystemLog.context_id == context_id)
        if start_date:
            query = query.filter(SystemLog.timestamp >= start_date)
        if end_date:
            query = query.filter(SystemLog.timestamp <= end_date)
        if search:
            query = query.filter(SystemLog.message.ilike(f"%{search}%"))
        
        return query.count()

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Obtenir les statistiques des logs"""
        
        # Total des logs
        total_logs = db.query(SystemLog).count()
        
        # Par niveau
        by_level = {}
        level_stats = db.query(
            SystemLog.level,
            func.count(SystemLog.id)
        ).group_by(SystemLog.level).all()
        
        for level, count in level_stats:
            by_level[level] = count
        
        # Par source
        by_source = {}
        source_stats = db.query(
            SystemLog.source,
            func.count(SystemLog.id)
        ).group_by(SystemLog.source).all()
        
        for source, count in source_stats:
            by_source[source] = count
        
        # Par agent
        by_agent = {}
        agent_stats = db.query(
            SystemLog.agent_name,
            func.count(SystemLog.id)
        ).filter(SystemLog.agent_name.isnot(None)).group_by(SystemLog.agent_name).all()
        
        for agent, count in agent_stats:
            by_agent[agent] = count
        
        # Logs récents (dernière heure)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_hour = db.query(SystemLog).filter(
            SystemLog.timestamp >= one_hour_ago
        ).count()
        
        return {
            "total_logs": total_logs,
            "by_level": by_level,
            "by_source": by_source,
            "by_agent": by_agent,
            "recent_hour": recent_hour
        }

    def delete_old_logs(self, db: Session, days_to_keep: int = 30) -> int:
        """Supprimer les logs anciens (nettoyage automatique)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Compter les logs à supprimer
        count = db.query(SystemLog).filter(
            SystemLog.timestamp < cutoff_date
        ).count()
        
        # Supprimer les logs anciens
        db.query(SystemLog).filter(
            SystemLog.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        return count

    def get_recent_errors(self, db: Session, limit: int = 50) -> List[SystemLog]:
        """Récupérer les erreurs récentes"""
        return db.query(SystemLog).filter(
            SystemLog.level == "ERROR"
        ).order_by(desc(SystemLog.timestamp)).limit(limit).all()

    def get_agent_logs(
        self, 
        db: Session, 
        agent_name: str, 
        limit: int = 100,
        level: Optional[str] = None
    ) -> List[SystemLog]:
        """Récupérer les logs d'un agent spécifique"""
        query = db.query(SystemLog).filter(SystemLog.agent_name == agent_name)
        
        if level:
            query = query.filter(SystemLog.level == level)
        
        return query.order_by(desc(SystemLog.timestamp)).limit(limit).all()

# Instance unique du CRUD
system_log = SystemLogCRUD()
