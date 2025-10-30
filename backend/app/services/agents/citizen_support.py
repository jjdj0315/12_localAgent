"""
Citizen Support Agent - 민원 지원 에이전트

Handles citizen inquiries with empathetic, polite responses.
Specialized for local government administrative questions.

Capabilities:
- Answer administrative procedure questions
- Explain required documents
- Provide office hours and contact information
- Use respectful Korean language (존댓말)
- Check completeness of responses (all parts of question answered)

Business Rules (FR-071.1):
- Always use polite language (존댓말)
- Answer all parts of the user's question
- Request additional information if needed
- Avoid legal/medical advice
- Redirect complex cases to appropriate departments
"""

from typing import Dict, Optional
from ..llm_service_factory import get_llm_service
from ..base_llm_service import BaseLLMService


class CitizenSupportAgent:
    """
    Citizen Support Agent for handling public inquiries

    Workflow:
    1. Analyze user query for completeness
    2. Generate empathetic response using agent-specific prompt
    3. Verify all parts of question are answered
    4. Add follow-up guidance if needed
    """

    def __init__(self):
        """Initialize agent with LLM service"""
        # Get LLM service (auto-detects llama.cpp or vLLM)
        self.llm: BaseLLMService = get_llm_service()
        self.agent_name = "citizen_support"

        # Load system prompt from file
        try:
            self.system_prompt = self.llm.get_agent_prompt(self.agent_name)
        except Exception as e:
            print(f"[CitizenSupportAgent] Warning: Could not load prompt: {e}")
            # Fallback to default prompt
            self.system_prompt = self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Get default system prompt if file loading fails"""
        return """당신은 지방자치단체의 민원 지원 전문가입니다.
시민의 문의를 친절하고 공손하게 답변하며, 존댓말을 사용합니다.
질문의 모든 부분에 답변하고, 필요한 경우 추가 정보를 요청합니다."""

    async def process(
        self,
        user_query: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process citizen inquiry and generate response

        Args:
            user_query: User's question or request
            context: Optional context dict containing:
                - conversation_history: Previous messages
                - previous_outputs: Outputs from previous agents (workflow)

        Returns:
            str: Agent's response in Korean

        Example:
            >>> agent = CitizenSupportAgent()
            >>> response = await agent.process("전입신고는 어떻게 하나요?")
        """
        if context is None:
            context = {}

        # Extract conversation history
        conversation_history = context.get("conversation_history", [])

        # Check if this is part of a workflow
        previous_outputs = context.get("previous_outputs", {})
        if previous_outputs:
            # If other agents ran before, incorporate their context
            workflow_context = self._build_workflow_context(previous_outputs)
            user_query = f"{workflow_context}\n\n{user_query}"

        # Generate response using LLM with agent-specific prompt
        try:
            response = await self.llm.generate_with_agent(
                agent_name=self.agent_name,
                user_query=user_query,
                conversation_history=conversation_history,
                max_tokens=4000
            )

            # Post-process response
            response = self._post_process_response(response, user_query)

            return response

        except Exception as e:
            # Error handling
            error_msg = f"죄송합니다. 답변 생성 중 오류가 발생했습니다. 다시 시도해 주시거나 담당자에게 문의해 주세요."
            print(f"[CitizenSupportAgent] Error: {e}")
            return error_msg

    def _build_workflow_context(self, previous_outputs: Dict[str, str]) -> str:
        """
        Build context from previous agent outputs in workflow

        Args:
            previous_outputs: Dict of {agent_name: response}

        Returns:
            str: Formatted context string
        """
        context_parts = ["[이전 에이전트 결과]"]

        for agent_name, output in previous_outputs.items():
            context_parts.append(f"\n{agent_name}: {output[:200]}...")  # Truncate

        return "\n".join(context_parts)

    def _post_process_response(self, response: str, user_query: str) -> str:
        """
        Post-process response for quality

        Checks:
        - Remove excessive whitespace
        - Ensure response is not empty
        - Truncate if too long

        Args:
            response: Raw LLM response
            user_query: Original user question

        Returns:
            str: Cleaned response
        """
        # Remove excessive whitespace
        response = response.strip()
        response = "\n".join(line.strip() for line in response.split("\n"))

        # Check for empty response
        if not response or len(response) < 10:
            return "죄송합니다. 답변을 생성할 수 없습니다. 질문을 다시 확인해 주시거나 담당자에게 문의해 주세요."

        # Truncate if too long (sanity check)
        max_length = 8000
        if len(response) > max_length:
            response = response[:max_length] + "\n\n(답변이 너무 길어 일부 생략되었습니다)"

        return response

    def get_agent_info(self) -> Dict[str, str]:
        """
        Get agent metadata

        Returns:
            Dict with agent name, description, capabilities
        """
        return {
            "name": self.agent_name,
            "display_name": "민원 지원 에이전트",
            "description": "시민 문의에 친절하고 정확하게 답변합니다",
            "capabilities": [
                "행정 절차 안내",
                "필요 서류 설명",
                "부서 및 연락처 안내",
                "존댓말 사용",
                "질문 완전성 확인"
            ],
            "language": "Korean (존댓말)"
        }
