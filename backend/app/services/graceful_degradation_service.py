"""
Graceful degradation service (T205, FR-087)

Fallback strategies when advanced features fail:
- Safety filter: ML fails → rule-based only
- ReAct: Tool fails → standard LLM response
- Orchestrator: Routing fails → general LLM
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class GracefulDegradationService:
    """
    Handles graceful degradation for advanced features
    """
    
    @staticmethod
    async def safety_filter_fallback(
        message: str,
        ml_error: Exception
    ) -> dict:
        """
        Safety filter fallback: Use rule-based filter only
        
        When ML filter (toxic-bert) fails, fall back to keyword-based
        """
        logger.warning(f"Safety filter ML failed, using rule-based fallback: {ml_error}")
        
        # Import here to avoid circular dependency
        from app.services.safety_filter.rule_based import rule_based_filter
        
        try:
            result = rule_based_filter(message)
            return {
                "is_safe": result["is_safe"],
                "categories": result["categories"],
                "method": "rule_based_fallback",
                "warning": "ML 필터 오류로 규칙 기반 필터만 사용했습니다."
            }
        except Exception as e:
            logger.error(f"Rule-based fallback also failed: {e}")
            # Ultimate fallback: assume safe but warn
            return {
                "is_safe": True,
                "categories": [],
                "method": "emergency_fallback",
                "warning": "안전 필터 오류가 발생했습니다. 신중하게 사용하세요."
            }
    
    @staticmethod
    async def react_agent_fallback(
        query: str,
        tool_error: Exception
    ) -> str:
        """
        ReAct agent fallback: Use standard LLM without tools
        
        When tool execution fails, generate response without tools
        """
        logger.warning(f"ReAct tool failed, using standard LLM fallback: {tool_error}")
        
        try:
            from app.services.llm_service import llm_service
            
            fallback_prompt = f"""도구 사용 없이 다음 질문에 답변하세요:

질문: {query}

참고: 일부 도구가 현재 사용 불가능하여 일반적인 지식으로만 답변합니다."""
            
            response = await llm_service.generate(fallback_prompt)
            
            warning = "\n\n⚠️ 일부 도구를 사용할 수 없어 제한된 정보로 답변했습니다."
            return response + warning
            
        except Exception as e:
            logger.error(f"LLM fallback also failed: {e}")
            return "죄송합니다. 현재 서비스 사용이 어렵습니다. 잠시 후 다시 시도해주세요."
    
    @staticmethod
    async def orchestrator_fallback(
        query: str,
        routing_error: Exception
    ) -> str:
        """
        Orchestrator fallback: Use general LLM without agent routing
        
        When agent routing fails, use base LLM directly
        """
        logger.warning(f"Orchestrator routing failed, using general LLM: {routing_error}")
        
        try:
            from app.services.llm_service import llm_service
            
            fallback_prompt = f"""다음 질문에 답변하세요:

{query}

답변:"""
            
            response = await llm_service.generate(fallback_prompt)
            return response
            
        except Exception as e:
            logger.error(f"General LLM fallback also failed: {e}")
            return "죄송합니다. 현재 서비스 사용이 어렵습니다. 잠시 후 다시 시도해주세요."
    
    @staticmethod
    def should_use_fallback(
        error: Exception,
        retry_count: int = 0,
        max_retries: int = 1
    ) -> bool:
        """
        Determine if fallback should be used
        
        Args:
            error: The exception that occurred
            retry_count: Number of retries attempted
            max_retries: Maximum retries before fallback
            
        Returns:
            True if should use fallback, False if should retry
        """
        # Network errors: retry once
        if isinstance(error, (ConnectionError, TimeoutError)):
            return retry_count >= max_retries
        
        # Model errors: immediate fallback
        if "model" in str(error).lower() or "load" in str(error).lower():
            return True
        
        # Resource errors: immediate fallback
        if "memory" in str(error).lower() or "resource" in str(error).lower():
            return True
        
        # Default: retry once
        return retry_count >= max_retries
