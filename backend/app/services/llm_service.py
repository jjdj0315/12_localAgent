"""LLM service for interacting with Ollama server"""

import os
import time
from typing import AsyncGenerator, List, Optional, Tuple

import httpx

from app.core.config import settings


class LLMService:
    """Service for LLM inference"""

    def __init__(self):
        self.base_url = settings.LLM_SERVICE_URL
        self.max_length = settings.MAX_RESPONSE_LENGTH
        self.model = os.getenv("OLLAMA_MODEL", "tinyllama")

    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[dict]] = None,
        document_context: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Tuple[str, int]:
        """
        Generate LLM response (non-streaming) using Ollama.

        Args:
            prompt: User query
            conversation_history: Previous messages for context
            document_context: Extracted text from documents
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (Generated response text, processing time in ms)
        """
        start_time = time.time()

        # Build full prompt with context
        full_prompt = self._build_prompt(prompt, conversation_history, document_context)

        # Call Ollama API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                    }
                },
            )
            response.raise_for_status()
            result = response.json()

        # Extract response text from Ollama format
        text = result.get("response", "")
        if len(text) > self.max_length:
            text = text[: self.max_length]

        end_time = time.time()
        processing_time_ms = int((end_time - start_time) * 1000)

        return text, processing_time_ms

    async def generate_stream(
        self,
        prompt: str,
        conversation_history: Optional[List[dict]] = None,
        document_context: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """
        Generate LLM response with streaming using Ollama.

        Args:
            prompt: User query
            conversation_history: Previous messages for context
            document_context: Extracted text from documents
            max_tokens: Maximum tokens to generate

        Yields:
            Generated tokens
        """
        import json

        full_prompt = self._build_prompt(prompt, conversation_history, document_context)

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                    }
                },
            ) as response:
                response.raise_for_status()
                char_count = 0

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")

                            if token:
                                # Check character limit
                                if char_count + len(token) > self.max_length:
                                    remaining = self.max_length - char_count
                                    if remaining > 0:
                                        yield token[:remaining]
                                    break

                                yield token
                                char_count += len(token)

                            # Check if generation is done
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

    def _build_prompt(
        self,
        current_message: str,
        history: Optional[List[dict]] = None,
        document_context: Optional[str] = None,
    ) -> str:
        """
        Build full prompt with conversation history and document context.

        Args:
            current_message: Current user message
            history: List of previous messages [{"role": "user|assistant", "content": "..."}]
            document_context: Extracted text from documents

        Returns:
            Full prompt string
        """
        prompt_parts = []

        # Add document context if provided
        if document_context:
            # Limit document context to prevent exceeding token limits
            max_doc_chars = 8000  # Approximately 2000 tokens
            if len(document_context) > max_doc_chars:
                document_context = document_context[:max_doc_chars] + "\n...(문서 내용이 잘렸습니다)"

            prompt_parts.append("=== 참고 문서 ===")
            prompt_parts.append(document_context)
            prompt_parts.append("=== 참고 문서 끝 ===\n")

        # Add conversation history
        if history:
            for msg in history[-10:]:  # Last 10 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt_parts.append(f"User: {content}")
                else:
                    prompt_parts.append(f"Assistant: {content}")

        # Add current message
        prompt_parts.append(f"User: {current_message}")

        # Add instruction for document-based queries
        if document_context:
            prompt_parts.append("Assistant: (위 참고 문서의 내용을 바탕으로 답변드리겠습니다)")
        else:
            prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)


# Singleton instance
llm_service = LLMService()
