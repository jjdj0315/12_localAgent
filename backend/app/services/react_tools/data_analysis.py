"""
Data Analysis Tool

Analyzes CSV/Excel data and provides summary statistics.
Per FR-061.4: pandas, openpyxl, summary statistics, Korean formatting.
"""
from typing import Dict, Any, Tuple
import pandas as pd
import io
from pathlib import Path


class DataAnalysisTool:
    """Data analysis tool for ReAct agent"""

    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """Get tool definition"""
        return {
            "name": "data_analysis",
            "display_name": "데이터 분석",
            "description": "CSV/Excel 데이터를 분석하고 통계 요약을 제공합니다.",
            "category": "data_analysis",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "분석할 데이터 (CSV 형식)"},
                    "operation": {"type": "string", "enum": ["summary", "mean", "count"], "default": "summary"}
                },
                "required": ["data"]
            },
            "timeout_seconds": 30
        }

    def execute(self, data: str, operation: str = "summary", **kwargs) -> str:
        """Execute data analysis"""
        try:
            df = pd.read_csv(io.StringIO(data))

            if operation == "summary":
                result = df.describe(include='all').to_string()
                return f"데이터 요약 통계:\n{result}\n\n총 행 수: {len(df)}, 열 수: {len(df.columns)}"
            elif operation == "mean":
                numeric_cols = df.select_dtypes(include=['number']).columns
                means = df[numeric_cols].mean()
                return f"평균값:\n{means.to_string()}"
            elif operation == "count":
                return f"행 개수: {len(df)}"

        except Exception as e:
            return f"데이터 분석 오류: {str(e)}"

    def validate_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate parameters"""
        if "data" not in parameters:
            return False, "data가 필요합니다."
        return True, ""
