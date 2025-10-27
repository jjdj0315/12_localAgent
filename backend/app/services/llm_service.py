"""LLM service for interacting with Hugging Face models"""

import os
import time
from typing import AsyncGenerator, List, Optional, Tuple
import asyncio
from threading import Thread

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
    BitsAndBytesConfig,
)

from app.core.config import settings


class LLMService:
    """Service for LLM inference using Hugging Face transformers"""

    def __init__(self):
        self.max_length = settings.MAX_RESPONSE_LENGTH
        self.model_name = os.getenv("HF_MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"[LLM] Initializing model: {self.model_name}")
        print(f"[LLM] Device: {self.device}")

        # 4-bit quantization configuration for lightweight deployment
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )

        print(f"[LLM] Using 4-bit quantization for memory efficiency")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Load model with 4-bit quantization
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                low_cpu_mem_usage=True,
            )
            print(f"[LLM] Model loaded with 4-bit quantization")
        except Exception as e:
            print(f"[LLM] 4-bit quantization failed, falling back to FP32: {e}")
            # Fallback to non-quantized for CPU
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
            )
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            print(f"[LLM] Model loaded without quantization")

        print(f"[LLM] Model loaded successfully")

    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[dict]] = None,
        document_context: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Tuple[str, int]:
        """
        Generate LLM response (non-streaming) using Hugging Face transformers.

        Args:
            prompt: User query
            conversation_history: Previous messages for context
            document_context: Extracted text from documents
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (Generated response text, processing time in ms)
        """
        start_time = time.time()

        # Build messages for chat template
        messages = self._build_messages(prompt, conversation_history, document_context)

        # Apply chat template
        input_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=2048,  # Limit input length
        ).to(self.device)

        # Generate
        max_new_tokens = min(max_tokens, 1024)  # Limit for smaller models

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.5,
                top_p=0.9,
                repetition_penalty=1.1,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode response
        full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the assistant's response
        response_text = self._extract_response(full_output, input_text)

        # Apply length limit
        if len(response_text) > self.max_length:
            response_text = response_text[:self.max_length]

        end_time = time.time()
        processing_time_ms = int((end_time - start_time) * 1000)

        return response_text, processing_time_ms

    async def generate_stream(
        self,
        prompt: str,
        conversation_history: Optional[List[dict]] = None,
        document_context: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """
        Generate LLM response with streaming using Hugging Face transformers.

        Args:
            prompt: User query
            conversation_history: Previous messages for context
            document_context: Extracted text from documents
            max_tokens: Maximum tokens to generate

        Yields:
            Generated tokens
        """
        # Build messages for chat template
        messages = self._build_messages(prompt, conversation_history, document_context)

        # Apply chat template
        input_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        ).to(self.device)

        # Setup streamer
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        # Generation parameters
        max_new_tokens = min(max_tokens, 1024)
        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_new_tokens,
            "temperature": 0.5,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "do_sample": True,
            "pad_token_id": self.tokenizer.eos_token_id,
            "streamer": streamer,
        }

        # Run generation in a separate thread
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        # Stream tokens
        char_count = 0
        for token in streamer:
            if char_count + len(token) > self.max_length:
                remaining = self.max_length - char_count
                if remaining > 0:
                    yield token[:remaining]
                break

            yield token
            char_count += len(token)
            await asyncio.sleep(0)  # Allow other tasks to run

        thread.join()

    def _build_messages(
        self,
        current_message: str,
        history: Optional[List[dict]] = None,
        document_context: Optional[str] = None,
    ) -> List[dict]:
        """
        Build messages list for chat template.

        Args:
            current_message: Current user message
            history: List of previous messages [{"role": "user|assistant", "content": "..."}]
            document_context: Extracted text from documents

        Returns:
            List of messages in chat format
        """
        messages = []

        # Debug: Log conversation context
        if history:
            print(f"[LLM] Loading {len(history)} messages from history (using last 6)")
        else:
            print("[LLM] No history - this is a new conversation")

        # Add comprehensive system message
        system_content = """You are a helpful, respectful, and honest AI assistant. Your goal is to provide accurate, clear, and concise responses.

Key guidelines:
- Always respond in Korean unless the user asks in another language
- If you don't know something, admit it honestly rather than making up information
- Maintain context from previous messages in the conversation
- Be concise but thorough - provide enough detail without being verbose
- If asked about your identity, explain you are an AI assistant here to help
- Remember and reference information the user has shared earlier in the conversation
- Ask clarifying questions when the user's request is ambiguous"""

        if document_context:
            # Limit document context to prevent exceeding token limits
            max_doc_chars = 4000
            if len(document_context) > max_doc_chars:
                document_context = document_context[:max_doc_chars] + "\n...(문서 내용이 잘렸습니다)"

            system_content += f"\n\n참고 문서:\n{document_context}\n\n위 문서의 내용을 바탕으로 답변하세요. 문서에 없는 내용은 추측하지 말고, 문서 기반으로만 답변하세요."

        messages.append({"role": "system", "content": system_content})

        # Add conversation history (last 6 messages)
        if history:
            for msg in history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append({"role": role, "content": content})

        # Add current message
        messages.append({"role": "user", "content": current_message})

        # Debug: Log final messages structure
        print(f"[LLM] Total messages: {len(messages)}")
        print(f"[LLM] Messages preview: {messages[:2]}")

        return messages

    def _extract_response(self, full_output: str, input_text: str) -> str:
        """
        Extract the assistant's response from the full output.

        Args:
            full_output: Full generated text
            input_text: Input text (prompt)

        Returns:
            Extracted response text
        """
        # Try to remove the input prompt from the output
        if full_output.startswith(input_text):
            response = full_output[len(input_text):].strip()
        else:
            # Fallback: just use the full output
            response = full_output.strip()

        return response


# Singleton instance
llm_service = LLMService()
