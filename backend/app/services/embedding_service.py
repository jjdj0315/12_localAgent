"""
Embedding Service for document vectorization.

Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) for
generating 384-dimensional embeddings for Korean text.
"""
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using sentence-transformers.

    Model: paraphrase-multilingual-MiniLM-L12-v2
    - Supports Korean language
    - 384-dimensional embeddings
    - CPU-compatible
    - ~420MB model size
    """

    _instance = None
    _model = None

    # Chunking configuration (FR-009)
    CHUNK_SIZE = 500  # characters
    CHUNK_OVERLAP = 50  # characters

    # Model configuration
    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM = 384

    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize embedding model (loaded once due to singleton)."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.MODEL_NAME}")
            self._model = SentenceTransformer(self.MODEL_NAME)
            logger.info(f"Embedding model loaded successfully (dim={self.EMBEDDING_DIM})")

    def chunk_text(self, text: str) -> List[Tuple[str, int]]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk

        Returns:
            List of (chunk_text, start_position) tuples

        Example:
            >>> chunks = service.chunk_text("Hello world" * 100)
            >>> len(chunks)  # Multiple chunks
            >>> chunks[0][1]  # 0 (first chunk starts at position 0)
        """
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Extract chunk
            end = min(start + self.CHUNK_SIZE, text_length)
            chunk = text[start:end].strip()

            if chunk:  # Only add non-empty chunks
                chunks.append((chunk, start))

            # Move to next chunk with overlap
            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP

            # Prevent infinite loop on very short text
            if start + self.CHUNK_OVERLAP >= text_length:
                break

        logger.debug(f"Chunked text into {len(chunks)} chunks (size={self.CHUNK_SIZE}, overlap={self.CHUNK_OVERLAP})")
        return chunks

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of 384-dimensional embedding vectors

        Example:
            >>> embeddings = service.embed(["안녕하세요", "Hello world"])
            >>> len(embeddings)  # 2
            >>> len(embeddings[0])  # 384
        """
        if not texts:
            return []

        logger.debug(f"Generating embeddings for {len(texts)} texts...")

        # Generate embeddings
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32  # Process in batches for efficiency
        )

        # Convert to list of lists for JSON serialization
        embedding_list = embeddings.tolist()

        logger.debug(f"Generated {len(embedding_list)} embeddings (dim={len(embedding_list[0]) if embedding_list else 0})")
        return embedding_list

    def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text string to embed

        Returns:
            384-dimensional embedding vector

        Example:
            >>> embedding = service.embed_single("안녕하세요")
            >>> len(embedding)  # 384
        """
        embeddings = self.embed([text])
        return embeddings[0] if embeddings else []

    def embed_document(self, text: str) -> List[Tuple[str, List[float], int]]:
        """
        Chunk and embed entire document.

        Args:
            text: Full document text

        Returns:
            List of (chunk_text, embedding_vector, start_position) tuples

        Example:
            >>> results = service.embed_document("Long document text...")
            >>> for chunk, embedding, pos in results:
            ...     print(f"Position {pos}: {len(embedding)}-dim vector")
        """
        if not text or not text.strip():
            logger.warning("Empty document text provided for embedding")
            return []

        # Step 1: Chunk text
        chunks = self.chunk_text(text)

        if not chunks:
            logger.warning("No valid chunks generated from document")
            return []

        # Step 2: Extract chunk texts
        chunk_texts = [chunk[0] for chunk in chunks]

        # Step 3: Generate embeddings
        embeddings = self.embed(chunk_texts)

        # Step 4: Combine results
        results = [
            (chunk[0], embeddings[i], chunk[1])
            for i, chunk in enumerate(chunks)
        ]

        logger.info(f"Embedded document into {len(results)} chunks with {self.EMBEDDING_DIM}-dim vectors")
        return results


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """
    Get singleton instance of EmbeddingService.

    Returns:
        EmbeddingService instance (singleton)

    Example:
        >>> service = get_embedding_service()
        >>> embedding = service.embed_single("Hello")
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
