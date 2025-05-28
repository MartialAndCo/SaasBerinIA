#!/usr/bin/env python3
"""
Version modifiée de l'application FastAPI principale pour résoudre les problèmes de connexion.
"""
import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
import logging
from sqlalchemy.orm import Session
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
import uvicorn
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
db_user = os.getenv("DB_USER", "berinia_user")
db_password = os.getenv("DB_PASSWORD", "berinia_pass")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "berinia")

# URL de connexion SQLAlchemy
DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
print(f"URL de connexion: {DATABASE_URL.replace(db_password, '*****')}")

# Créer le moteur SQLAlchemy et la session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Fonction de dépendance pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BerinIA API Fixed",
    description="Version corrigée de l'API BerinIA",
    version="0.1.0",
)

# Exception handler middleware
@app.middleware("http")
async def exception_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}"}
        )

# Configuration CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route de base
@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API BerinIA corrigée"}

@app.get("/debug/routes")
def list_routes():
    return [{"path": route.path, "name": route.name} for route in app.routes]

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    """Test simple de la connexion à la base de données."""
    try:
        # Exécuter une requête simple
        result = db.execute(text("SELECT 1 AS test"))
        value = result.scalar()
        
        # Vérifier la table system_settings
        result = db.execute(text("SELECT COUNT(*) FROM system_settings"))
        count = result.scalar()
        
        # Vérifier les paramètres d'intégration
        result = db.execute(text("SELECT * FROM system_settings WHERE name LIKE 'instantly%'"))
        settings = [{"name": row[1], "value": row[2], "type": row[3]} for row in result]
        
        return {
            "connection": "success",
            "test_query_result": value,
            "system_settings_count": count,
            "instantly_settings": settings
        }
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {"connection": "error", "error": str(e)}

@app.get("/api/services/")
def get_services():
    """Simuler l'endpoint de services en retournant des données statiques."""
    return [
        {
            "name": "berinia-api.service",
            "display_name": "berinia-api",
            "description": "API backend principale",
            "status": "active",
            "is_active": True,
            "is_enabled": True,
            "uptime": "3d 4h 12m"
        },
        {
            "name": "berinia-agents.service",
            "display_name": "berinia-agents",
            "description": "Environnement d'exécution des agents IA",
            "status": "inactive",
            "is_active": False,
            "is_enabled": False,
        },
        {
            "name": "berinia-scheduler.service",
            "display_name": "berinia-scheduler",
            "description": "Planificateur de tâches",
            "status": "inactive",
            "is_active": False,
            "is_enabled": False,
        }
    ]

@app.get("/api/system-settings/integrations/instantly")
def get_instantly_settings(db: Session = Depends(get_db)):
    """Récupérer les paramètres d'intégration Instantly.ai depuis la base de données."""
    try:
        # Récupérer les paramètres d'intégration Instantly.ai
        result = db.execute(text("SELECT name, value, data_type FROM system_settings WHERE name LIKE 'instantly%'"))
        settings = {}
        
        for row in result:
            name, value, data_type = row
            
            # Convertir la valeur selon son type
            if data_type == 'boolean':
                settings[name] = value.lower() == 'true'
            elif data_type == 'integer':
                settings[name] = int(value) if value else 0
            else:
                settings[name] = value
        
        return {"status": "success", "data": settings}
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
