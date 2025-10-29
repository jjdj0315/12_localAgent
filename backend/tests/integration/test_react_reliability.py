"""
ReAct Agent Reliability Tests

T168: Test tool execution success rate <10% error across 100 invocations
T169: Test ReAct agent stops at 5 iterations with helpful summary
T170: Test transparent error display when tool fails
T171: Verify tool execution audit log (sanitized parameters, no PII)
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.services.react_agent_service import ReActAgentService
from app.models.tool import Tool
from app.models.tool_execution import ToolExecution


class TestToolExecutionSuccessRate:
    """T168: Test tool execution success rate"""

    def test_calculator_success_rate(self):
        """Test calculator tool success rate over 100 invocations"""
        from app.services.react_tools.calculator import CalculatorTool

        tool = CalculatorTool()
        success_count = 0
        total_count = 100

        test_cases = [
            {"expression": "100 + 200"},
            {"expression": "50 * 2"},
            {"expression": "1000 / 10"},
            {"expression": "5만원 + 3만원"},
            {"expression": "(100 + 50) * 2"},
        ]

        for i in range(total_count):
            try:
                test_case = test_cases[i % len(test_cases)]
                result = tool.execute(test_case)
                if "오류" not in result and result:
                    success_count += 1
            except Exception:
                pass

        success_rate = (success_count / total_count) * 100
        error_rate = 100 - success_rate

        assert error_rate < 10, f"Error rate {error_rate:.1f}% exceeds 10% threshold"
        assert success_count >= 90, f"Only {success_count}/100 executions succeeded"

    def test_date_schedule_success_rate(self):
        """Test date/schedule tool success rate over 100 invocations"""
        from app.services.react_tools.date_schedule import DateScheduleTool

        tool = DateScheduleTool()
        success_count = 0
        total_count = 100

        test_cases = [
            {"query": "오늘부터 7일 후", "operation": "add_days"},
            {"query": "2025-12-31까지 남은 일수", "operation": "days_until"},
            {"query": "2024-10-03은 공휴일인가요?", "operation": "check_holiday"},
            {"query": "2024년 회계연도", "operation": "fiscal_year"},
        ]

        for i in range(total_count):
            try:
                test_case = test_cases[i % len(test_cases)]
                result = tool.execute(test_case)
                if "오류" not in result and result:
                    success_count += 1
            except Exception:
                pass

        success_rate = (success_count / total_count) * 100
        error_rate = 100 - success_rate

        assert error_rate < 10, f"Error rate {error_rate:.1f}% exceeds 10% threshold"
        assert success_count >= 90

    def test_document_template_success_rate(self):
        """Test document template tool success rate"""
        from app.services.react_tools.document_template import DocumentTemplateTool

        tool = DocumentTemplateTool()
        success_count = 0
        total_count = 100

        test_cases = [
            {
                "template_type": "official_letter",
                "variables": {"title": "테스트", "recipient": "담당자", "content": "내용"}
            },
            {
                "template_type": "report",
                "variables": {"title": "보고서", "period": "2024-Q1", "summary": "요약"}
            },
            {
                "template_type": "notice",
                "variables": {"title": "안내", "date": "2024-10-30", "content": "내용"}
            },
        ]

        for i in range(total_count):
            try:
                test_case = test_cases[i % len(test_cases)]
                result = tool.execute(test_case)
                if "오류" not in result and result and len(result) > 10:
                    success_count += 1
            except Exception:
                pass

        success_rate = (success_count / total_count) * 100
        error_rate = 100 - success_rate

        assert error_rate < 10, f"Error rate {error_rate:.1f}% exceeds 10% threshold"


class TestIterationLimits:
    """T169: Test ReAct agent stops at iteration limits"""

    def test_max_iterations_reached(self, db_session, test_user):
        """Test agent stops at max_iterations with helpful summary"""
        # Create test tool
        tool = Tool(
            name="test_tool",
            display_name="테스트 도구",
            description="테스트용 도구",
            category="test",
            is_active=True,
            priority=1
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        # Mock LLM that never returns Final Answer
        def mock_llm_infinite(prompt: str) -> str:
            return """
