"""
응답 길이 제한 및 문서 생성 모드 키워드 감지 (FR-017, T225, T225A)

- 일반 모드: 최대 4,000자
- 문서 생성 모드: 최대 10,000자 (키워드 감지 시 자동 전환)
- 초과 시 잘림 경고 메시지 추가
"""

import re
from typing import Tuple

# 문서 생성 모드 키워드 (FR-017)
DOCUMENT_GENERATION_KEYWORDS = [
    "문서 작성",
    "초안 생성",
    "공문",
    "보고서 작성",
    "안내문 작성",
    "정책 문서",
    "문서 생성",
    "초안 작성",
    "작성해",
    "작성해줘",
    "작성해주세요",
]

# 응답 길이 제한
DEFAULT_MAX_LENGTH = 4000  # 일반 모드
DOCUMENT_MAX_LENGTH = 10000  # 문서 생성 모드


def detect_document_generation_mode(user_message: str) -> bool:
    """
    사용자 메시지에서 문서 생성 모드 키워드 감지
    
    Args:
        user_message: 사용자 입력 메시지
        
    Returns:
        문서 생성 모드 여부
    """
    message_lower = user_message.lower()
    
    for keyword in DOCUMENT_GENERATION_KEYWORDS:
        if keyword in message_lower:
            return True
    
    return False


def get_max_response_length(user_message: str) -> int:
    """
    사용자 메시지 기반 최대 응답 길이 반환
    
    Args:
        user_message: 사용자 입력 메시지
        
    Returns:
        최대 응답 길이 (문자 수)
    """
    if detect_document_generation_mode(user_message):
        return DOCUMENT_MAX_LENGTH
    return DEFAULT_MAX_LENGTH


def truncate_response(
    response: str,
    user_message: str,
    force_max_length: int = None
) -> Tuple[str, bool]:
    """
    응답 길이 제한 및 잘림 경고 추가
    
    Args:
        response: AI 응답 텍스트
        user_message: 사용자 입력 (모드 감지용)
        force_max_length: 강제 최대 길이 (선택)
        
    Returns:
        (잘린 응답, 잘렸는지 여부)
    """
    max_length = force_max_length or get_max_response_length(user_message)
    
    if len(response) <= max_length:
        return response, False
    
    # 응답 자르기
    truncated = response[:max_length]
    
    # 마지막 문장이 완결되도록 조정
    last_period = truncated.rfind('.')
    last_newline = truncated.rfind('\n')
    last_punctuation = max(last_period, last_newline)
    
    if last_punctuation > max_length - 200:  # 200자 이내면 문장 끝에서 자르기
        truncated = truncated[:last_punctuation + 1]
    
    # 잘림 경고 메시지 추가
    warning = "\n\n⚠️ 응답이 너무 길어 잘렸습니다. 더 구체적인 질문으로 나눠주세요."
    truncated += warning
    
    return truncated, True


def count_tokens_approximate(text: str) -> int:
    """
    토큰 수 근사 계산 (정확한 토크나이저 사용 권장)
    
    한국어 기준:
    - 1 토큰 ≈ 2-3자 (공백 포함)
    - 영어: 1 토큰 ≈ 4자
    
    Args:
        text: 텍스트
        
    Returns:
        근사 토큰 수
    """
    # 한국어 문자 수
    korean_chars = len(re.findall(r'[가-힣]', text))
    # 영어 단어 수
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    # 숫자 및 기타
    other_chars = len(text) - korean_chars - english_words
    
    # 근사 계산
    tokens = (korean_chars / 2.5) + english_words + (other_chars / 4)
    
    return int(tokens)


def validate_response_length(response: str, user_message: str) -> dict:
    """
    응답 길이 검증 및 통계 반환
    
    Args:
        response: AI 응답
        user_message: 사용자 메시지
        
    Returns:
        검증 결과 딕셔너리
    """
    char_count = len(response)
    token_count = count_tokens_approximate(response)
    max_length = get_max_response_length(user_message)
    is_document_mode = detect_document_generation_mode(user_message)
    is_truncated = char_count > max_length
    
    return {
        "char_count": char_count,
        "token_count": token_count,
        "max_length": max_length,
        "is_document_mode": is_document_mode,
        "is_truncated": is_truncated,
        "within_limit": not is_truncated
    }


# 편의 함수
def process_llm_response(response: str, user_message: str) -> str:
    """
    LLM 응답 처리 (길이 제한 적용)
    
    사용 예:
        raw_response = model.generate(prompt)
        final_response = process_llm_response(raw_response, user_message)
    
    Args:
        response: 원본 LLM 응답
        user_message: 사용자 메시지
        
    Returns:
        처리된 응답 (필요 시 잘림)
    """
    truncated_response, was_truncated = truncate_response(response, user_message)
    
    if was_truncated:
        print(f"[Response Limiter] Response truncated from {len(response)} to {len(truncated_response)} chars")
    
    return truncated_response
