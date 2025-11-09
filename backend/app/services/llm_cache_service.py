"""
LLM Response Cache Service

Caches LLM responses to reduce computation and improve response time.
Only caches responses for queries without conversation context or document references.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

from redis.exceptions import RedisError

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


class LLMCacheService:
    """
    Service for caching LLM responses.

    Caching strategy:
    - Only cache queries without conversation context (new conversations)
    - Only cache queries without document references
    - Do not cache time-sensitive queries
    - Do not cache personal queries
    - Use MD5 hash of query as cache key
    - TTL: 1 hour (3600 seconds)
    """

    # Time-related keywords (not cacheable)
    TIME_KEYWORDS = ["지금", "현재", "오늘", "어제", "내일", "시간", "날짜", "몇 시"]

    # Personal keywords (not cacheable)
    PERSONAL_KEYWORDS = ["나", "내", "우리", "저", "제", "나의", "내가", "우리가"]

    @staticmethod
    def is_cacheable(
        query: str, conversation_id: Optional[str], document_ids: Optional[list]
    ) -> bool:
        """
        Check if a query response can be cached.

        Args:
            query: User query
            conversation_id: Conversation ID (None for new conversations)
            document_ids: List of document IDs (None or empty for no documents)

        Returns:
            True if response can be cached, False otherwise
        """
        # Don't cache if conversation context exists
        if conversation_id:
            logger.debug(f"Not cacheable: conversation context exists ({conversation_id})")
            return False

        # Don't cache if document references exist
        if document_ids and len(document_ids) > 0:
            logger.debug(f"Not cacheable: document references exist ({len(document_ids)} docs)")
            return False

        # Don't cache time-sensitive queries
        query_lower = query.lower()
        if any(kw in query_lower for kw in LLMCacheService.TIME_KEYWORDS):
            logger.debug(f"Not cacheable: time-sensitive query")
            return False

        # Don't cache personal queries
        if any(kw in query for kw in LLMCacheService.PERSONAL_KEYWORDS):
            logger.debug(f"Not cacheable: personal query")
            return False

        logger.debug(f"Cacheable query: {query[:50]}...")
        return True

    @staticmethod
    def get_cache_key(query: str) -> str:
        """
        Generate cache key from query.

        Uses MD5 hash to avoid key collision and handle special characters.

        Args:
            query: User query

        Returns:
            Redis cache key
        """
        query_hash = hashlib.md5(query.encode("utf-8")).hexdigest()
        return f"llm_response:{query_hash}"

    @staticmethod
    def get_cached_response(query: str) -> Optional[str]:
        """
        Get cached LLM response.

        Args:
            query: User query

        Returns:
            Cached response if exists, None otherwise
        """
        redis = get_redis()
        if not redis:
            logger.debug("Redis unavailable, cache miss")
            return None

        cache_key = LLMCacheService.get_cache_key(query)

        try:
            cached = redis.get(cache_key)
            if cached:
                # Parse JSON
                data = json.loads(cached)
                response = data.get("response")
                cached_at = data.get("cached_at")

                logger.info(
                    f"[LLM Cache HIT] query={query[:50]}... cached_at={cached_at}"
                )
                return response
            else:
                logger.debug(f"[LLM Cache MISS] query={query[:50]}...")
                return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache read error: {e}")
            return None

    @staticmethod
    def set_cached_response(query: str, response: str, ttl: int = 3600) -> bool:
        """
        Cache LLM response.

        Args:
            query: User query
            response: LLM response
            ttl: Time to live in seconds (default: 3600 = 1 hour)

        Returns:
            True if cached successfully, False otherwise
        """
        redis = get_redis()
        if not redis:
            logger.debug("Redis unavailable, skip caching")
            return False

        cache_key = LLMCacheService.get_cache_key(query)

        try:
            # Store as JSON with metadata
            data = {
                "query": query,
                "response": response,
                "cached_at": datetime.now().isoformat(),
            }

            redis.setex(cache_key, ttl, json.dumps(data, ensure_ascii=False))

            logger.info(f"[LLM Cache SET] query={query[:50]}... ttl={ttl}s")
            return True

        except (RedisError, TypeError) as e:
            logger.warning(f"Cache write error: {e}")
            return False

    @staticmethod
    def invalidate_cache(query: str) -> bool:
        """
        Invalidate cached response for a query.

        Args:
            query: User query

        Returns:
            True if invalidated successfully, False otherwise
        """
        redis = get_redis()
        if not redis:
            return False

        cache_key = LLMCacheService.get_cache_key(query)

        try:
            deleted = redis.delete(cache_key)
            if deleted:
                logger.info(f"[LLM Cache INVALIDATE] query={query[:50]}...")
            return bool(deleted)

        except RedisError as e:
            logger.warning(f"Cache invalidation error: {e}")
            return False


# Global instance
llm_cache_service = LLMCacheService()
