"""
ReAct Tools Unit Tests

T167: Test each of 6 tools individually
- DocumentSearchTool
- CalculatorTool
- DateScheduleTool
- DataAnalysisTool
- DocumentTemplateTool
- LegalReferenceTool
"""
import pytest
from datetime import datetime
import json
import pandas as pd
import tempfile

from app.services.react_tools.document_search import DocumentSearchTool
from app.services.react_tools.calculator import CalculatorTool
from app.services.react_tools.date_schedule import DateScheduleTool
from app.services.react_tools.data_analysis import DataAnalysisTool
from app.services.react_tools.document_template import DocumentTemplateTool
from app.services.react_tools.legal_reference import LegalReferenceTool


class TestDocumentSearchTool:
    """T167: Test DocumentSearchTool"""

    def test_document_search_basic(self, db_session):
        """Test basic document search"""
        tool = DocumentSearchTool(db_session)

        result = tool.execute({"query": "예산", "top_k": 3})

        assert "검색 결과" in result or "문서가 없습니다" in result
        assert isinstance(result, str)

    def test_document_search_empty_query(self, db_session):
        """Test document search with empty query"""
        tool = DocumentSearchTool(db_session)

        result = tool.execute({"query": "", "top_k": 3})

        assert "오류" in result or "검색어를 입력" in result

    def test_document_search_invalid_top_k(self, db_session):
        """Test document search with invalid top_k"""
        tool = DocumentSearchTool(db_session)

        result = tool.execute({"query": "test", "top_k": -1})

        # Should handle gracefully
        assert isinstance(result, str)


class TestCalculatorTool:
    """T167: Test CalculatorTool"""

    def test_calculator_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        tool = CalculatorTool()

        result = tool.execute({"expression": "100 + 200"})

        assert "300" in result

    def test_calculator_korean_currency(self):
        """Test Korean currency units"""
        tool = CalculatorTool()

        # Test 만원 (10,000 won)
        result = tool.execute({"expression": "10만원 + 5만원"})
        assert "150000" in result or "15만" in result

        # Test 억원 (100,000,000 won)
        result = tool.execute({"expression": "1억원 + 5000만원"})
        assert "150000000" in result or "1.5억" in result

    def test_calculator_complex_expression(self):
        """Test complex mathematical expressions"""
        tool = CalculatorTool()

        result = tool.execute({"expression": "(100 + 50) * 2 / 3"})

        assert "100" in result

    def test_calculator_invalid_expression(self):
        """Test invalid mathematical expression"""
        tool = CalculatorTool()

        result = tool.execute({"expression": "invalid + expression"})

        assert "오류" in result or "계산할 수 없습니다" in result

    def test_calculator_division_by_zero(self):
        """Test division by zero"""
        tool = CalculatorTool()

        result = tool.execute({"expression": "100 / 0"})

        assert "오류" in result or "0으로 나눌 수 없습니다" in result


class TestDateScheduleTool:
    """T167: Test DateScheduleTool"""

    def test_date_schedule_add_days(self):
        """Test adding days to current date"""
        tool = DateScheduleTool()

        result = tool.execute({
            "query": "오늘부터 30일 후",
            "operation": "add_days"
        })

        assert "2025" in result or "2024" in result
        assert isinstance(result, str)

    def test_date_schedule_days_until(self):
        """Test calculating days until a date"""
        tool = DateScheduleTool()

        result = tool.execute({
            "query": "2025-12-31까지 남은 일수",
            "operation": "days_until"
        })

        # Should return number of days
        assert "일" in result or "day" in result.lower()

    def test_date_schedule_check_holiday(self):
        """Test checking if date is a holiday"""
        tool = DateScheduleTool()

        # Test known holiday (설날)
        result = tool.execute({
            "query": "2024-02-10은 휴일인가요?",
            "operation": "check_holiday"
        })

        assert "설날" in result or "휴일" in result or "공휴일" in result

    def test_date_schedule_business_days(self):
        """Test calculating business days"""
        tool = DateScheduleTool()

        result = tool.execute({
            "query": "2024-01-01부터 2024-01-31까지 영업일",
            "operation": "business_days"
        })

        # Should return number of business days
        assert any(char.isdigit() for char in result)

    def test_date_schedule_fiscal_year(self):
        """Test fiscal year conversion"""
        tool = DateScheduleTool()

        result = tool.execute({
            "query": "2024년 회계연도",
            "operation": "fiscal_year"
        })

        assert "회계연도" in result or "2024" in result


