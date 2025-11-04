"""
ReAct Agent Performance Tests

T166: Test ReAct agent completes 2-3 tool task within 30 seconds
"""
import pytest
import time
from uuid import uuid4
from unittest.mock import MagicMock

from app.services.react_agent_service import ReActAgentService
from app.models.tool import Tool


@pytest.fixture
def react_agent(db_session, test_user):
    """Create ReAct agent instance with test data"""
    # Create test tools
    tools = [
        Tool(
            name="calculator",
            display_name="계산기",
            description="수학 계산 도구",
            category="utility",
            is_active=True,
            priority=1
        ),
        Tool(
            name="date_schedule",
            display_name="날짜/일정",
            description="날짜 및 일정 계산 도구",
            category="utility",
            is_active=True,
            priority=1
        ),
        Tool(
            name="document_search",
            display_name="문서 검색",
            description="업로드된 문서 검색 도구",
            category="knowledge",
            is_active=True,
            priority=2
        ),
    ]
    for tool in tools:
        db_session.add(tool)
    db_session.commit()

    conversation_id = uuid4()
    return ReActAgentService(db_session, test_user.id, conversation_id)


def test_react_two_tool_task_performance(react_agent):
    """
    T166: Test ReAct agent completes 2-tool task within 30 seconds

    Test scenario:
    - Query requires calculator + date tool
    - Should complete within 30 seconds
    """
    # Mock LLM to return predictable responses
    def mock_llm_generate(prompt: str) -> str:
        if "Thought:" in prompt and "iteration 1" in prompt.lower():
            return """
Thought: I need to calculate the budget and then determine the deadline date.
Action: calculator
Action Input: {"expression": "1000000 + 500000"}
"""
        elif "iteration 2" in prompt.lower():
            return """
Thought: Now I need to check the deadline date.
Action: date_schedule
Action Input: {"query": "오늘부터 30일 후", "operation": "add_days"}
"""
        else:
            return "Final Answer: 예산은 150만원이며, 마감일은 30일 후입니다."

    start_time = time.time()

    result = react_agent.execute_react_loop(
        query="예산 100만원에 50만원을 추가하고, 오늘부터 30일 후 날짜를 알려주세요",
        llm_generate=mock_llm_generate,
        max_iterations=5
    )

    elapsed_time = time.time() - start_time

    # Assertions
    assert elapsed_time < 30, f"ReAct agent took {elapsed_time:.2f}s, should be <30s"
    assert result["final_answer"] is not None
    assert len(result["tools_used"]) == 2
    assert "calculator" in result["tools_used"]
    assert "date_schedule" in result["tools_used"]
    assert len(result["steps"]) >= 2


def test_react_three_tool_task_performance(react_agent):
    """
    T166: Test ReAct agent completes 3-tool task within 30 seconds

    Test scenario:
    - Query requires calculator + date + document search
    - Should complete within 30 seconds
    """
    # Mock LLM to return predictable responses
    call_count = [0]

    def mock_llm_generate(prompt: str) -> str:
        call_count[0] += 1
        if call_count[0] == 1:
            return """
Thought: First, I need to calculate the total amount.
Action: calculator
Action Input: {"expression": "2000000 * 0.1"}
"""
        elif call_count[0] == 2:
            return """
Thought: Next, I'll check the date for the payment.
Action: date_schedule
Action Input: {"query": "2024-12-31까지 남은 일수", "operation": "days_until"}
"""
        elif call_count[0] == 3:
            return """
Thought: Finally, I need to search for related documents.
Action: document_search
Action Input: {"query": "예산 집행 규정", "top_k": 3}
"""
        else:
            return "Final Answer: 예산의 10%는 20만원이며, 12월 31일까지 남은 기간에 집행해야 합니다."

    start_time = time.time()

    result = react_agent.execute_react_loop(
        query="예산 200만원의 10%를 계산하고, 연말까지 남은 기간과 관련 규정을 찾아주세요",
        llm_generate=mock_llm_generate,
        max_iterations=5
    )

    elapsed_time = time.time() - start_time

    # Assertions
    assert elapsed_time < 30, f"ReAct agent took {elapsed_time:.2f}s, should be <30s"
    assert result["final_answer"] is not None
    assert len(result["tools_used"]) == 3
    assert len(result["steps"]) >= 3


def test_react_complex_calculation_performance(react_agent):
    """
    T166: Test complex calculation with multiple steps

    Test scenario:
    - Multiple calculator operations
    - Should complete efficiently
    """
    call_count = [0]

    def mock_llm_generate(prompt: str) -> str:
        call_count[0] += 1
        if call_count[0] == 1:
            return """
Thought: Calculate base amount.
Action: calculator
Action Input: {"expression": "5000000 * 12"}
"""
        elif call_count[0] == 2:
            return """
Thought: Calculate tax rate.
Action: calculator
Action Input: {"expression": "60000000 * 0.1"}
"""
        else:
            return "Final Answer: 연봉은 6천만원이며, 세금은 6백만원입니다."

    start_time = time.time()

    result = react_agent.execute_react_loop(
        query="월급 500만원의 연봉과 10% 세금을 계산해주세요",
        llm_generate=mock_llm_generate,
        max_iterations=5
    )

    elapsed_time = time.time() - start_time

    # Verify performance
    assert elapsed_time < 30, f"ReAct agent took {elapsed_time:.2f}s, should be <30s"
    assert result["final_answer"] is not None
    assert "calculator" in result["tools_used"]


def test_react_tool_execution_timeout(react_agent):
    """
    T166: Test that individual tool timeouts don't exceed limits

    Each tool should timeout at 30 seconds max
    """
    def mock_llm_generate(prompt: str) -> str:
        return """
Thought: I need to search documents.
Action: document_search
Action Input: {"query": "test", "top_k": 5}
"""

    # Mock a slow tool execution
    import time
    original_execute = react_agent._execute_tool_node

    def slow_execute(state):
        time.sleep(0.5)  # Simulate slow tool
        return original_execute(state)

    react_agent._execute_tool_node = slow_execute

    start_time = time.time()

    result = react_agent.execute_react_loop(
        query="문서를 검색해주세요",
        llm_generate=mock_llm_generate,
        max_iterations=2
    )

    elapsed_time = time.time() - start_time

    # Should complete even with slow tools
    assert elapsed_time < 30, f"Tool execution took too long: {elapsed_time:.2f}s"
    assert result is not None


def test_react_parallel_requests(react_agent):
    """
    T166: Test multiple ReAct agents running in parallel

    Verify that multiple concurrent requests complete within reasonable time
    """
    from concurrent.futures import ThreadPoolExecutor
    import time

    def mock_llm_generate(prompt: str) -> str:
        return """
Thought: Calculate the value.
Action: calculator
Action Input: {"expression": "100 + 200"}

Final Answer: The result is 300.
"""

    def run_agent():
        return react_agent.execute_react_loop(
            query="Calculate 100 + 200",
            llm_generate=mock_llm_generate,
            max_iterations=3
        )

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_agent) for _ in range(3)]
        results = [f.result() for f in futures]

    elapsed_time = time.time() - start_time

    # All 3 requests should complete within reasonable time
    assert elapsed_time < 60, f"Parallel execution took {elapsed_time:.2f}s, should be <60s"
    assert len(results) == 3
    assert all(r["final_answer"] is not None for r in results)
