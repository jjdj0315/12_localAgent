"""
Mock LLM Server for Testing

This mock server simulates vLLM responses for local development and testing
without requiring a GPU or actual LLM model.
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import Dict, Any

app = FastAPI(title="Mock LLM Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mock Korean responses for common queries
MOCK_RESPONSES = {
    "공문서": """공문서 작성 시 주의사항은 다음과 같습니다:

1. **형식 준수**: 공문서는 정해진 양식과 형식을 따라야 합니다.
2. **정확성**: 날짜, 이름, 직책 등 모든 정보가 정확해야 합니다.
3. **간결성**: 불필요한 내용 없이 핵심만 간결하게 작성합니다.
4. **예의**: 공손하고 격식 있는 표현을 사용합니다.
5. **법적 효력**: 공문서는 법적 효력이 있으므로 신중하게 작성해야 합니다.

추가로 궁금하신 사항이 있으시면 말씀해 주세요.""",

    "업무": """업무 효율성을 높이는 방법:

1. 우선순위 설정: 중요하고 긴급한 업무부터 처리
2. 시간 관리: 업무 시간을 효율적으로 배분
3. 문서화: 업무 절차와 결과를 체계적으로 기록
4. 협업: 동료들과 원활한 소통과 협력
5. 지속적 학습: 새로운 업무 도구와 방법 습득

더 구체적인 부분에 대해 질문해 주시면 도움을 드리겠습니다.""",

    "default": """안녕하세요! Local LLM 테스트 시스템입니다.

현재 Mock 모드로 실행 중입니다. 실제 환경에서는 Meta-Llama-3-8B 모델이 사용됩니다.

질문하신 내용에 대해 다음과 같이 답변드립니다:
- 이것은 테스트 응답입니다
- 실제 LLM 환경에서는 더 정확하고 상세한 답변을 제공합니다
- 한국어 질의응답이 원활하게 작동합니다

궁금하신 점이 더 있으시면 말씀해 주세요!"""
}


def get_mock_response(prompt: str) -> str:
    """Get appropriate mock response based on prompt"""
    prompt_lower = prompt.lower()

    for keyword, response in MOCK_RESPONSES.items():
        if keyword != "default" and keyword in prompt_lower:
            return response

    return MOCK_RESPONSES["default"]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mock LLM Service",
        "status": "running",
        "mode": "mock",
        "message": "This is a mock LLM service for testing. Real service uses vLLM with Llama-3-8B."
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "llm-mock",
        "model": "mock-llama-3-8b"
    }


@app.post("/generate")
async def generate(request: Dict[str, Any]):
    """
    Generate LLM response (non-streaming)

    Request body:
    {
        "prompt": "User query",
        "max_tokens": 4096
    }
    """
    prompt = request.get("prompt", "")
    max_tokens = request.get("max_tokens", 4096)

    # Simulate processing delay
    await asyncio.sleep(0.5)

    response_text = get_mock_response(prompt)

    # Respect max_tokens (approximate - 1 token ~= 4 chars in Korean)
    max_chars = max_tokens * 4
    if len(response_text) > max_chars:
        response_text = response_text[:max_chars]

    return {
        "text": response_text,
        "model": "mock-llama-3-8b",
        "tokens_generated": len(response_text) // 4
    }


@app.post("/generate_stream")
async def generate_stream(request: Dict[str, Any]):
    """
    Generate LLM response with streaming (SSE)

    Request body:
    {
        "prompt": "User query",
        "max_tokens": 4096
    }
    """
    prompt = request.get("prompt", "")
    max_tokens = request.get("max_tokens", 4096)

    async def stream_response():
        """Stream response character by character"""
        response_text = get_mock_response(prompt)

        # Respect max_tokens
        max_chars = max_tokens * 4
        if len(response_text) > max_chars:
            response_text = response_text[:max_chars]

        # Stream character by character
        for char in response_text:
            yield f"data: {char}\n\n"
            # Simulate typing delay (faster for testing)
            await asyncio.sleep(0.02)

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Mock LLM Service Starting...")
    print("=" * 60)
    print("This is a mock service for testing without GPU/LLM model")
    print("Real deployment uses vLLM with Meta-Llama-3-8B")
    print("=" * 60)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
