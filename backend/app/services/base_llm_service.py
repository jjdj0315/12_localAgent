"""
Abstract base class for LLM services

Provides unified interface for different LLM backends:
- llama.cpp (local testing, CPU-optimized)
- vLLM (production, GPU-optimized, multi-user)

This allows switching between implementations without changing agent code.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, AsyncGenerator


class BaseLLMService(ABC):
    """
    Abstract LLM service interface

    Design goals:
    1. Environment-agnostic: Works with llama.cpp or vLLM
    2. Agent-friendly: Simplified API for multi-agent system
    3. Context-aware: Supports conversation history
    4. Extensible: Easy to add new backends
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text response from prompt

        Args:
            prompt: Input text (can include system prompt + user query)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            stop_sequences: List of strings that stop generation

        Returns:
            Generated text (string)
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text response with streaming (SSE)

        Args:
            prompt: Input text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop_sequences: List of strings that stop generation

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    async def generate_with_agent(
        self,
        agent_name: str,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 4000,
    ) -> str:
        """
        Generate response using agent-specific configuration

        This method:
        1. Loads agent-specific system prompt
        2. Optionally loads agent-specific LoRA adapter (if configured)
        3. Builds full prompt with conversation history
        4. Generates response

        Args:
            agent_name: Name of agent (e.g., "citizen_support", "document_writing")
            user_query: User's question or request
            conversation_history: Previous messages [{"role": "user/assistant", "content": "..."}]
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text
        """
        pass

    @abstractmethod
    def get_agent_prompt(self, agent_name: str) -> str:
        """
        Get system prompt for specific agent

        Args:
            agent_name: Name of agent

        Returns:
            System prompt text (Korean)

        Raises:
            ValueError: If agent_name not found
        """
        pass

    def build_conversation_prompt(
        self,
        system_prompt: str,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Build full prompt from system prompt, history, and user query

        Format:
        ```
        {system_prompt}

        [이전 대화 내역]
        사용자: {previous user message}
        답변: {previous assistant message}
        ...

        사용자: {current user query}
        답변:
        ```

        Args:
            system_prompt: Agent's system instructions
            user_query: Current user question
            conversation_history: Previous messages (optional)

        Returns:
            Formatted prompt string
        """
        prompt_parts = [system_prompt, ""]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages max
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "user":
                    prompt_parts.append(f"사용자: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"답변: {content}")

        # Add current user query
        prompt_parts.append(f"사용자: {user_query}")
        prompt_parts.append("답변:")

        return "\n".join(prompt_parts)

    @abstractmethod
    def health_check(self) -> Dict[str, any]:
        """
        Check if LLM service is ready

        Returns:
            Dict with health status:
            {
                "status": "ready" | "loading" | "error",
                "backend": "llama_cpp" | "vllm",
                "model": "model_name",
                "device": "cpu" | "cuda",
                "message": "optional status message"
            }
        """
        pass
