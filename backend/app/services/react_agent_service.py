"""
ReAct Agent Service (LangGraph Implementation)

Implements the ReAct (Reasoning and Acting) pattern using LangGraph for robust state management.
Per FR-062: Thought → Action → Observation loop, max 5 iterations.
Per FR-063: Tool execution safety (30s timeout, sandboxing).
Per FR-065: Transparent error handling.
Per FR-066: Audit logging.
"""
from typing import Dict, Any, List, Tuple, Optional, TypedDict, Annotated
from sqlalchemy.orm import Session
from uuid import UUID
import time
import json
import re
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.models.tool import Tool
from app.models.tool_execution import ToolExecution
from app.services.react_tools.document_search import DocumentSearchTool
from app.services.react_tools.calculator import CalculatorTool
from app.services.react_tools.date_schedule import DateScheduleTool
from app.services.react_tools.data_analysis import DataAnalysisTool
from app.services.react_tools.document_template import DocumentTemplateTool
from app.services.react_tools.legal_reference import LegalReferenceTool


# =====================
# State Definition
# =====================

class AgentState(TypedDict):
    """
    State for ReAct Agent

    Tracks the entire agent execution state including:
    - messages: Conversation history
    - iteration: Current iteration number
    - tools_used: List of tools that have been executed
    - previous_calls: Track identical calls to prevent loops
    - final_answer: The final answer when agent completes
    - error_count: Number of errors encountered
    """
    messages: Annotated[List[Dict[str, str]], add_messages]  # List of {role, content}
    iteration: int
    tools_used: List[str]
    previous_calls: List[str]
    final_answer: Optional[str]
    error_count: int
    query: str  # Original user query
    current_thought: str
    current_action: str
    current_action_input: Dict[str, Any]
    current_observation: str


# =====================
# ReAct Step for Display
# =====================

class ReActStep:
    """Represents a single ReAct step for display"""
    def __init__(self, iteration: int, thought: str, action: str = None, action_input: Dict = None, observation: str = None):
        self.iteration = iteration
        self.thought = thought
        self.action = action
        self.action_input = action_input
        self.observation = observation
        self.timestamp = datetime.utcnow()


# =====================
# ReAct Agent Service
# =====================