Thought: I need to use the tool again.
Action: test_tool
Action Input: {"query": "test"}
"""

        result = agent.execute_react_loop(
            query="Infinite loop test",
            llm_generate=mock_llm_infinite,
            max_iterations=5
        )

        # Should stop at iteration 5
        assert len(result["steps"]) <= 5
        assert result["final_answer"] is not None
        assert "최대 반복" in result["final_answer"] or "요약" in result["final_answer"]

    def test_early_termination_on_answer(self, db_session, test_user):
        """Test agent stops early when Final Answer is reached"""
        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        call_count = [0]

        def mock_llm_early_answer(prompt: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return "Final Answer: The answer is 42."
            return "This should not be reached"

        result = agent.execute_react_loop(
            query="What is the answer?",
            llm_generate=mock_llm_early_answer,
            max_iterations=5
        )

        # Should stop at iteration 1
        assert len(result["steps"]) == 1
        assert result["final_answer"] == "The answer is 42."

    def test_error_limit_termination(self, db_session, test_user):
        """Test agent stops after too many errors"""
        tool = Tool(
            name="failing_tool",
            display_name="실패 도구",
            description="항상 실패하는 도구",
            category="test",
            is_active=True,
            priority=1
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        def mock_llm_error(prompt: str) -> str:
            return """
Thought: Try the failing tool.
Action: failing_tool
Action Input: {"query": "test"}
"""

        result = agent.execute_react_loop(
            query="Error test",
            llm_generate=mock_llm_error,
            max_iterations=10
        )

        # Should stop after 3 errors
        assert result["final_answer"] is not None
        assert "오류" in result["final_answer"]


class TestErrorDisplay:
    """T170: Test transparent error display"""

    def test_tool_error_in_observation(self, db_session, test_user):
        """Test that tool errors are clearly shown in observations"""
        tool = Tool(
            name="calculator",
            display_name="계산기",
            description="계산 도구",
            category="utility",
            is_active=True,
            priority=1
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        def mock_llm(prompt: str) -> str:
            if "iteration 1" in prompt.lower():
                return """
Thought: Calculate with invalid expression.
Action: calculator
Action Input: {"expression": "invalid expression"}
"""
            else:
                return "Final Answer: Calculation failed."

        result = agent.execute_react_loop(
            query="Calculate something",
            llm_generate=mock_llm,
            max_iterations=3
        )

        # Check that error is visible in steps
        assert len(result["steps"]) > 0
        first_step = result["steps"][0]
        assert first_step.observation is not None
        assert "오류" in first_step.observation or "실패" in first_step.observation

    def test_tool_not_found_error(self, db_session, test_user):
        """Test error when tool is not found"""
        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        def mock_llm(prompt: str) -> str:
            return """
Thought: Use nonexistent tool.
Action: nonexistent_tool
Action Input: {"query": "test"}
"""

        result = agent.execute_react_loop(
            query="Test nonexistent tool",
            llm_generate=mock_llm,
            max_iterations=2
        )

        # Should have error in observation
        assert len(result["steps"]) > 0
        assert "도구를 찾을 수 없습니다" in result["steps"][0].observation

    def test_timeout_error_display(self, db_session, test_user):
        """Test that timeout errors are displayed"""
        tool = Tool(
            name="slow_tool",
            display_name="느린 도구",
            description="시간 초과 테스트",
            category="test",
            is_active=True,
            priority=1,
            timeout_seconds=1  # 1 second timeout
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        def mock_llm(prompt: str) -> str:
            return """
Thought: Use slow tool.
Action: slow_tool
Action Input: {"query": "test"}
"""

        result = agent.execute_react_loop(
            query="Timeout test",
            llm_generate=mock_llm,
            max_iterations=2
        )

        # Should show timeout error
        assert any("시간 초과" in step.observation or "timeout" in step.observation.lower()
                   for step in result["steps"] if step.observation)


class TestAuditLogging:
    """T171: Verify tool execution audit logging"""

    def test_tool_execution_logged(self, db_session, test_user):
        """Test that tool executions are logged to database"""
        tool = Tool(
            name="calculator",
            display_name="계산기",
            description="계산 도구",
            category="utility",
            is_active=True,
            priority=1
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        def mock_llm(prompt: str) -> str:
            return """
