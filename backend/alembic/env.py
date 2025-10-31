import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Load .env file for local development
from dotenv import load_dotenv
load_dotenv()

# Import all models for Alembic to detect
from app.models.user import User
from app.models.session import Session
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document, ConversationDocument
from app.core.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from environment variables"""
    # Check if SQLite is requested
    use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
    if use_sqlite:
        url = "sqlite:///./data/app.db"
        print(f"Database URL: {url}")
        return url

    # First try to get DATABASE_URL from .env (for local development)
    url = os.getenv("DATABASE_URL")
    if url:
        # Replace asyncpg with psycopg2 for Alembic (sync driver)
        url = url.replace("postgresql+asyncpg://", "postgresql://")
        print(f"Database URL: {url.split('@')[0].split('://')[0]}://***@{url.split('@')[1]}")
        return url

    # Fallback to individual env vars (for Docker)
    user = os.getenv("POSTGRES_USER", "llm_app")
    password = os.getenv("POSTGRES_PASSWORD", "changeme")
    host = os.getenv("POSTGRES_HOST", "localhost")  # Changed default to localhost
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "llm_webapp")
    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    print(f"Database URL: postgresql://{user}:***@{host}:{port}/{db}")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
