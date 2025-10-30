"""
Legal Research Agent - 법규 검색 에이전트

Searches and interprets laws and regulations.
Provides legal information with proper citations.

Capabilities:
- Search relevant laws and local ordinances
- Cite specific articles and clauses
- Explain legal terms in plain language
- Provide practical application guidance
- Indicate limitations (not legal advice)

Business Rules (FR-071.3):
- Cite laws accurately (법령명, 조문 번호)
- Explain legal terms in plain Korean
- Always state "본 답변은 법적 조언이 아닙니다"
- Reference sources (국가법령정보센터)
- Suggest consulting legal counsel for complex cases
"""

from typing import Dict, Optional
from ..llm_service_factory import get_llm_service
from ..base_llm_service import BaseLLMService


class LegalResearchAgent:
    """
    Legal Research Agent for law and regulation interpretation

    Workflow:
    1. Identify relevant laws/ordinances
    2. Quote specific articles
    3. Provide plain-language explanation
    4. Add disclaimer (not legal advice)
    """

    def __init__(self):
        """Initialize agent with LLM service"""
        self.llm: BaseLLMService = get_llm_service()
        self.agent_name = "legal_research"

        try:
            self.system_prompt = self.llm.get_agent_prompt(self.agent_name)
        except Exception as e:
            print(f"[LegalResearchAgent] Warning: Could not load prompt: {e}")
            self.system_prompt = self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return """당신은 법규 검색 및 해석 전문가입니다.
관련 법령 및 조례 조항을 정확히 인용하고, 법률 용어를 쉽게 풀어 설명합니다.
출처를 명확히 밝히고, 법적 해석의 한계를 안내합니다."""

    async def process(
        self,
        user_query: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process legal research request

        Args:
            user_query: Legal question
            context: Optional context dict

        Returns:
            str: Legal information with citations
        """
        if context is None:
            context = {}

        conversation_history = context.get("conversation_history", [])
        previous_outputs = context.get("previous_outputs", {})

        if previous_outputs:
            workflow_context = self._build_workflow_context(previous_outputs)
            user_query = f"{workflow_context}\n\n{user_query}"

        try:
            response = await self.llm.generate_with_agent(
                agent_name=self.agent_name,
                user_query=user_query,
                conversation_history=conversation_history,
                max_tokens=4000
            )

            # Always add disclaimer
            response = self._add_legal_disclaimer(response)
            response = self._post_process_response(response)

            return response

        except Exception as e:
            error_msg = "죄송합니다. 법령 검색 중 오류가 발생했습니다. 법제처 또는 자문 변호사에게 문의해 주세요."
            print(f"[LegalResearchAgent] Error: {e}")
            return error_msg

    def _build_workflow_context(self, previous_outputs: Dict[str, str]) -> str:
        """Build context from previous agent outputs"""
        context_parts = ["[이전 단계 결과]"]
        for agent_name, output in previous_outputs.items():
            context_parts.append(f"\n{agent_name}: {output[:200]}...")
        return "\n".join(context_parts)

    def _add_legal_disclaimer(self, response: str) -> str:
        """Add legal disclaimer to response"""
        disclaimer = "\n\n※ 본 답변은 법률 정보 제공을 위한 것으로, 법적 조언이 아닙니다. 구체적인 법률 문제는 법제처 또는 자문 변호사에게 문의하시기 바랍니다."

        if disclaimer not in response:
            response += disclaimer

        return response

    def _post_process_response(self, response: str) -> str:
        """Post-process response"""
        response = response.strip()

        if not response or len(response) < 10:
            return "죄송합니다. 관련 법령을 찾을 수 없습니다. 법제처에 문의해 주세요."

        max_length = 8000
        if len(response) > max_length:
            response = response[:max_length] + "\n\n(답변이 너무 길어 일부 생략되었습니다)"

        return response

    def get_agent_info(self) -> Dict[str, str]:
        """Get agent metadata"""
        return {
            "name": self.agent_name,
            "display_name": "법규 검색 에이전트",
            "description": "관련 법령을 검색하고 쉽게 해석합니다",
            "capabilities": [
                "법령 조항 인용",
                "법률 용어 해석",
                "출처 명시",
                "실무 적용 안내",
                "법적 한계 안내"
            ],
            "language": "Korean (법률 용어 + 쉬운 설명)"
        }
