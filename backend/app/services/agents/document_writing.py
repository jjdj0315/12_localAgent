"""
Document Writing Agent - 문서 작성 에이전트

Drafts official government documents following standard formats.
Specialized for formal reports, memos, and announcements.

Capabilities:
- Draft official memos (공문서)
- Write reports (보고서)
- Create announcements (안내문)
- Use formal administrative language
- Follow standard document structure (제목, 배경, 내용, 결론)
- Cite laws and regulations when applicable

Business Rules (FR-071.2):
- Follow standard document templates
- Use formal, respectful language
- Structure: Title → Background → Content → Conclusion
- Avoid colloquial expressions
- Include specific dates instead of vague terms
"""

from typing import Dict, Optional
from ..llm_service_factory import get_llm_service
from ..base_llm_service import BaseLLMService


class DocumentWritingAgent:
    """
    Document Writing Agent for official government documents

    Workflow:
    1. Identify document type (memo, report, announcement)
    2. Generate document using agent-specific prompt
    3. Verify standard structure is followed
    4. Offer revision suggestions
    """

    def __init__(self):
        """Initialize agent with LLM service"""
        self.llm: BaseLLMService = get_llm_service()
        self.agent_name = "document_writing"

        # Load system prompt
        try:
            self.system_prompt = self.llm.get_agent_prompt(self.agent_name)
        except Exception as e:
            print(f"[DocumentWritingAgent] Warning: Could not load prompt: {e}")
            self.system_prompt = self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return """당신은 정부 문서 작성 전문가입니다.
공문서, 보고서, 안내문을 작성할 때는 표준 양식을 따릅니다.
제목, 배경, 내용, 결론 순서로 작성하며 격식 있는 표현을 사용합니다."""

    async def process(
        self,
        user_query: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process document writing request

        Args:
            user_query: User's document request
            context: Optional context dict

        Returns:
            str: Generated document in Korean

        Example:
            >>> agent = DocumentWritingAgent()
            >>> response = await agent.process("환경 개선 사업 보고서를 작성해주세요")
        """
        if context is None:
            context = {}

        conversation_history = context.get("conversation_history", [])
        previous_outputs = context.get("previous_outputs", {})

        # Add workflow context if available
        if previous_outputs:
            workflow_context = self._build_workflow_context(previous_outputs)
            user_query = f"{workflow_context}\n\n{user_query}"

        # Generate document
        try:
            response = await self.llm.generate_with_agent(
                agent_name=self.agent_name,
                user_query=user_query,
                conversation_history=conversation_history,
                max_tokens=4000
            )

            # Post-process
            response = self._post_process_response(response)

            return response

        except Exception as e:
            error_msg = "죄송합니다. 문서 작성 중 오류가 발생했습니다. 다시 시도해 주세요."
            print(f"[DocumentWritingAgent] Error: {e}")
            return error_msg

    def _build_workflow_context(self, previous_outputs: Dict[str, str]) -> str:
        """Build context from previous agent outputs"""
        context_parts = ["[이전 단계 결과]"]
        for agent_name, output in previous_outputs.items():
            context_parts.append(f"\n{agent_name}: {output[:200]}...")
        return "\n".join(context_parts)

    def _post_process_response(self, response: str) -> str:
        """Post-process generated document"""
        response = response.strip()

        if not response or len(response) < 10:
            return "죄송합니다. 문서를 생성할 수 없습니다. 요청 내용을 다시 확인해 주세요."

        # Truncate if too long
        max_length = 8000
        if len(response) > max_length:
            response = response[:max_length] + "\n\n(문서가 너무 길어 일부 생략되었습니다)"

        return response

    def get_agent_info(self) -> Dict[str, str]:
        """Get agent metadata"""
        return {
            "name": self.agent_name,
            "display_name": "문서 작성 에이전트",
            "description": "공식 문서를 표준 양식에 맞춰 작성합니다",
            "capabilities": [
                "공문서 작성",
                "보고서 작성",
                "안내문 작성",
                "격식 있는 표현 사용",
                "표준 문서 구조 준수"
            ],
            "language": "Korean (격식체)"
        }
