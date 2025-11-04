"""
Legal Reference Tool

Searches and references Korean laws and regulations.
Per FR-061.6: Search regulations, return citations.
"""
from typing import Dict, Any, Tuple, List


class LegalReferenceTool:
    """Legal reference tool for ReAct agent"""

    # Mock legal database (in production, would query actual legal DB)
    MOCK_LAWS = {
        "주민등록법": {
            "조문": [
                {"조": "제7조", "내용": "주민등록 신고는 전입일로부터 14일 이내에 하여야 한다."},
                {"조": "제20조", "내용": "주민등록증 발급은 만 17세 이상의 국민이 신청할 수 있다."}
            ]
        },
        "지방재정법": {
            "조문": [
                {"조": "제33조", "내용": "예산편성은 전년도 11월 30일까지 완료하여야 한다."},
                {"조": "제39조", "내용": "예비비는 예산총액의 100분의 1 이내로 계상할 수 있다."}
            ]
        },
        "행정절차법": {
            "조문": [
                {"조": "제21조", "내용": "처분의 사전 통지는 처분을 하기 전에 당사자에게 의견 제출 기회를 주어야 한다."},
                {"조": "제23조", "내용": "의견 제출은 서면 또는 말로 할 수 있다."}
            ]
        }
    }

    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "name": "legal_reference",
            "display_name": "법규 참조",
            "description": "법령, 조례를 검색하고 인용합니다.",
            "category": "legal_reference",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 법령 또는 키워드"},
                    "article": {"type": "string", "description": "특정 조문 (선택사항)"}
                },
                "required": ["query"]
            },
            "timeout_seconds": 15
        }

    def execute(self, query: str, article: str = None, **kwargs) -> str:
        """Execute legal reference search"""
        try:
            results = []

            # Search in mock database
            for law_name, law_data in self.MOCK_LAWS.items():
                if query.lower() in law_name.lower():
                    if article:
                        # Search for specific article
                        for art in law_data["조문"]:
                            if article in art["조"]:
                                results.append(f"**{law_name} {art['조']}**\n{art['내용']}")
                    else:
                        # Return all articles
                        for art in law_data["조문"]:
                            results.append(f"**{law_name} {art['조']}**\n{art['내용']}")

            if not results:
                # Keyword search in content
                for law_name, law_data in self.MOCK_LAWS.items():
                    for art in law_data["조문"]:
                        if query.lower() in art["내용"].lower():
                            results.append(f"**{law_name} {art['조']}**\n{art['내용']}")

            if not results:
                return f"'{query}'에 대한 법령을 찾을 수 없습니다. (현재 제한된 법령 DB 사용 중)"

            return "법령 검색 결과:\n\n" + "\n\n".join(results[:5])

        except Exception as e:
            return f"법령 검색 오류: {str(e)}"

    def validate_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate parameters"""
        if "query" not in parameters:
            return False, "query가 필요합니다."
        return True, ""
