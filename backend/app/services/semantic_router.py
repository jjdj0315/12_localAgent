"""
Semantic Router for Query Classification

Fast 2-stage routing:
1. Keyword matching (0.001초) - 90% of queries
2. Embedding similarity (0.01초) - 10% fallback

Replaces slow LLM classification (0.5초) in Unified Orchestrator.
"""

import logging
from typing import Dict, List, Literal

import numpy as np

from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

RouteType = Literal["direct", "reasoning", "specialized"]


class SemanticRouter:
    """
    Fast query routing using keywords and embedding similarity.

    No LLM calls needed - all classification is deterministic and fast.
    """

    # Route definitions with example queries for embedding
    ROUTE_EXAMPLES: Dict[RouteType, List[str]] = {
        "direct": [
            "안녕",
            "날씨 알려줘",
            "지금 몇 시야",
            "Qwen이 뭐야",
            "Python이 뭔가요",
            "감사합니다",
        ],
        "specialized": [
            "문서에서 검색해줘",
            "100 곱하기 200 계산해줘",
            "이 데이터 분석해줘",
            "PDF 파일 찾아줘",
            "엑셀 데이터 정리해줘",
        ],
        "reasoning": [
            "이거 좀 도와줘",
            "어떻게 해야 해?",
            "왜 그래?",
            "무엇을 의미하나요?",
            "차이가 뭐야?",
        ],
    }

    # Keyword patterns for fast matching
    KEYWORD_PATTERNS: Dict[RouteType, List[str]] = {
        "direct": [
            "안녕",
            "날씨",
            "시간",
            "몇 시",
            "뭐야",
            "뭔가요",
            "감사",
            "고마워",
            "누구",
            "언제",
            "어디",
        ],
        "specialized": [
            "검색",
            "찾아",
            "계산",
            "분석",
            "정리",
            "비교",
            "문서",
            "파일",
            "데이터",
            "엑셀",
            "pdf",
            "작성",
            "생성",
        ],
        "reasoning": [
            "어떻게",
            "왜",
            "차이",
            "이거",
            "그거",
            "저거",
            "도와",
            "의미",
            "설명",
            "무엇",
        ],
    }

    def __init__(self):
        """Initialize router with pre-computed route embeddings."""
        self.route_embeddings: Dict[RouteType, np.ndarray] = {}
        self._initialize_route_embeddings()

    def _initialize_route_embeddings(self):
        """Pre-compute average embeddings for each route."""
        logger.info("Initializing Semantic Router embeddings...")

        for route, examples in self.ROUTE_EXAMPLES.items():
            # Generate embeddings for all examples
            embeddings = []
            for example in examples:
                emb = embedding_service.embed_query(example)
                embeddings.append(emb)

            # Compute average embedding for this route
            avg_embedding = np.mean(embeddings, axis=0)
            self.route_embeddings[route] = avg_embedding

            logger.info(f"  {route}: {len(examples)} examples → {avg_embedding.shape}")

        logger.info("Semantic Router initialized successfully")

    def classify(self, query: str) -> RouteType:
        """
        Classify query using 2-stage approach.

        Stage 1: Keyword matching (fast, 90% hit rate)
        Stage 2: Embedding similarity (slower, fallback)

        Args:
            query: User query

        Returns:
            Route type: "direct", "specialized", or "reasoning"
        """
        # Stage 1: Keyword matching
        keyword_route = self._keyword_classify(query)
        if keyword_route:
            logger.debug(f"Keyword match: '{query[:50]}...' → {keyword_route}")
            return keyword_route

        # Stage 2: Embedding similarity
        semantic_route = self._semantic_classify(query)
        logger.debug(f"Semantic match: '{query[:50]}...' → {semantic_route}")
        return semantic_route

    def _keyword_classify(self, query: str) -> RouteType | None:
        """
        Fast keyword-based classification.

        Returns:
            Route type if matched, None if ambiguous
        """
        query_lower = query.lower()

        # Count keyword matches for each route
        scores: Dict[RouteType, int] = {"direct": 0, "specialized": 0, "reasoning": 0}

        for route, keywords in self.KEYWORD_PATTERNS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[route] += 1

        # No matches → use semantic
        if sum(scores.values()) == 0:
            return None

        # Find route with max score
        max_route = max(scores, key=scores.get)
        max_score = scores[max_route]

        # If tie or ambiguous → use semantic
        other_scores = [s for r, s in scores.items() if r != max_route]
        if max_score == max(other_scores):
            return None

        return max_route

    def _semantic_classify(self, query: str) -> RouteType:
        """
        Embedding similarity-based classification.

        Returns:
            Route type (always returns a route, never None)
        """
        # Generate query embedding
        query_emb = embedding_service.embed_query(query)

        # Compute cosine similarity with each route
        similarities: Dict[RouteType, float] = {}

        for route, route_emb in self.route_embeddings.items():
            # Cosine similarity
            sim = self._cosine_similarity(query_emb, route_emb)
            similarities[route] = sim

        # Return route with highest similarity
        best_route = max(similarities, key=similarities.get)
        best_sim = similarities[best_route]

        logger.debug(
            f"Semantic similarities: {similarities} → {best_route} ({best_sim:.3f})"
        )

        # If all similarities are low, default to "reasoning"
        if best_sim < 0.3:
            logger.warning(f"Low similarity ({best_sim:.3f}), defaulting to reasoning")
            return "reasoning"

        return best_route

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# Global singleton instance
semantic_router = SemanticRouter()
