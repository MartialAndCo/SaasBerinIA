from __future__ import with_statement
import sys
import os
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from sqlalchemy.ext.declarative import declarative_base
from alembic import context
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('alembic_migration')

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models from messenger module
from models.messenger import Base, MailgunConfig, TwilioConfig, MessengerPerformance, MessengerDirectives

# Database URL
DATABASE_URL = "postgresql://berinia_user:bhcmi6pm@localhost/berinia_db"

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use the database URL from the configuration
config = context.config
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Set up the metadata
target_metadata = Base.metadata

# Configure logging
try:
    fileConfig(config.config_file_name)
except Exception as e:
    logger.error(f"Error configuring logging: {e}")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    try:
        logger.info("Running offline migrations")
        context.configure(
            url=DATABASE_URL,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()
    except Exception as e:
        logger.error(f"Offline migration error: {e}")
        raise

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    try:
        logger.info("Running online migrations")
        def do_run_migrations(connection):
            context.configure(
                connection=connection, 
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True
            )

            with context.begin_transaction():
                context.run_migrations()

        with engine.connect() as connection:
            do_run_migrations(connection)
    except Exception as e:
        logger.error(f"Online migration error: {e}")
        raise

# Force the migration to run
context.configure(
    url=DATABASE_URL,
    target_metadata=target_metadata,
    compare_type=True,
    compare_server_default=True
)

# Ensure the alembic_version table exists
def ensure_version_table():
    try:
        with engine.connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)")
    except Exception as e:
        logger.error(f"Error creating alembic_version table: {e}")

ensure_version_table()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
