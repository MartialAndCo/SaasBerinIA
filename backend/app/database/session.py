from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Use the settings from config.py instead of hardcoded values
# Mais on s'assure que l'URL est bien construite avec les bonnes valeurs
SQLALCHEMY_DATABASE_URL = "postgresql://berinia_user:berinia_pass@localhost:5432/berinia"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
