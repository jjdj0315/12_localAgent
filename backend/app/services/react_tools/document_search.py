"""
Document Search Tool

Searches uploaded documents using vector similarity and returns snippets with source references.
Per FR-061.1: Vector similarity on uploaded docs, return snippets with source refs.
"""
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer, util
import torch
from uuid import UUID

from app.models.document import Document
from app.models.conversation import Conversation


class DocumentSearchTool:
    """
    Document search tool for ReAct agent

    Searches documents uploaded to the current conversation using semantic similarity.
    Returns relevant snippets with source references.
    """

    def __init__(self, db: Session, embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize document search tool

        Args:
            db: Database session
            embedding_model_name: Sentence transformer model for embeddings
        """
        self.db = db
        self.model = SentenceTransformer(embedding_model_name)

    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """Get tool definition for ReAct agent"""
        return {
            "name": "document_search",
            "display_name": "문서 검색",
            "description": "대화에 업로드된 문서에서 관련 내용을 검색합니다. 법규, 조례, 매뉴얼 등을 찾을 때 사용하세요.",
            "category": "document_search",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 내용 (예: '주민등록 신청 절차', '예산 편성 기준')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "반환할 최대 결과 수 (기본값: 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            },
            "timeout_seconds": 30,
            "examples": [
                {
                    "query": "주민등록 신청 절차",
                    "description": "주민등록 관련 문서에서 신청 절차를 검색합니다."
                },
                {
                    "query": "예산 편성 기준",
                    "top_k": 5,
                    "description": "예산 관련 문서에서 편성 기준을 검색합니다."
                }
            ]
        }

    def execute(
        self,
        conversation_id: UUID,
        query: str,
        top_k: int = 3,
        **kwargs
    ) -> str:
        """
        Execute document search

        Args:
            conversation_id: Current conversation ID
            query: Search query
            top_k: Number of results to return
            **kwargs: Additional parameters (ignored)

        Returns:
            Formatted search results with source references

        Raises:
            ValueError: If conversation not found or no documents available
        """
        # Validate conversation exists
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError(f"대화를 찾을 수 없습니다: {conversation_id}")

        # Get documents for this conversation
        documents = self.db.query(Document).filter(
            Document.conversation_id == conversation_id
        ).all()

        if not documents:
            return "검색 가능한 문서가 없습니다. 먼저 문서를 업로드해주세요."

        # Perform semantic search
        results = self._semantic_search(query, documents, top_k)

        if not results:
            return f"'{query}'에 대한 검색 결과가 없습니다. 다른 키워드로 시도해보세요."

        # Format results
        return self._format_results(results, query)

    def _semantic_search(
        self,
        query: str,
        documents: List[Document],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on documents

        Args:
            query: Search query
            documents: List of documents to search
            top_k: Number of results to return

        Returns:
            List of search results with scores and source info
        """
        # Encode query
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        results = []

        for doc in documents:
            if not doc.extracted_text or not doc.extracted_text.strip():
                continue

            # Split document into chunks (simple chunking by paragraphs)
            chunks = self._chunk_text(doc.extracted_text, chunk_size=500, overlap=50)

            # Encode all chunks
            chunk_embeddings = self.model.encode(chunks, convert_to_tensor=True)

            # Compute similarities
            similarities = util.cos_sim(query_embedding, chunk_embeddings)[0]

            # Get top chunks for this document
            top_indices = torch.topk(similarities, k=min(top_k, len(chunks))).indices.tolist()

            for idx in top_indices:
                score = similarities[idx].item()

                # Only include results with similarity > 0.3
                if score > 0.3:
                    results.append({
                        "document_id": doc.id,
                        "document_name": doc.original_filename,
                        "chunk": chunks[idx],
                        "score": score,
                    })

        # Sort all results by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        # Split by paragraphs first
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Start new chunk with overlap
                    current_chunk = current_chunk[-overlap:] + " " + para if overlap > 0 else para
                else:
                    # Paragraph itself is too long, split it
                    words = para.split()
                    for i in range(0, len(words), chunk_size // 10):
                        chunk = " ".join(words[i:i + chunk_size // 10])
                        chunks.append(chunk)
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Format search results for display

        Args:
            results: List of search results
            query: Original query

        Returns:
            Formatted string with results and source references
        """
        output = [f"'{query}' 검색 결과 ({len(results)}개):\n"]

        for i, result in enumerate(results, 1):
            doc_name = result["document_name"]
            chunk = result["chunk"]
            score = result["score"]

            # Truncate long chunks
            if len(chunk) > 300:
                chunk = chunk[:300] + "..."

            output.append(f"\n[{i}] 문서: {doc_name} (관련도: {score:.2f})")
            output.append(f"내용: {chunk}")
            output.append("")

        output.append("\n💡 출처: 위 내용은 업로드된 문서에서 검색한 결과입니다.")

        return "\n".join(output)

    def validate_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate input parameters

        Args:
            parameters: Input parameters

        Returns:
            (is_valid, error_message)
        """
        if "query" not in parameters:
            return False, "검색어(query)가 필요합니다."

        query = parameters["query"]
        if not isinstance(query, str) or not query.strip():
            return False, "검색어는 비어있지 않은 문자열이어야 합니다."

        if "top_k" in parameters:
            top_k = parameters["top_k"]
            if not isinstance(top_k, int) or top_k < 1 or top_k > 10:
                return False, "top_k는 1~10 사이의 정수여야 합니다."

        return True, ""
