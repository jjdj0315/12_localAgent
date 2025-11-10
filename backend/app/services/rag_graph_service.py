"""
RAG (Retrieval-Augmented Generation) Pipeline with LangGraph

Implements document retrieval and generation pipeline using StateGraph for:
- Query preprocessing and expansion
- Document retrieval from vector store
- Result reranking (optional)
- Context generation for LLM
- Response formatting

This replaces the manual pipeline in document_search.py with a declarative graph structure.
"""
from typing import TypedDict, List, Dict, Any, Optional
from uuid import UUID
import logging

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[WARNING] LangGraph not installed. Install with: pip install langgraph langchain-core")

from sentence_transformers import SentenceTransformer, util
import torch
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


class RAGState(TypedDict):
    """
    State for RAG pipeline graph

    Tracks the complete lifecycle of retrieval-augmented generation:
    - Input: query and conversation context
    - Processing: embeddings, retrieval, reranking
    - Output: formatted results with sources
    """
    # Input
    conversation_id: UUID
    query: str
    top_k: int

    # Query Processing
    processed_query: str
    query_embedding: Optional[Any]  # torch.Tensor

    # Retrieval
    documents: List[Document]
    chunks: List[str]
    chunk_embeddings: Optional[Any]  # torch.Tensor

    # Results
    raw_results: List[Dict[str, Any]]
    reranked_results: List[Dict[str, Any]]

    # Output
    formatted_output: str

    # Metadata
    execution_log: List[Dict[str, Any]]
    error: Optional[str]


