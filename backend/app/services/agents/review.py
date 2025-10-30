"""
Review Agent - 검토 에이전트

Reviews documents for errors and suggests improvements.
Checks factual accuracy, grammar, policy compliance.

Capabilities:
- Detect factual errors
- Find grammar and spelling mistakes
- Verify policy compliance
- Identify missing information
- Suggest improvements with examples

Business Rules (FR-071.5):
- Check completeness, accuracy, consistency, compliance
- Categorize issues by severity (높음/중간/낮음)
- Provide specific improvement suggestions
- Include examples in recommendations
- Use constructive tone
"""

from typing import Dict, Optional
from ..llm_service_factory import get_llm_service
from ..base_llm_service import BaseLLMService


class ReviewAgent:
    """
    Review Agent for document quality assurance

    Workflow:
    1. Analyze document structure
    2. Check for errors (factual, grammatical, policy)
    3. Categorize issues by severity
    4. Provide improvement suggestions
    5. Offer recommendations
    """

    def __init__(self):
        """Initialize agent with LLM service"""
        self.llm: BaseLLMService = get_llm_service()
        self.agent_name = "review"

        try:
            self.system_prompt = self.llm.get_agent_prompt(self.agent_name)
        except Exception as e:
            print(f"[ReviewAgent] Warning: Could not load prompt: {e}")
            self.system_prompt = self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return """당신은 문서 검토 전문가입니다.
작성된 내용의 사실 오류, 문법 오류, 정책 준수 여부를 검토합니다.
문제점을 구체적으로 지적하고, 개선 방안을 예시와 함께 제안합니다."""

    async def process(
        self,
        user_query: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process document review request

        Args:
            user_query: Document to review
            context: Optional context dict containing:
                - previous_outputs: Documents from previous agents

        Returns:
            str: Review results with improvement suggestions
        """
        if context is None:
            context = {}

        conversation_history = context.get("conversation_history", [])
        previous_outputs = context.get("previous_outputs", {})

        # If reviewing output from another agent in workflow
        if previous_outputs:
            # Extract document to review from previous agent
            workflow_context = self._build_workflow_context(previous_outputs)
            user_query = f"다음 문서를 검토해주세요:\n\n{workflow_context}\n\n{user_query}"

        try:
            response = await self.llm.generate_with_agent(
                agent_name=self.agent_name,
                user_query=user_query,
                conversation_history=conversation_history,
                max_tokens=4000
            )

            response = self._post_process_response(response)

            return response

        except Exception as e:
            error_msg = "죄송합니다. 문서 검토 중 오류가 발생했습니다. 다시 시도해 주세요."
            print(f"[ReviewAgent] Error: {e}")
            return error_msg

    def _build_workflow_context(self, previous_outputs: Dict[str, str]) -> str:
        """
        Build document to review from previous agent outputs

        In workflow, Review Agent typically reviews output from:
        - DocumentWritingAgent
        - CitizenSupportAgent
        - LegalResearchAgent
        """
        # Use the most recent output (last agent in workflow)
        if previous_outputs:
            # Get last output
            last_agent = list(previous_outputs.keys())[-1]
            document = previous_outputs[last_agent]
            return f"[{last_agent} 작성 문서]\n{document}"

        return ""

    def _post_process_response(self, response: str) -> str:
        """Post-process review results"""
        response = response.strip()

        if not response or len(response) < 10:
            return "죄송합니다. 검토 결과를 생성할 수 없습니다. 문서를 확인해 주세요."

        max_length = 8000
        if len(response) > max_length:
            response = response[:max_length] + "\n\n(검토 결과가 너무 길어 일부 생략되었습니다)"

        return response

    def get_agent_info(self) -> Dict[str, str]:
        """Get agent metadata"""
        return {
            "name": self.agent_name,
            "display_name": "검토 에이전트",
            "description": "문서의 오류를 검토하고 개선 방안을 제안합니다",
            "capabilities": [
                "사실 오류 검출",
                "문법 검토",
                "정책 준수 확인",
                "개선 방안 제안",
                "심각도별 분류"
            ],
            "language": "Korean (검토 및 제안)"
        }
