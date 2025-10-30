"""
LLM service wrapper - Phase 10 with llama.cpp

This module provides a singleton llm_service instance that uses
the factory pattern to select between llama.cpp (Phase 10) or vLLM (future).

For Phase 10, llama-cpp-python is used for CPU-optimized local inference.
"""

import os
from app.services.llm_service_factory import get_llm_service

# Create singleton LLM service instance
# This uses environment variable LLM_BACKEND to select the implementation
llm_service = get_llm_service()

print(f"[LLM Service] Initialized with backend: {os.getenv('LLM_BACKEND', 'llama_cpp')}")
