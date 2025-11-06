"""Database connection and session management"""

import os
import time
from typing import AsyncGenerator

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Import Prometheus metrics
from app.core.metrics import (
    db_connections_active,
    db_query_duration,
    db_queries_total
)

# Get database URL from environment
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() in ("true", "1", "yes")

if USE_SQLITE:
    # SQLite for local development
    DB_FILE = os.getenv("SQLITE_DB_FILE", "llm_webapp.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"
    ASYNC_SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"
else:
    # PostgreSQL for production
    POSTGRES_USER = os.getenv("POSTGRES_USER", "llm_app")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "llm_webapp")

    # Sync database URL (for Alembic migrations)
    SQLALCHEMY_DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Async database URL (for FastAPI)
    ASYNC_SQLALCHEMY_DATABASE_URL = (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

# Create sync engine (for migrations)
if USE_SQLITE:
    sync_engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    sync_engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=40,
    )

# Create async engine (for application)
if USE_SQLITE:
    async_engine = create_async_engine(
        ASYNC_SQLALCHEMY_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL with READ COMMITTED isolation level (FR-113, T294)
    # - READ COMMITTED: Prevents dirty reads while allowing concurrent metric collection
    # - pool_pre_ping: Connection health checks before using from pool
    # - pool_recycle: Recycle connections after 1 hour (3600s) to avoid stale connections
    async_engine = create_async_engine(
        ASYNC_SQLALCHEMY_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # T294: Connection health checks
        pool_size=20,
        max_overflow=40,
        pool_recycle=3600,  # T294: Recycle connections after 1 hour
        isolation_level="READ COMMITTED"  # T294: Consistent metric snapshots
    )

# ==============================================================================
# Database Metrics Collection
# ==============================================================================

def _get_query_type(statement: str) -> str:
    """Extract query type from SQL statement"""
    statement = statement.strip().upper()
    if statement.startswith('SELECT'):
        return 'select'
    elif statement.startswith('INSERT'):
        return 'insert'
    elif statement.startswith('UPDATE'):
        return 'update'
    elif statement.startswith('DELETE'):
        return 'delete'
    else:
        return 'other'

# Event listener for query execution timing (FR-117)
# Universal listener captures both sync (migrations) and async (application) queries
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time for both sync and async engines"""
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query duration and count for both sync and async engines"""
    # Calculate duration
    duration = time.time() - context._query_start_time

    # Determine query type
    query_type = _get_query_type(statement)

    # Record metrics
    db_query_duration.labels(query_type=query_type).observe(duration)
    db_queries_total.labels(query_type=query_type, status='success').inc()

# Update connection pool metrics (FR-117)
def update_pool_metrics():
    """Update connection pool metrics from async engine"""
    try:
        # Get pool from async engine's sync_engine (FR-117)
        # This captures actual application connection usage
        pool = async_engine.sync_engine.pool
        db_connections_active.set(pool.checkedout())
    except Exception as e:
        # Ignore errors (pool might not be initialized yet)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to update pool metrics: {e}")

# Create session factories
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


# Dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.

    Usage:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    # Update connection pool metrics
    update_pool_metrics()

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            # Update metrics after closing
            update_pool_metrics()


def get_sync_db() -> Session:
    """
    Get sync database session (for scripts and migrations).

    Usage:
        db = get_sync_db()
        try:
            # ... do work
            db.commit()
        finally:
            db.close()
    """
    db = SyncSessionLocal()
    try:
        return db
    finally:
        db.close()