Thought: Calculate 100 + 200.
Action: calculator
Action Input: {"expression": "100 + 200"}

Final Answer: The result is 300.
"""

        result = agent.execute_react_loop(
            query="Calculate 100 + 200",
            llm_generate=mock_llm,
            max_iterations=3
        )

        # Check that execution was logged
        executions = db_session.query(ToolExecution).filter(
            ToolExecution.user_id == test_user.id,
            ToolExecution.conversation_id == conversation_id
        ).all()

        assert len(executions) > 0
        execution = executions[0]
        assert execution.tool_id == tool.id
        assert execution.success is not None
        assert execution.execution_time_ms > 0

    def test_pii_sanitization_in_logs(self, db_session, test_user):
        """Test that PII is sanitized in tool execution logs"""
        tool = Tool(
            name="calculator",
            display_name="계산기",
            description="계산 도구",
            category="utility",
            is_active=True,
            priority=1
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        def mock_llm(prompt: str) -> str:
            return """
Thought: Calculate with PII.
Action: calculator
Action Input: {"expression": "100 + 200", "user_id": "123456-1234567", "phone": "010-1234-5678"}

Final Answer: Done.
"""

        result = agent.execute_react_loop(
            query="Test PII sanitization",
            llm_generate=mock_llm,
            max_iterations=3
        )

        # Check logged parameters are sanitized
        executions = db_session.query(ToolExecution).filter(
            ToolExecution.conversation_id == conversation_id
        ).all()

        if executions:
            execution = executions[0]
            params_str = str(execution.parameters)

            # PII should be masked
            assert "123456-1234567" not in params_str
            assert "010-1234-5678" not in params_str

    def test_no_message_content_in_logs(self, db_session, test_user):
        """Test that message content is not logged (FR-056)"""
        tool = Tool(
            name="calculator",
            display_name="계산기",
            description="계산 도구",
            category="utility",
            is_active=True,
            priority=1
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        sensitive_query = "비밀 프로젝트 예산 계산: 100억원 + 50억원"

        def mock_llm(prompt: str) -> str:
            return """
Thought: Calculate budget.
Action: calculator
Action Input: {"expression": "10000000000 + 5000000000"}

Final Answer: 150억원입니다.
"""

        result = agent.execute_react_loop(
            query=sensitive_query,
            llm_generate=mock_llm,
            max_iterations=3
        )

        # Check that query content is not in tool execution logs
        executions = db_session.query(ToolExecution).all()

        for execution in executions:
            # Should not log the actual query content
            # Only parameters and results should be logged
            assert "비밀 프로젝트" not in str(execution.parameters)

    def test_execution_statistics_tracked(self, db_session, test_user):
        """Test that execution statistics are properly tracked"""
        tool = Tool(
            name="calculator",
            display_name="계산기",
            description="계산 도구",
            category="utility",
            is_active=True,
            priority=1
        )
        db_session.add(tool)
        db_session.commit()

        conversation_id = uuid4()
        agent = ReActAgentService(db_session, test_user.id, conversation_id)

        def mock_llm(prompt: str) -> str:
            return """
Thought: Calculate.
Action: calculator
Action Input: {"expression": "100 + 200"}

Final Answer: 300.
"""

        result = agent.execute_react_loop(
            query="Calculate",
            llm_generate=mock_llm,
            max_iterations=3
        )

        # Check statistics
        executions = db_session.query(ToolExecution).filter(
            ToolExecution.conversation_id == conversation_id
        ).all()

        assert len(executions) > 0

        for execution in executions:
            # All executions should have timestamps
            assert execution.created_at is not None

            # Should have execution time
            assert execution.execution_time_ms is not None
            assert execution.execution_time_ms >= 0

            # Should have success status
            assert execution.success is not None
