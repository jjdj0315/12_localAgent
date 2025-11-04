"""
Document Template Tool

Generates government documents from templates.
Per FR-061.5: 공문서, 보고서, 안내문 templates using Jinja2.
"""
from typing import Dict, Any, Tuple
from jinja2 import Template
from datetime import datetime


class DocumentTemplateTool:
    """Document template tool for ReAct agent"""

    TEMPLATES = {
        "official_letter": """[공문서]

수신: {{ recipient }}
제목: {{ title }}

{{ content }}

{{ date }}
발신: {{ sender }}
""",
        "report": """[업무 보고서]

제목: {{ title }}
작성일: {{ date }}
작성자: {{ author }}

1. 개요
{{ overview }}

2. 상세 내용
{{ details }}

3. 결론
{{ conclusion }}
""",
        "notice": """[안내문]

제목: {{ title }}

{{ content }}

문의: {{ contact }}
날짜: {{ date }}
"""
    }

    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "name": "document_template",
            "display_name": "문서 템플릿",
            "description": "공문서, 보고서, 안내문 등을 템플릿에서 생성합니다.",
            "category": "document_template",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "template_type": {"type": "string", "enum": ["official_letter", "report", "notice"]},
                    "variables": {"type": "object", "description": "템플릿 변수"}
                },
                "required": ["template_type", "variables"]
            },
            "timeout_seconds": 10
        }

    def execute(self, template_type: str, variables: Dict[str, str], **kwargs) -> str:
        """Execute template generation"""
        try:
            if template_type not in self.TEMPLATES:
                return f"알 수 없는 템플릿: {template_type}"

            # Add default date if not provided
            if "date" not in variables:
                variables["date"] = datetime.now().strftime("%Y년 %m월 %d일")

            template = Template(self.TEMPLATES[template_type])
            result = template.render(**variables)

            return f"문서 생성 완료:\n\n{result}"

        except Exception as e:
            return f"템플릿 생성 오류: {str(e)}"

    def validate_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate parameters"""
        if "template_type" not in parameters:
            return False, "template_type이 필요합니다."
        if "variables" not in parameters:
            return False, "variables가 필요합니다."
        return True, ""