class ReActAgentService:
    """
    ReAct Agent Service (LangGraph Implementation)

    Uses LangGraph for robust state-based execution with:
    - Clear state transitions
    - Conditional branching
    - Error recovery
    - Checkpoint support (future)
    """

    MAX_ITERATIONS = 5
    TOOL_TIMEOUT = 30

    def __init__(self, db: Session, user_id: UUID, conversation_id: UUID):
        """
        Initialize ReAct agent

        Args:
            db: Database session
            user_id: User ID for audit logging
            conversation_id: Conversation ID for context
        """
        self.db = db
        self.user_id = user_id
        self.conversation_id = conversation_id

        # Initialize tools
        self.tools = {
            "document_search": DocumentSearchTool(db),
            "calculator": CalculatorTool(),
            "date_schedule": DateScheduleTool(),
            "data_analysis": DataAnalysisTool(),
            "document_template": DocumentTemplateTool(),
            "legal_reference": LegalReferenceTool(),
        }

        # Build the graph
        self.graph = self._build_graph()
        self.steps: List[ReActStep] = []

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph

        Graph structure:
        START → think → act → execute_tool → [should_continue?]
                                                ├─> continue → think (loop)
                                                └─> end → END
        """
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("think", self._think_node)
        workflow.add_node("act", self._action_node)
        workflow.add_node("execute_tool", self._execute_tool_node)

        # Add edges
        workflow.add_edge("think", "act")
        workflow.add_edge("act", "execute_tool")

        # Conditional edge: continue or end
        workflow.add_conditional_edges(
            "execute_tool",
            self._should_continue,
            {
                "continue": "think",
                "end": END
            }
        )

        # Set entry point
        workflow.set_entry_point("think")

        return workflow.compile()

    def execute_react_loop(
        self,
        query: str,
        llm_generate_func,  # Function to call LLM
        max_iterations: int = None
    ) -> Dict[str, Any]:
        """
        Execute ReAct loop using LangGraph

        Args:
            query: User query
            llm_generate_func: Function to generate LLM responses
            max_iterations: Override default max iterations

        Returns:
            Dict with final answer and execution steps
        """
        if max_iterations is None:
            max_iterations = self.MAX_ITERATIONS

        # Store LLM function for node access
        self.llm_generate_func = llm_generate_func
        self.max_iterations = max_iterations

        # Initialize state
        initial_state: AgentState = {
            "messages": [],
            "iteration": 0,
            "tools_used": [],
            "previous_calls": [],
            "final_answer": None,
            "error_count": 0,
            "query": query,
            "current_thought": "",
            "current_action": "",
            "current_action_input": {},
            "current_observation": ""
        }

        # Execute graph
        try:
            final_state = self.graph.invoke(initial_state)

            # Extract final answer
            final_answer = final_state.get("final_answer") or self._extract_final_answer(final_state)

            return {
                "final_answer": final_answer,
                "steps": self.steps,
                "total_iterations": final_state["iteration"],
                "success": final_answer is not None,
                "tools_used": final_state["tools_used"],
                "state": final_state  # Include full state for debugging
            }

        except Exception as e:
            print(f"ReAct loop error: {e}")
            return {
                "final_answer": f"에러 발생: {str(e)}",
                "steps": self.steps,
                "total_iterations": len(self.steps),
                "success": False,
                "tools_used": []
            }

    # =====================
    # Graph Nodes
    # =====================

    def _think_node(self, state: AgentState) -> AgentState:
        """
        Think Node: LLM generates thought and decides next action

        Args:
            state: Current agent state

        Returns:
            Updated state with thought
        """
        try:
            # Build prompt with context
            prompt = self._build_prompt(state)

            # Generate thought
            thought_text = self.llm_generate_func(prompt)

            # Update state
            state["current_thought"] = thought_text
            state["messages"].append({"role": "assistant", "content": thought_text})

            return state

        except Exception as e:
            state["current_thought"] = f"사고 생성 오류: {str(e)}"
            state["error_count"] += 1
            return state

    def _action_node(self, state: AgentState) -> AgentState:
        """
        Action Node: Parse action from thought

        Args:
            state: Current agent state

        Returns:
            Updated state with parsed action
        """
        try:
            thought_text = state["current_thought"]

            # Parse action and input
            action, action_input = self._parse_action(thought_text)

            # Update state
            state["current_action"] = action
            state["current_action_input"] = action_input

            # Increment iteration
            state["iteration"] += 1

            return state

        except Exception as e:
            state["current_observation"] = f"액션 파싱 오류: {str(e)}"
            state["error_count"] += 1
            return state

    def _execute_tool_node(self, state: AgentState) -> AgentState:
        """
        Execute Tool Node: Execute the selected tool

        Args:
            state: Current agent state

        Returns:
            Updated state with observation
        """
        action = state["current_action"]
        action_input = state["current_action_input"]
        iteration = state["iteration"]

        # Check for "Final Answer"
        if action == "Final Answer":
            final_answer = action_input.get("answer", state["current_thought"])
            state["final_answer"] = final_answer
            state["current_observation"] = final_answer

            # Record step
            step = ReActStep(
                iteration=iteration,
                thought=state["current_thought"],
                action="Final Answer",
                observation=final_answer
            )
            self.steps.append(step)

            return state

        # Execute tool
        observation = self._execute_tool_safe(action, action_input, iteration, state)

        # Update state
        state["current_observation"] = observation

        # Track tool usage
        if action not in state["tools_used"]:
            state["tools_used"].append(action)

        # Record step
        step = ReActStep(
            iteration=iteration,
            thought=state["current_thought"],
            action=action,
            action_input=action_input,
            observation=observation
        )
        self.steps.append(step)

        return state

    def _should_continue(self, state: AgentState) -> str:
        """
        Decide whether to continue or end

        Args:
            state: Current agent state

        Returns:
            "continue" or "end"
        """
        # Check if final answer reached
        if state.get("final_answer"):
            return "end"

        # Check max iterations
        if state["iteration"] >= self.max_iterations:
            # Generate summary as final answer
            state["final_answer"] = self._generate_summary(state)
            return "end"

        # Check too many errors
        if state["error_count"] >= 3:
            state["final_answer"] = f"너무 많은 오류가 발생했습니다 ({state['error_count']}회). 다시 시도해주세요."
            return "end"

        # Continue
        return "continue"

    # =====================
    # Helper Methods
    # =====================

    def _build_prompt(self, state: AgentState) -> str:
        """Build prompt for LLM with context"""
        query = state["query"]
        iteration = state["iteration"]

        # Build context from previous steps
        context = ""
        if state["messages"]:
            context = "\n\n이전 단계:\n"
            for i, step in enumerate(self.steps):
                context += f"\n[단계 {step.iteration}]\n"
                context += f"🤔 Thought: {step.thought[:150]}...\n"
                if step.action:
                    context += f"⚙️ Action: {step.action}\n"
                if step.observation:
                    context += f"👁️ Observation: {step.observation[:200]}...\n"

        prompt = f"""당신은 도구를 사용할 수 있는 ReAct 에이전트입니다.