class RAGGraphService:
    """
    RAG Pipeline using LangGraph StateGraph

    Provides a declarative, modular approach to retrieval-augmented generation:
    - Easy to debug (node-level inspection)
    - Easy to extend (add reranking, query expansion, etc.)
    - Clear flow visualization
    """

    def __init__(
        self,
        db: Session,
        embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Initialize RAG graph service

        Args:
            db: Database session
            embedding_model_name: Sentence transformer model for embeddings
        """
        self.db = db
        self.model = SentenceTransformer(embedding_model_name)

        if LANGGRAPH_AVAILABLE:
            self.graph = self._build_workflow()
        else:
            self.graph = None
            logger.warning("LangGraph not available, falling back to manual pipeline")

    def _build_workflow(self) -> StateGraph:
        """
        Build RAG workflow graph

        Graph Structure:
        preprocess → retrieve → rerank → format → END

        Each node is independent and testable.
        """
        if not LANGGRAPH_AVAILABLE:
            return None

        workflow = StateGraph(RAGState)

        # Add nodes
        workflow.add_node("preprocess", self._preprocess_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("rerank", self._rerank_node)
        workflow.add_node("format", self._format_node)

        # Define edges
        workflow.set_entry_point("preprocess")
        workflow.add_edge("preprocess", "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "format")
        workflow.add_edge("format", END)

        return workflow.compile()

    def search(
        self,
        conversation_id: UUID,
        query: str,
        top_k: int = 3
    ) -> str:
        """
        Execute RAG search pipeline

        Args:
            conversation_id: Current conversation ID
            query: Search query
            top_k: Number of results to return

        Returns:
            Formatted search results with source references

        Raises:
            ValueError: If conversation not found or no documents available
        """
        if not self.graph:
            # Fallback to manual pipeline if LangGraph unavailable
            return self._manual_search(conversation_id, query, top_k)

        # Initialize state
        initial_state: RAGState = {
            "conversation_id": conversation_id,
            "query": query,
            "top_k": top_k,
            "processed_query": "",
            "query_embedding": None,
            "documents": [],
            "chunks": [],
            "chunk_embeddings": None,
            "raw_results": [],
            "reranked_results": [],
            "formatted_output": "",
            "execution_log": [],
            "error": None
        }

        try:
            # Execute graph with streaming (Phase 1.1: invoke → stream)
            final_state = None

            # Stream graph execution (Phase 1.2: Add "messages" for LLM token streaming)
            for chunk in self.graph.stream(initial_state, stream_mode=["updates", "messages"]):
                # chunk is a tuple: (node_name, state_updates)
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    node_name, state_updates = chunk

                    # Initialize final_state on first chunk
                    if final_state is None:
                        final_state = initial_state.copy()

                    # Update state with new data
                    final_state.update(state_updates)

            # Ensure we have a final state
            if final_state is None:
                raise RuntimeError("Graph execution completed without producing any state")

            if final_state.get("error"):
                raise ValueError(final_state["error"])

            return final_state["formatted_output"]

        except Exception as e:
            logger.error(f"RAG graph execution failed: {e}")
            raise

    def _preprocess_node(self, state: RAGState) -> Dict[str, Any]:
        """
        Node 1: Preprocess query

        - Validate conversation exists
        - Load documents
        - Clean/normalize query (future: query expansion)
        """
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == state["conversation_id"]
            ).first()

            if not conversation:
                return {
                    "error": f"대화를 찾을 수 없습니다: {state['conversation_id']}"
                }

            # Load documents
            documents = self.db.query(Document).filter(
                Document.conversation_id == state["conversation_id"]
            ).all()

            if not documents:
                return {
                    "formatted_output": "검색 가능한 문서가 없습니다. 먼저 문서를 업로드해주세요.",
                    "error": "no_documents"
                }

            # Query preprocessing (currently just trim, can add expansion later)
            processed_query = state["query"].strip()

            # Encode query
            query_embedding = self.model.encode(processed_query, convert_to_tensor=True)

            return {
                "documents": documents,
                "processed_query": processed_query,
                "query_embedding": query_embedding,
                "execution_log": [{"node": "preprocess", "status": "completed"}]
            }

        except Exception as e:
            logger.error(f"Preprocess node failed: {e}")
            return {"error": str(e)}

    def _retrieve_node(self, state: RAGState) -> Dict[str, Any]:
        """
        Node 2: Retrieve relevant chunks

        - Chunk documents
        - Compute embeddings
        - Calculate similarity scores
        - Return top-K chunks
        """
        try:
            if state.get("error"):
                return {}  # Skip if error occurred

            query_embedding = state["query_embedding"]
            documents = state["documents"]
            top_k = state["top_k"]

            results = []

            for doc in documents:
                if not doc.extracted_text or not doc.extracted_text.strip():
                    continue

                # Chunk document
                chunks = self._chunk_text(doc.extracted_text)

                # Encode chunks
                chunk_embeddings = self.model.encode(chunks, convert_to_tensor=True)

                # Compute similarities
                similarities = util.cos_sim(query_embedding, chunk_embeddings)[0]

                # Get top chunks for this document
                top_indices = torch.topk(similarities, k=min(top_k, len(chunks))).indices.tolist()

                for idx in top_indices:
                    score = similarities[idx].item()

                    # Filter by minimum similarity threshold
                    if score > 0.3:
                        results.append({
                            "document_id": doc.id,
                            "document_name": doc.filename,
                            "chunk": chunks[idx],
                            "score": score,
                        })

            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)

            return {
                "raw_results": results[:top_k * 2],  # Keep extra for reranking
                "execution_log": state["execution_log"] + [
                    {"node": "retrieve", "status": "completed", "results_count": len(results)}
                ]
            }

        except Exception as e:
            logger.error(f"Retrieve node failed: {e}")
            return {"error": str(e)}

    def _rerank_node(self, state: RAGState) -> Dict[str, Any]:
        """
        Node 3: Rerank results (optional refinement)

        Currently just selects top-K from raw results.
        Future: Can add cross-encoder reranking, diversity scoring, etc.
        """
        try:
            if state.get("error"):
                return {}

            raw_results = state["raw_results"]
            top_k = state["top_k"]

            # Simple reranking: just take top-K
            # Future: Add cross-encoder, MMR (Maximal Marginal Relevance), etc.
            reranked_results = raw_results[:top_k]

            if not reranked_results:
                return {
                    "formatted_output": f"'{state['processed_query']}'에 대한 검색 결과가 없습니다. 다른 키워드로 시도해보세요.",
                    "reranked_results": [],
                    "execution_log": state["execution_log"] + [
                        {"node": "rerank", "status": "completed", "final_count": 0}
                    ]
                }

            return {
                "reranked_results": reranked_results,
                "execution_log": state["execution_log"] + [
                    {"node": "rerank", "status": "completed", "final_count": len(reranked_results)}
                ]
            }

        except Exception as e:
            logger.error(f"Rerank node failed: {e}")
            return {"error": str(e)}

    def _format_node(self, state: RAGState) -> Dict[str, Any]:
        """
        Node 4: Format results for display

        - Format chunks with source references
        - Add metadata (scores, document names)
        - Generate user-friendly output
        """
        try:
            if state.get("error") == "no_documents":
                return {}  # Already have formatted output

            if state.get("error"):
                return {}

            results = state["reranked_results"]
            query = state["processed_query"]

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

            return {
                "formatted_output": "\n".join(output),
                "execution_log": state["execution_log"] + [
                    {"node": "format", "status": "completed"}
                ]
            }

        except Exception as e:
            logger.error(f"Format node failed: {e}")
            return {"error": str(e)}

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

    def _manual_search(
        self,
        conversation_id: UUID,
        query: str,
        top_k: int = 3
    ) -> str:
        """
        Fallback manual search if LangGraph unavailable

        Uses the same logic as the graph but in sequential function calls.
        """
        # This is the original implementation from document_search.py
        # Kept for backward compatibility
        raise NotImplementedError("Manual fallback not yet implemented. Install LangGraph.")
