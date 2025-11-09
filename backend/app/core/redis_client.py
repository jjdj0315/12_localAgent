"""
Redis client singleton for caching and rate limiting.
"""
import logging
from typing import Optional

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client singleton.

    Provides a single Redis connection instance shared across the application.
    Used for:
    - Rate limiting (shared counter across workers)
    - LLM response caching
    """

    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls, host: str = "redis", port: int = 6379, db: int = 0) -> redis.Redis:
        """
        Get Redis client instance (singleton pattern).

        Args:
            host: Redis host (default: "redis" for Docker)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)

        Returns:
            Redis client instance
        """
        if cls._instance is None:
            try:
                cls._instance = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,  # Auto-decode bytes to str
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                cls._instance.ping()
                logger.info(f"Redis client initialized: {host}:{port}/db{db}")
            except RedisError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Return a None-safe mock for graceful degradation
                cls._instance = None
                raise

        return cls._instance

    @classmethod
    def is_available(cls) -> bool:
        """Check if Redis is available."""
        try:
            if cls._instance is None:
                return False
            cls._instance.ping()
            return True
        except RedisError:
            return False


# Global instance
def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client instance.

    Returns None if Redis is unavailable (graceful degradation).
    """
    try:
        return RedisClient.get_instance()
    except RedisError:
        logger.warning("Redis unavailable, returning None")
        return None