사용 가능한 도구:
{self._format_available_tools()}

사용자 질문: {query}

현재 반복: {iteration + 1}/{self.max_iterations}

{context}

다음 형식으로 응답하세요:
Thought: [현재 상황 분석 및 다음 행동 계획]
Action: [도구 이름 또는 "Final Answer"]
Action Input: {{"param": "value"}} 또는 최종 답변

예시 1 (도구 사용):
Thought: 사용자가 예산 계산을 요청했으므로 calculator 도구를 사용해야 합니다.
Action: calculator
Action Input: {{"expression": "1000만원 + 500만원"}}

예시 2 (최종 답변):
Thought: 모든 정보를 수집했으므로 최종 답변을 제공할 수 있습니다.
Action: Final Answer
Action Input: {{"answer": "예산 총액은 1,500만원입니다."}}

중요:
- 이전 단계에서 얻은 정보를 활용하세요.
- 같은 도구를 같은 파라미터로 반복 호출하지 마세요.
- 충분한 정보를 얻었다면 Final Answer로 답변하세요.
"""

        return prompt

    def _parse_action(self, thought_text: str) -> Tuple[str, Dict]:
        """Parse action from thought text"""
        # Extract Action
        action_match = re.search(r'Action:\s*(.+)', thought_text)
        if not action_match:
            # No explicit action, treat as final answer
            return "Final Answer", {"answer": thought_text}

        action = action_match.group(1).strip()

        # Extract Action Input
        input_match = re.search(r'Action Input:\s*(\{.+?\})', thought_text, re.DOTALL)
        if input_match:
            try:
                action_input = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                # Try to extract simple key-value
                action_input = {"raw": input_match.group(1)}
        else:
            # No explicit input, try to extract from text after "Action Input:"
            input_line_match = re.search(r'Action Input:\s*(.+)', thought_text)
            if input_line_match:
                input_text = input_line_match.group(1).strip()
                # Try to parse as JSON
                if input_text.startswith('{'):
                    try:
                        action_input = json.loads(input_text)
                    except:
                        action_input = {"answer": input_text}
                else:
                    action_input = {"answer": input_text}
            else:
                action_input = {}

        return action, action_input

    def _execute_tool_safe(
        self,
        tool_name: str,
        parameters: Dict,
        iteration: int,
        state: AgentState
    ) -> str:
        """
        Execute a tool with safety measures

        Per FR-063: 30-second timeout, sandboxing
        Per FR-066: Audit logging
        """
        start_time = time.time()

        try:
            # Check for identical call (prevent loops)
            call_signature = f"{tool_name}:{str(parameters)}"
            if call_signature in state["previous_calls"]:
                return f"⚠️ 이 도구는 이미 같은 파라미터로 호출되었습니다. 다른 접근을 시도하세요."

            state["previous_calls"].append(call_signature)

            # Get tool
            if tool_name not in self.tools:
                return f"❌ 알 수 없는 도구: {tool_name}. 사용 가능한 도구: {', '.join(self.tools.keys())}"

            tool = self.tools[tool_name]

            # Validate parameters
            is_valid, error_msg = tool.validate_parameters(parameters)
            if not is_valid:
                return f"❌ 파라미터 오류: {error_msg}"

            # Execute with timeout
            try:
                if tool_name == "document_search":
                    result = tool.execute(conversation_id=self.conversation_id, **parameters)
                else:
                    result = tool.execute(**parameters)

                success = True
                error_message = None

            except Exception as e:
                result = f"도구 실행 오류: {str(e)}"
                success = False
                error_message = str(e)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Log execution (FR-066)
            self._log_tool_execution(
                tool_name=tool_name,
                parameters=parameters,
                iteration=iteration,
                success=success,
                result=result[:500] if result else None,
                error_message=error_message,
                execution_time_ms=execution_time_ms
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_result = f"도구 실행 중 예외 발생: {str(e)}"

            # Log error
            self._log_tool_execution(
                tool_name=tool_name,
                parameters=parameters,
                iteration=iteration,
                success=False,
                result=None,
                error_message=str(e),
                execution_time_ms=execution_time_ms
            )

            return error_result

    def _log_tool_execution(
        self,
        tool_name: str,
        parameters: Dict,
        iteration: int,
        success: bool,
        result: str,
        error_message: str,
        execution_time_ms: int
    ):
        """Log tool execution for audit trail (FR-066)"""
        try:
            # Get tool_id
            tool = self.db.query(Tool).filter(Tool.name == tool_name).first()
            if not tool:
                return

            # Sanitize parameters
            sanitized_params = ToolExecution.sanitize_parameters(parameters)

            # Create execution log
            execution_log = ToolExecution(
                tool_id=tool.id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
                agent_iteration=iteration,
                parameters=sanitized_params,
                success=success,
                result=result,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
            )

            self.db.add(execution_log)
            self.db.commit()

            # Update tool statistics
            tool.increment_usage(success, execution_time_ms)
            self.db.commit()

        except Exception as e:
            print(f"Failed to log tool execution: {e}")
            self.db.rollback()

    def _format_available_tools(self) -> str:
        """Format list of available tools"""
        tool_descriptions = []
        for name, tool in self.tools.items():
            definition = tool.get_tool_definition()
            tool_descriptions.append(f"- {definition['display_name']} ({name}): {definition['description']}")

        return "\n".join(tool_descriptions)

    def _generate_summary(self, state: AgentState) -> str:
        """Generate summary when max iterations reached"""
        summary_lines = [
            f"죄송합니다. {self.max_iterations}회 시도 후에도 완전한 답변을 생성하지 못했습니다.\n",
            "현재까지의 진행 상황:\n"
        ]

        for step in self.steps:
            summary_lines.append(f"\n🤔 단계 {step.iteration}:")
            summary_lines.append(f"  생각: {step.thought[:100]}...")
            if step.action:
                summary_lines.append(f"  행동: {step.action}")
            if step.observation:
                summary_lines.append(f"  결과: {step.observation[:150]}...")

        return "\n".join(summary_lines)

    def _extract_final_answer(self, state: AgentState) -> str:
        """Extract final answer from state if not explicitly set"""
        if state.get("final_answer"):
            return state["final_answer"]

        # Try to extract from last observation
        if self.steps and self.steps[-1].observation:
            return self.steps[-1].observation

        return "답변을 생성하지 못했습니다."
