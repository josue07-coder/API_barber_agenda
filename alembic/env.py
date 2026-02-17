import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

#  RUTA DEL PROYECTO
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

#  CARGAR VARIABLES DE ENTORNO
load_dotenv(BASE_DIR / ".env")

print("✅ ALEMBIC ENV CARGADO")

# IMPORTS DEL PROYECTO
from app.core.config import settings
from app.database.base import Base

from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment


config = context.config

fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
        print("ALEMBIC DATABASE URL:", settings.DATABASE_URL)
        return settings.DATABASE_URL

def run_migrations_offline():
        context.configure(
                url=get_url(),
                target_metadata=target_metadata,
                literal_binds=True,
                compare_type=True
        )

        with context.begin_transaction():
                context.run_migrations()
        
def run_migrations_online():
        from app.database.session import engine

        with engine.connect() as connection:
            context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            version_table="alembic_version",
            version_table_schema="public",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
        run_migrations_offline
else:
        run_migrations_online