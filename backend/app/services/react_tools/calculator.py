"""
Calculator Tool

Performs mathematical calculations supporting Korean currency symbols.
Per FR-061.2: sympy or numexpr, handle Korean currency symbols (원, 만원, 억원).
"""
from typing import Dict, Any, Tuple
import re
import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


class CalculatorTool:
    """
    Calculator tool for ReAct agent

    Evaluates mathematical expressions including:
    - Basic arithmetic (+, -, *, /, ^, **)
    - Functions (sqrt, log, sin, cos, etc.)
    - Korean currency units (원, 만원, 억원)
    - Percentage calculations
    """

    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """Get tool definition for ReAct agent"""
        return {
            "name": "calculator",
            "display_name": "계산기",
            "description": "수학 계산을 수행합니다. 예산 계산, 통계 계산, 일반 수식 계산 등에 사용하세요. 한국 통화 단위(원, 만원, 억원)를 지원합니다.",
            "category": "calculator",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "계산할 수식 (예: '1000만원 + 500만원', '10억원 * 0.05', 'sqrt(16)')"
                    }
                },
                "required": ["expression"]
            },
            "timeout_seconds": 10,
            "examples": [
                {
                    "expression": "1000만원 + 500만원",
                    "description": "통화 단위를 포함한 계산"
                },
                {
                    "expression": "10억원 * 0.05",
                    "description": "백분율 계산 (5%)"
                },
                {
                    "expression": "(1200 + 800) / 2",
                    "description": "평균 계산"
                },
                {
                    "expression": "sqrt(144)",
                    "description": "제곱근 계산"
                }
            ]
        }

    def execute(self, expression: str, **kwargs) -> str:
        """
        Execute calculation

        Args:
            expression: Mathematical expression to evaluate
            **kwargs: Additional parameters (ignored)

        Returns:
            Calculation result with explanation

        Raises:
            ValueError: If expression is invalid or unsafe
        """
        try:
            # Preprocess expression (handle Korean currency)
            processed_expr = self._preprocess_expression(expression)

            # Validate expression safety
            if not self._is_safe_expression(processed_expr):
                raise ValueError("표현식에 허용되지 않는 문자가 포함되어 있습니다.")

            # Parse and evaluate
            transformations = (standard_transformations + (implicit_multiplication_application,))
            result = parse_expr(processed_expr, transformations=transformations)

            # Evaluate to numeric value
            numeric_result = float(result.evalf())

            # Format result
            return self._format_result(expression, processed_expr, numeric_result)

        except Exception as e:
            raise ValueError(f"계산 오류: {str(e)}")

    def _preprocess_expression(self, expression: str) -> str:
        """
        Preprocess expression to handle Korean currency units

        Converts:
        - 원 (won) → * 1
        - 만원 (10,000 won) → * 10000
        - 억원 (100,000,000 won) → * 100000000

        Args:
            expression: Original expression

        Returns:
            Processed expression
        """
        # Replace Korean currency units
        # 억원 must be replaced before 원
        expr = expression

        # Handle 억원 (100 million won)
        expr = re.sub(r'(\d+(?:\.\d+)?)\s*억원', r'(\1 * 100000000)', expr)

        # Handle 만원 (10 thousand won)
        expr = re.sub(r'(\d+(?:\.\d+)?)\s*만원', r'(\1 * 10000)', expr)

        # Handle 원 (1 won) - but not part of 만원 or 억원
        expr = re.sub(r'(\d+(?:\.\d+)?)\s*원(?![\u4e00-\u9fff\uac00-\ud7af])', r'(\1 * 1)', expr)

        # Replace Korean percentage symbol
        expr = expr.replace('%', '/ 100')

        # Replace × and ÷ symbols
        expr = expr.replace('×', '*')
        expr = expr.replace('÷', '/')
        expr = expr.replace('÷', '/')

        # Replace Korean comma separator
        expr = expr.replace(',', '')

        return expr

    def _is_safe_expression(self, expression: str) -> bool:
        """
        Check if expression is safe to evaluate

        Args:
            expression: Expression to check

        Returns:
            True if safe, False otherwise
        """
        # Allowed characters: digits, operators, parentheses, letters (for functions), dot, space
        allowed_pattern = r'^[\d\+\-\*/\(\)\.\s\w\^]+$'

        if not re.match(allowed_pattern, expression):
            return False

        # Blacklist dangerous functions
        dangerous = ['eval', 'exec', 'compile', '__', 'import', 'open', 'file']
        for danger in dangerous:
            if danger in expression.lower():
                return False

        return True

    def _format_result(self, original_expr: str, processed_expr: str, result: float) -> str:
        """
        Format calculation result

        Args:
            original_expr: Original expression
            processed_expr: Processed expression
            result: Numeric result

        Returns:
            Formatted result string
        """
        # Format number with commas for readability
        if abs(result) >= 1:
            formatted_number = f"{result:,.2f}".rstrip('0').rstrip('.')
        else:
            formatted_number = f"{result:.6f}".rstrip('0').rstrip('.')

        # Determine appropriate unit
        unit_info = ""
        if "원" in original_expr or "만원" in original_expr or "억원" in original_expr:
            # Result is in won, convert to appropriate unit
            if abs(result) >= 100000000:  # >= 1억
                unit_value = result / 100000000
                unit_info = f" (약 {unit_value:,.2f}억원)"
            elif abs(result) >= 10000:  # >= 1만
                unit_value = result / 10000
                unit_info = f" (약 {unit_value:,.2f}만원)"
            else:
                unit_info = "원"

        output = [
            f"계산 결과: {formatted_number}{unit_info}",
            "",
            f"📝 수식: {original_expr}",
        ]

        # Show processed expression if different
        if original_expr != processed_expr and len(processed_expr) < 100:
            output.append(f"📝 처리된 수식: {processed_expr}")

        return "\n".join(output)

    def validate_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate input parameters

        Args:
            parameters: Input parameters

        Returns:
            (is_valid, error_message)
        """
        if "expression" not in parameters:
            return False, "계산 수식(expression)이 필요합니다."

        expression = parameters["expression"]
        if not isinstance(expression, str) or not expression.strip():
            return False, "수식은 비어있지 않은 문자열이어야 합니다."

        if len(expression) > 500:
            return False, "수식이 너무 깁니다 (최대 500자)."

        return True, ""


# Convenience function for testing
def calculate(expression: str) -> str:
    """
    Convenience function to perform calculation

    Args:
        expression: Mathematical expression

    Returns:
        Calculation result
    """
    tool = CalculatorTool()
    return tool.execute(expression)
