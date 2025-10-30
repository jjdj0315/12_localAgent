"""
LLM Service Factory - Environment-based LLM backend selection

Provides unified interface for switching between:
- llama.cpp (Phase 10 local testing, CPU-optimized)
- vLLM (Production deployment, GPU-optimized, multi-user)

Environment variable LLM_BACKEND controls which implementation loads.
Agent code remains unchanged across environments.
"""

import os
from typing import Optional

# Load .env file
from dotenv import load_dotenv
load_dotenv()

from .base_llm_service import BaseLLMService


# Singleton instance (lazy initialization)
_llm_service_instance: Optional[BaseLLMService] = None


def get_llm_service() -> BaseLLMService:
    """
    Get LLM service singleton based on environment variable

    Environment Configuration (.env):
        LLM_BACKEND=llama_cpp  # Phase 10 local testing (default)
        LLM_BACKEND=vllm       # Production deployment

    Returns:
        BaseLLMService: Concrete implementation (LlamaCppLLMService or VLLMLLMService)

    Raises:
        ValueError: If LLM_BACKEND has invalid value
        RuntimeError: If service initialization fails

    Example:
        >>> llm = get_llm_service()
        >>> response = await llm.generate("Hello", max_tokens=100)
    """
    global _llm_service_instance

    # Return cached instance if already initialized
    if _llm_service_instance is not None:
        return _llm_service_instance

    # Get backend type from environment
    backend = os.getenv("LLM_BACKEND", "llama_cpp").lower()

    print(f"[LLM Factory] Initializing LLM backend: {backend}")

    # Load appropriate service
    if backend == "vllm":
        try:
            from .vllm_llm_service import VLLMLLMService
            print("[LLM Factory] Loading vLLM service (Production mode)")
            _llm_service_instance = VLLMLLMService()
            print("[LLM Factory] [OK] vLLM service initialized")

        except ImportError as e:
            raise RuntimeError(
                f"vLLM backend not available. Install with: pip install vllm\n"
                f"Error: {e}"
            )

    elif backend == "llama_cpp":
        try:
            from .llama_cpp_llm_service import LlamaCppLLMService
            print("[LLM Factory] Loading llama.cpp service (Test mode)")
            _llm_service_instance = LlamaCppLLMService()
            print("[LLM Factory] [OK] llama.cpp service initialized")

        except ImportError as e:
            raise RuntimeError(
                f"llama-cpp-python not available. Install with: pip install llama-cpp-python\n"
                f"Error: {e}"
            )

    else:
        raise ValueError(
            f"Invalid LLM_BACKEND: '{backend}'. Must be 'llama_cpp' or 'vllm'"
        )

    return _llm_service_instance


def reset_llm_service():
    """
    Reset the singleton instance (for testing purposes)

    This allows tests to switch between backends or reload configuration.
    NOT intended for production use.
    """
    global _llm_service_instance
    _llm_service_instance = None
    print("[LLM Factory] Service instance reset")


def get_current_backend() -> str:
    """
    Get the currently configured LLM backend name

    Returns:
        str: "llama_cpp" or "vllm"
    """
    return os.getenv("LLM_BACKEND", "llama_cpp").lower()


def is_production_mode() -> bool:
    """
    Check if running in production mode (vLLM)

    Returns:
        bool: True if using vLLM, False if using llama.cpp
    """
    return get_current_backend() == "vllm"
