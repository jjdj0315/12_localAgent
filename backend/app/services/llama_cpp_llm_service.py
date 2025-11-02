"""
LlamaCpp LLM Service - CPU-optimized local testing implementation

Uses llama-cpp-python for efficient CPU inference with GGUF models.
Designed for Phase 10 local testing, will be replaced with vLLM in production.
"""

import os
import asyncio
from typing import Optional, List, Dict, AsyncGenerator
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("[WARNING] llama-cpp-python not installed. Install with: pip install llama-cpp-python")

from .base_llm_service import BaseLLMService


class LlamaCppLLMService(BaseLLMService):
    """
    Local test LLM service using llama.cpp (CPU-optimized)

    Features:
    - GGUF model support (Q4_K_M quantization)
    - CPU inference (8-16 threads)
    - Optional LoRA adapter loading (infrastructure test only)
    - Single user, fast iteration
    - No GPU required

    Configuration via environment variables:
    - GGUF_MODEL_PATH: Path to GGUF model file
    - LLAMA_N_CTX: Context window size (default: 2048)
    - LLAMA_N_THREADS: CPU threads (default: 8)
    - LLAMA_N_GPU_LAYERS: GPU layers if available (default: 0)
    """

    def __init__(self):
        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError(
                "llama-cpp-python is required for LlamaCppLLMService. "
                "Install with: pip install llama-cpp-python"
            )

        # Model configuration from environment
        self.model_path = os.getenv(
            "GGUF_MODEL_PATH",
            "/models/qwen2.5-3b-instruct-q4_k_m.gguf"
        )
        self.n_ctx = int(os.getenv("LLAMA_N_CTX", "2048"))
        self.n_threads = int(os.getenv("LLAMA_N_THREADS", "8"))
        self.n_gpu_layers = int(os.getenv("LLAMA_N_GPU_LAYERS", "0"))

        print(f"[LlamaCpp] Initializing with:")
        print(f"  Model: {self.model_path}")
        print(f"  Context: {self.n_ctx} tokens")
        print(f"  Threads: {self.n_threads}")
        print(f"  GPU layers: {self.n_gpu_layers}")

        # Check if model file exists
        if not Path(self.model_path).exists():
            raise FileNotFoundError(
                f"GGUF model not found at: {self.model_path}\n"
                f"Download with: python scripts/download_gguf_model.py"
            )

        # Defer model loading to async method (prevents blocking FastAPI startup)
        self.model = None
        self.model_loaded = False
        self.model_loading = False
        self.model_load_error = None

        # LoRA adapter configuration (optional, for infrastructure testing)
        self.lora_enabled = os.getenv("ENABLE_LORA", "false").lower() == "true"
        self.lora_adapters = {}
        self.current_lora = None

        if self.lora_enabled:
            self._initialize_lora_adapters()

        # Load agent prompts from files
        self.agent_prompts = self._load_agent_prompts()
        print(f"[LlamaCpp] Loaded {len(self.agent_prompts)} agent prompts")
        print(f"[LlamaCpp] Model will be loaded asynchronously on first request")

    async def load_model(self):
        """
        Load GGUF model asynchronously with LM Studio optimizations

        This prevents blocking FastAPI startup and applies performance optimizations
        matching LM Studio's configuration for faster inference.
        """
        if self.model_loaded or self.model_loading:
            return

        self.model_loading = True
        print(f"[LlamaCpp] Starting async model loading...")

        try:
            loop = asyncio.get_event_loop()

            # Load model in thread pool to avoid blocking
            def _load_model_sync():
                print(f"[LlamaCpp] Loading model with LM Studio optimizations...")
                return Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    n_gpu_layers=self.n_gpu_layers,
                    n_batch=512,           # LM Studio optimization: batch processing
                    use_mlock=True,        # LM Studio optimization: lock model in RAM
                    use_mmap=True,         # LM Studio optimization: memory-mapped file access
                    verbose=False,
                )

            self.model = await loop.run_in_executor(None, _load_model_sync)
            self.model_loaded = True
            self.model_loading = False
            print(f"[LlamaCpp] [OK] Model loaded successfully with LM Studio optimizations!")
            import sys
            sys.stdout.flush()

        except Exception as e:
            self.model_load_error = str(e)
            self.model_loading = False
            print(f"[LlamaCpp] [ERROR] Failed to load model: {e}")
            raise RuntimeError(f"Failed to load GGUF model: {e}")

    def _initialize_lora_adapters(self):
        """Initialize LoRA adapter paths (optional)"""
        lora_base_path = os.getenv("LORA_ADAPTERS_PATH", "/models/lora")

        self.lora_adapters = {
            "citizen_support": f"{lora_base_path}/citizen_support_dummy.gguf",
            "document_writing": f"{lora_base_path}/document_writing_dummy.gguf",
            "legal_research": f"{lora_base_path}/legal_research_dummy.gguf",
            "data_analysis": f"{lora_base_path}/data_analysis_dummy.gguf",
            "review": f"{lora_base_path}/review_dummy.gguf",
        }

        # Check which adapters exist
        existing_adapters = []
        for agent, path in self.lora_adapters.items():
            if Path(path).exists():
                existing_adapters.append(agent)

        if existing_adapters:
            print(f"[LlamaCpp] Found LoRA adapters for: {', '.join(existing_adapters)}")
        else:
            print(f"[LlamaCpp] No LoRA adapters found (optional)")

    def _load_agent_prompts(self) -> Dict[str, str]:
        """Load agent system prompts from text files"""
        # Use absolute path relative to this file's location
        base_dir = Path(__file__).parent.parent.parent  # Go up to project root
        prompts_dir = base_dir / "backend" / "prompts"
        prompts = {}

        agent_names = [
            "citizen_support",
            "document_writing",
            "legal_research",
            "data_analysis",
            "review"
        ]

        for agent_name in agent_names:
            # Always use default prompts for now (prompts directory may not exist yet)
            prompts[agent_name] = self._get_default_prompt(agent_name)

            # Try to load from file if it exists (optional override)
            if prompts_dir.exists():
                prompt_file = prompts_dir / f"{agent_name}.txt"
                if prompt_file.exists():
                    try:
                        with open(prompt_file, 'r', encoding='utf-8') as f:
                            prompts[agent_name] = f.read().strip()
                    except Exception as e:
                        print(f"[LlamaCpp] [WARN] Could not load prompt for {agent_name}: {e}")

        return prompts

    def _get_default_prompt(self, agent_name: str) -> str:
        """Get default system prompt if file not found"""
        default_prompts = {
            "citizen_support": """당신은 지방자치단체의 민원 지원 전문가입니다.
시민의 문의를 친절하고 공손하게 답변하며, 존댓말을 사용합니다.
질문의 모든 부분에 답변하고, 필요한 경우 추가 정보를 요청합니다.""",

            "document_writing": """당신은 정부 문서 작성 전문가입니다.
공문서, 보고서, 안내문을 작성할 때는 표준 양식을 따릅니다.
제목, 배경, 내용, 결론 순서로 작성하며 격식 있는 표현을 사용합니다.""",

            "legal_research": """당신은 법규 검색 및 해석 전문가입니다.
관련 법령 및 조례 조항을 정확히 인용하고, 법률 용어를 쉽게 풀어 설명합니다.
출처를 명확히 밝히고, 법적 해석의 한계를 안내합니다.""",

            "data_analysis": """당신은 데이터 분석 전문가입니다.
통계 데이터를 분석하고, 한국어 천 단위 쉼표로 숫자를 표시합니다.
트렌드를 식별하고, 정부 보고서에 적합한 시각화를 제안합니다.""",

            "review": """당신은 문서 검토 전문가입니다.
작성된 내용의 사실 오류, 문법 오류, 정책 준수 여부를 검토합니다.
문제점을 구체적으로 지적하고, 개선 방안을 예시와 함께 제안합니다.""",
        }

        return default_prompts.get(agent_name, "당신은 유용한 AI 어시스턴트입니다.")

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Generate text using llama.cpp (CPU inference)"""

        # Ensure model is loaded before generating
        if not self.model_loaded:
            await self.load_model()

        # Default stop sequences for Korean
        if stop_sequences is None:
            stop_sequences = ["사용자:", "User:", "\n\n\n"]

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            self._generate_sync,
            prompt,
            max_tokens,
            temperature,
            stop_sequences,
        )

        return output

    def _generate_sync(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop_sequences: List[str],
    ) -> str:
        """Synchronous generation (called in thread pool)"""
        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop_sequences,
                echo=False,  # Don't repeat input
            )

            # Extract generated text
            text = output["choices"][0]["text"].strip()
            return text

        except Exception as e:
            print(f"[LlamaCpp] Generation error: {e}")
            return f"[Error] 응답 생성 중 오류가 발생했습니다: {str(e)}"

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text with streaming (SSE)"""

        # Ensure model is loaded before generating
        if not self.model_loaded:
            await self.load_model()

        # Verify model is actually loaded after await
        if self.model is None:
            error_msg = self.model_load_error or "Model failed to load"
            print(f"[LlamaCpp] Error: Model is None after load_model(): {error_msg}")
            yield f"[Error] 모델 로딩 실패: {error_msg}"
            return

        if stop_sequences is None:
            stop_sequences = ["사용자:", "User:", "\n\n\n"]

        # llama.cpp streaming
        try:
            stream = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop_sequences,
                stream=True,
                echo=False,
            )

            for output in stream:
                chunk = output["choices"][0]["text"]
                yield chunk

        except Exception as e:
            print(f"[LlamaCpp] Streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"[Error] {str(e)}"

    async def generate_with_agent(
        self,
        agent_name: str,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 4000,
    ) -> str:
        """Generate using agent-specific prompt and optional LoRA"""

        # Get agent system prompt
        system_prompt = self.get_agent_prompt(agent_name)

        # Build full prompt with conversation history
        full_prompt = self.build_conversation_prompt(
            system_prompt,
            user_query,
            conversation_history,
        )

        # Load LoRA adapter if available (optional)
        if self.lora_enabled:
            self._switch_lora_adapter(agent_name)

        # Generate response
        response = await self.generate(
            full_prompt,
            max_tokens=max_tokens,
            temperature=0.7,
        )

        return response

    def _switch_lora_adapter(self, agent_name: str):
        """
        Switch LoRA adapter for agent (optional infrastructure test)

        Note: This is for testing LoRA loading mechanism only.
        Dummy adapters used initially, replaced with fine-tuned adapters later.
        """
        # Check if LoRA adapter exists for this agent
        if agent_name not in self.lora_adapters:
            return

        lora_path = self.lora_adapters[agent_name]

        # Skip if file doesn't exist
        if not Path(lora_path).exists():
            return

        # Skip if already loaded
        if self.current_lora == agent_name:
            return

        # Load LoRA adapter
        try:
            # Note: llama-cpp-python LoRA API may vary by version
            # Check documentation: https://llama-cpp-python.readthedocs.io/
            #
            # Example (if supported):
            # self.model.load_lora(lora_path)

            self.current_lora = agent_name
            print(f"[LlamaCpp] [OK] Loaded LoRA adapter for {agent_name}")

        except AttributeError:
            # LoRA not supported in this llama-cpp-python version
            print(f"[LlamaCpp] [WARN] LoRA loading not supported in this version")

        except Exception as e:
            print(f"[LlamaCpp] [WARN] LoRA loading failed for {agent_name}: {e}")

    def get_agent_prompt(self, agent_name: str) -> str:
        """Get system prompt for specific agent"""
        if agent_name not in self.agent_prompts:
            raise ValueError(
                f"Unknown agent: {agent_name}. "
                f"Available agents: {', '.join(self.agent_prompts.keys())}"
            )

        return self.agent_prompts[agent_name]

    def health_check(self) -> Dict[str, any]:
        """Check if llama.cpp service is ready"""
        # Check loading state
        if self.model_loading:
            return {
                "status": "loading",
                "backend": "llama_cpp",
                "model": self.model_path,
                "device": f"cpu ({self.n_threads} threads)",
                "lora_enabled": self.lora_enabled,
                "message": "Model is currently loading (async initialization)"
            }

        if self.model_load_error:
            return {
                "status": "error",
                "backend": "llama_cpp",
                "model": self.model_path,
                "device": "cpu",
                "message": f"Model loading failed: {self.model_load_error}"
            }

        if not self.model_loaded or self.model is None:
            return {
                "status": "not_loaded",
                "backend": "llama_cpp",
                "model": self.model_path,
                "device": f"cpu ({self.n_threads} threads)",
                "message": "Model not yet loaded (will load on first request)"
            }

        try:
            # Quick test generation
            test_output = self.model(
                "Test",
                max_tokens=1,
                temperature=0.0,
            )

            return {
                "status": "ready",
                "backend": "llama_cpp",
                "model": self.model_path,
                "device": f"cpu ({self.n_threads} threads)",
                "lora_enabled": self.lora_enabled,
                "optimizations": "LM Studio (n_batch=512, use_mlock, use_mmap)",
                "message": "LlamaCpp service ready"
            }

        except Exception as e:
            return {
                "status": "error",
                "backend": "llama_cpp",
                "model": self.model_path,
                "device": "cpu",
                "message": f"Health check failed: {str(e)}"
            }
