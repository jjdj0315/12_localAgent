"""LLM service for interacting with vLLM server"""

from typing import AsyncGenerator, List, Optional

import httpx

from app.core.config import settings


class LLMService:
    """Service for LLM inference"""

    def __init__(self):
        self.base_url = settings.LLM_SERVICE_URL
        self.max_length = settings.MAX_RESPONSE_LENGTH

    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[dict]] = None,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate LLM response (non-streaming).

        Args:
            prompt: User query
            conversation_history: Previous messages for context
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text
        """
        # Build full prompt with context
        full_prompt = self._build_prompt(prompt, conversation_history)

        # Call vLLM service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={"prompt": full_prompt, "max_tokens": max_tokens},
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

        # Limit response length
        text = result.get("text", "")
        if len(text) > self.max_length:
            text = text[: self.max_length]

        return text

    async def generate_stream(
        self,
        prompt: str,
        conversation_history: Optional[List[dict]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """
        Generate LLM response with streaming (SSE).

        Args:
            prompt: User query
            conversation_history: Previous messages for context
            max_tokens: Maximum tokens to generate

        Yields:
            Generated tokens
        """
        full_prompt = self._build_prompt(prompt, conversation_history)

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/generate_stream",
                json={"prompt": full_prompt, "max_tokens": max_tokens},
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                char_count = 0

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        token = line[6:]  # Remove "data: " prefix

                        # Check character limit
                        if char_count + len(token) > self.max_length:
                            remaining = self.max_length - char_count
                            if remaining > 0:
                                yield token[:remaining]
                            break

                        yield token
                        char_count += len(token)

    def _build_prompt(
        self, current_message: str, history: Optional[List[dict]] = None
    ) -> str:
        """
        Build full prompt with conversation history.

        Args:
            current_message: Current user message
            history: List of previous messages [{"role": "user|assistant", "content": "..."}]

        Returns:
            Full prompt string
        """
        if not history:
            return current_message

        # Build conversation context
        prompt_parts = []
        for msg in history[-10:]:  # Last 10 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"User: {content}")
            else:
                prompt_parts.append(f"Assistant: {content}")

        # Add current message
        prompt_parts.append(f"User: {current_message}")
        prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)


# Singleton instance
llm_service = LLMService()
