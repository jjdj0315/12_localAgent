"""
Qdrant Vector Database Service for document search.

Provides conversation-scoped vector storage and similarity search
using Qdrant with HNSW index and cosine similarity.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from qdrant_client.http.exceptions import UnexpectedResponse
import logging
import os

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Service for managing document vectors in Qdrant.

    Features:
    - Conversation-scoped collections (one collection per conversation)
    - HNSW index for fast similarity search
    - Cosine similarity metric
    - 384-dimensional vectors (paraphrase-multilingual-MiniLM-L12-v2)
    """

    VECTOR_SIZE = 384  # Must match EmbeddingService.EMBEDDING_DIM
    DISTANCE_METRIC = Distance.COSINE
    HNSW_CONFIG = {
        "m": 16,  # Number of edges per node
        "ef_construct": 100,  # Construction time accuracy
    }

    def __init__(
        self,
        host: str = None,
        port: int = None,
        grpc_port: int = None,
    ):
        """
        Initialize Qdrant client.

        Args:
            host: Qdrant server host (default: from env QDRANT_HOST)
            port: Qdrant HTTP port (default: from env QDRANT_PORT or 6333)
            grpc_port: Qdrant gRPC port (default: from env QDRANT_GRPC_PORT or 6334)
        """
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.grpc_port = grpc_port or int(os.getenv("QDRANT_GRPC_PORT", "6334"))

        logger.info(f"Initializing Qdrant client: {self.host}:{self.port}")

        # Initialize client
        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port,
            prefer_grpc=False,  # Use HTTP for simplicity
        )

        logger.info("Qdrant client initialized successfully")

    def _get_collection_name(self, conversation_id: UUID) -> str:
        """
        Get collection name for conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Collection name (format: "conv_{uuid}")
        """
        return f"conv_{str(conversation_id).replace('-', '_')}"

    def ensure_collection(self, conversation_id: UUID) -> str:
        """
        Ensure collection exists for conversation, create if not.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Collection name

        Raises:
            Exception: If collection creation fails
        """
        collection_name = self._get_collection_name(conversation_id)

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                logger.info(f"Creating collection: {collection_name}")

                # Create collection with HNSW index
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.VECTOR_SIZE,
                        distance=self.DISTANCE_METRIC,
                        hnsw_config=self.HNSW_CONFIG,
                    ),
                )

                logger.info(f"Collection created: {collection_name}")
            else:
                logger.debug(f"Collection already exists: {collection_name}")

            return collection_name

        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {e}")
            raise

    def upload_vectors(
        self,
        conversation_id: UUID,
        document_id: UUID,
        chunks: List[Dict[str, Any]],
    ) -> int:
        """
        Upload document chunk vectors to Qdrant.

        Args:
            conversation_id: Conversation UUID
            document_id: Document UUID
            chunks: List of chunk dicts with keys:
                - chunk_text: str (chunk content)
                - embedding: List[float] (384-dim vector)
                - chunk_index: int (position in document)
                - start_position: int (character position)

        Returns:
            Number of vectors uploaded

        Example:
            >>> chunks = [
            ...     {
            ...         "chunk_text": "안녕하세요...",
            ...         "embedding": [0.1, 0.2, ...],  # 384 dims
            ...         "chunk_index": 0,
            ...         "start_position": 0,
            ...     },
            ... ]
            >>> count = service.upload_vectors(conv_id, doc_id, chunks)
        """
        if not chunks:
            logger.warning("No chunks to upload")
            return 0

        collection_name = self.ensure_collection(conversation_id)

        # Prepare points
        points = []
        for idx, chunk in enumerate(chunks):
            # Generate unique point ID using hash (integer for compatibility)
            # Combine document_id and chunk_index to create unique ID
            import hashlib
            id_string = f"{str(document_id)}_{chunk['chunk_index']}"
            point_id = int(hashlib.md5(id_string.encode()).hexdigest()[:15], 16)

            point = PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload={
                    "conversation_id": str(conversation_id),
                    "document_id": str(document_id),
                    "chunk_text": chunk["chunk_text"],
                    "chunk_index": chunk["chunk_index"],
                    "start_position": chunk["start_position"],
                },
            )
            points.append(point)

        try:
            # Upload points
            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            logger.info(f"Uploaded {len(points)} vectors to {collection_name} (document={document_id})")
            return len(points)

        except Exception as e:
            logger.error(f"Failed to upload vectors to {collection_name}: {e}")
            raise

    def search(
        self,
        conversation_id: UUID,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks.

        Args:
            conversation_id: Conversation UUID
            query_vector: Query embedding (384-dim)
            limit: Maximum number of results (default: 5)
            score_threshold: Minimum similarity score (0.0-1.0, default: 0.0)

        Returns:
            List of result dicts with keys:
                - chunk_text: str
                - document_id: str
                - chunk_index: int
                - score: float (cosine similarity 0.0-1.0)

        Example:
            >>> results = service.search(conv_id, query_embedding, limit=5)
            >>> for r in results:
            ...     print(f"Score: {r['score']:.3f} - {r['chunk_text'][:50]}")
        """
        collection_name = self._get_collection_name(conversation_id)

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                logger.info(f"Collection {collection_name} does not exist, returning empty results")
                return []

            # Perform search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )

            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "chunk_text": hit.payload.get("chunk_text", ""),
                    "document_id": hit.payload.get("document_id", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0),
                    "start_position": hit.payload.get("start_position", 0),
                    "score": hit.score,
                })

            logger.info(f"Found {len(results)} results in {collection_name} (threshold={score_threshold})")
            return results

        except UnexpectedResponse as e:
            if "Not found" in str(e):
                logger.info(f"Collection {collection_name} not found, returning empty results")
                return []
            logger.error(f"Search failed in {collection_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            raise

    def delete_document_vectors(
        self,
        conversation_id: UUID,
        document_id: UUID,
    ) -> int:
        """
        Delete all vectors for a specific document.

        Args:
            conversation_id: Conversation UUID
            document_id: Document UUID

        Returns:
            Number of vectors deleted (estimated)

        Example:
            >>> count = service.delete_document_vectors(conv_id, doc_id)
            >>> print(f"Deleted {count} vectors")
        """
        collection_name = self._get_collection_name(conversation_id)

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                logger.info(f"Collection {collection_name} does not exist, nothing to delete")
                return 0

            # Delete points by filter (document_id)
            self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id)),
                        )
                    ]
                ),
            )

            logger.info(f"Deleted vectors for document {document_id} from {collection_name}")
            return 1  # Return success indicator (actual count unknown)

        except Exception as e:
            logger.error(f"Failed to delete document vectors from {collection_name}: {e}")
            raise

    def delete_collection(self, conversation_id: UUID) -> bool:
        """
        Delete entire collection for conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            True if deleted, False if not found

        Example:
            >>> deleted = service.delete_collection(conv_id)
        """
        collection_name = self._get_collection_name(conversation_id)

        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True

        except UnexpectedResponse as e:
            if "Not found" in str(e):
                logger.info(f"Collection {collection_name} not found, nothing to delete")
                return False
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if Qdrant server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            collections = self.client.get_collections()
            logger.debug(f"Qdrant health check OK ({len(collections.collections)} collections)")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Singleton instance
_qdrant_service = None


def get_qdrant_service() -> QdrantService:
    """
    Get singleton instance of QdrantService.

    Returns:
        QdrantService instance (singleton)

    Example:
        >>> service = get_qdrant_service()
        >>> service.health_check()
    """
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service
