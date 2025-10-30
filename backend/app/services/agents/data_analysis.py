"""
Data Analysis Agent - 데이터 분석 에이전트

Analyzes statistical data and provides insights.
Specialized for government reports and decision support.

Capabilities:
- Analyze trends and patterns
- Format numbers with Korean thousand separators (1,234,567)
- Identify meaningful insights
- Suggest appropriate visualizations
- Compare data across time periods or regions

Business Rules (FR-071.4):
- Use Korean number formatting (천 단위 쉼표)
- Identify trends (증가/감소)
- Suggest chart types for government reports
- Avoid speculation without data support
- State data source or indicate "확인 필요"
"""

from typing import Dict, Optional
from ..llm_service_factory import get_llm_service
from ..base_llm_service import BaseLLMService


class DataAnalysisAgent:
    """
    Data Analysis Agent for statistical analysis

    Workflow:
    1. Parse data from query
    2. Calculate summary statistics
    3. Identify trends and patterns
    4. Suggest visualizations
    5. Provide insights and recommendations
    """

    def __init__(self):
        """Initialize agent with LLM service"""
        self.llm: BaseLLMService = get_llm_service()
        self.agent_name = "data_analysis"

        try:
            self.system_prompt = self.llm.get_agent_prompt(self.agent_name)
        except Exception as e:
            print(f"[DataAnalysisAgent] Warning: Could not load prompt: {e}")
            self.system_prompt = self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return """당신은 데이터 분석 전문가입니다.
통계 데이터를 분석하고, 한국어 천 단위 쉼표로 숫자를 표시합니다.
트렌드를 식별하고, 정부 보고서에 적합한 시각화를 제안합니다."""

    async def process(
        self,
        user_query: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process data analysis request

        Args:
            user_query: Data analysis question with data
            context: Optional context dict

        Returns:
            str: Analysis results with insights
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

            response = self._post_process_response(response)

            return response

        except Exception as e:
            error_msg = "죄송합니다. 데이터 분석 중 오류가 발생했습니다. 데이터를 확인해 주세요."
            print(f"[DataAnalysisAgent] Error: {e}")
            return error_msg

    def _build_workflow_context(self, previous_outputs: Dict[str, str]) -> str:
        """Build context from previous agent outputs"""
        context_parts = ["[이전 단계 결과]"]
        for agent_name, output in previous_outputs.items():
            context_parts.append(f"\n{agent_name}: {output[:200]}...")
        return "\n".join(context_parts)

    def _post_process_response(self, response: str) -> str:
        """Post-process analysis results"""
        response = response.strip()

        if not response or len(response) < 10:
            return "죄송합니다. 데이터 분석 결과를 생성할 수 없습니다. 데이터를 확인해 주세요."

        max_length = 8000
        if len(response) > max_length:
            response = response[:max_length] + "\n\n(분석 결과가 너무 길어 일부 생략되었습니다)"

        return response

    def get_agent_info(self) -> Dict[str, str]:
        """Get agent metadata"""
        return {
            "name": self.agent_name,
            "display_name": "데이터 분석 에이전트",
            "description": "통계 데이터를 분석하고 인사이트를 제공합니다",
            "capabilities": [
                "트렌드 분석",
                "통계 계산",
                "시각화 제안",
                "인사이트 도출",
                "한국어 숫자 표기"
            ],
            "language": "Korean (데이터 분석)"
        }