class TestDataAnalysisTool:
    """T167: Test DataAnalysisTool"""

    def test_data_analysis_basic_csv(self):
        """Test analyzing a basic CSV file"""
        tool = DataAnalysisTool()

        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("이름,나이,부서\n")
            f.write("홍길동,30,개발팀\n")
            f.write("김철수,35,기획팀\n")
            f.write("이영희,28,디자인팀\n")
            csv_path = f.name

        result = tool.execute({
            "file_path": csv_path,
            "operation": "summary"
        })

        assert "3" in result or "행" in result
        assert isinstance(result, str)

    def test_data_analysis_statistics(self):
        """Test statistical analysis"""
        tool = DataAnalysisTool()

        # Create temporary CSV with numeric data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("항목,금액\n")
            f.write("예산1,1000000\n")
            f.write("예산2,2000000\n")
            f.write("예산3,1500000\n")
            csv_path = f.name

        result = tool.execute({
            "file_path": csv_path,
            "operation": "statistics",
            "column": "금액"
        })

        # Should include mean, sum, etc.
        assert "평균" in result or "합계" in result or "mean" in result.lower()

    def test_data_analysis_invalid_file(self):
        """Test analysis with non-existent file"""
        tool = DataAnalysisTool()

        result = tool.execute({
            "file_path": "/nonexistent/file.csv",
            "operation": "summary"
        })

        assert "오류" in result or "찾을 수 없습니다" in result


class TestDocumentTemplateTool:
    """T167: Test DocumentTemplateTool"""

    def test_document_template_official_letter(self):
        """Test generating official letter template"""
        tool = DocumentTemplateTool()

        result = tool.execute({
            "template_type": "official_letter",
            "variables": {
                "title": "예산 집행 계획",
                "recipient": "담당자",
                "content": "2024년 예산 집행 계획을 제출합니다."
            }
        })

        assert "예산 집행 계획" in result
        assert "담당자" in result
        assert isinstance(result, str)

    def test_document_template_report(self):
        """Test generating report template"""
        tool = DocumentTemplateTool()

        result = tool.execute({
            "template_type": "report",
            "variables": {
                "title": "분기 실적 보고",
                "period": "2024년 1분기",
                "summary": "실적 요약 내용"
            }
        })

        assert "분기 실적 보고" in result
        assert "2024년 1분기" in result

    def test_document_template_notice(self):
        """Test generating notice template"""
        tool = DocumentTemplateTool()

        result = tool.execute({
            "template_type": "notice",
            "variables": {
                "title": "시스템 점검 안내",
                "date": "2024-10-30",
                "content": "정기 점검이 진행됩니다."
            }
        })

        assert "시스템 점검 안내" in result
        assert "2024-10-30" in result

    def test_document_template_invalid_type(self):
        """Test with invalid template type"""
        tool = DocumentTemplateTool()

        result = tool.execute({
            "template_type": "invalid_type",
            "variables": {}
        })

        assert "오류" in result or "지원하지 않는" in result


class TestLegalReferenceTool:
    """T167: Test LegalReferenceTool"""

    def test_legal_reference_search_law(self):
        """Test searching for law references"""
        tool = LegalReferenceTool()

        result = tool.execute({
            "query": "예산",
            "reference_type": "law"
        })

        assert "법" in result or "조례" in result or "규정" in result
        assert isinstance(result, str)

    def test_legal_reference_search_ordinance(self):
        """Test searching for local ordinances"""
        tool = LegalReferenceTool()

        result = tool.execute({
            "query": "환경",
            "reference_type": "ordinance"
        })

        assert "조례" in result or "규정" in result

    def test_legal_reference_search_regulation(self):
        """Test searching for regulations"""
        tool = LegalReferenceTool()

        result = tool.execute({
            "query": "민원",
            "reference_type": "regulation"
        })

        assert "규정" in result or "지침" in result

    def test_legal_reference_article_lookup(self):
        """Test looking up specific article"""
        tool = LegalReferenceTool()

        result = tool.execute({
            "query": "지방재정법 제37조",
            "reference_type": "law",
            "article": "37"
        })

        assert "37조" in result or "제37조" in result

    def test_legal_reference_empty_query(self):
        """Test with empty query"""
        tool = LegalReferenceTool()

        result = tool.execute({
            "query": "",
            "reference_type": "law"
        })

        assert "오류" in result or "검색어를 입력" in result


# Integration tests for all tools
class TestToolsIntegration:
    """T167: Integration tests for all tools working together"""

    def test_all_tools_initialization(self, db_session):
        """Test that all tools can be initialized"""
        tools = [
            DocumentSearchTool(db_session),
            CalculatorTool(),
            DateScheduleTool(),
            DataAnalysisTool(),
            DocumentTemplateTool(),
            LegalReferenceTool(),
        ]

        assert len(tools) == 6
        for tool in tools:
            assert hasattr(tool, 'execute')
            assert callable(tool.execute)

    def test_tool_error_handling(self):
        """Test that all tools handle errors gracefully"""
        tools = [
            CalculatorTool(),
            DateScheduleTool(),
            DataAnalysisTool(),
            DocumentTemplateTool(),
            LegalReferenceTool(),
        ]

        for tool in tools:
            # Try executing with invalid/missing parameters
            result = tool.execute({})
            assert isinstance(result, str)
            # Should not raise exception
