"""
Multi-Agent Orchestrator with LangGraph

Routes user queries to appropriate agents and manages workflows.
Supports single agent, sequential, and parallel execution.

Features:
- LLM-based intent classification with few-shot examples
- Sequential workflows with context sharing (FR-072, FR-077)
- Parallel execution for independent tasks (max 3, FR-078)
- Error handling and workflow timeout (5 min, FR-079)
- Execution logging (FR-075)
- Keyword-based fallback option (FR-076)
"""

import asyncio
import time
from typing import TypedDict, Dict, List, Optional
from pathlib import Path

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[WARNING] LangGraph not installed. Install with: pip install langgraph langchain-core")

from .llm_service_factory import get_llm_service
from .base_llm_service import BaseLLMService
from .agents import (
    CitizenSupportAgent,
    DocumentWritingAgent,
    LegalResearchAgent,
    DataAnalysisAgent,
    ReviewAgent,
)


class AgentState(TypedDict):
    """State for multi-agent workflow"""
    user_query: str
    conversation_history: list
    current_agent: str
    agent_outputs: Dict[str, str]  # {agent_name: response}
    workflow_type: str  # "single", "sequential", "parallel"
    agent_sequence: List[str]  # For sequential/parallel workflows
    errors: list
    execution_log: list


class MultiAgentOrchestrator:
    """
    LangGraph-based Multi-Agent Orchestrator

    Workflow Types:
    1. Single: Route to one agent
    2. Sequential: Chain multiple agents (context shared)
    3. Parallel: Execute independent agents concurrently (max 3)
    """

    def __init__(self):
        """Initialize orchestrator with all agents and LLM service"""
        # Initialize agents
        self.agents = {
            "citizen_support": CitizenSupportAgent(),
            "document_writing": DocumentWritingAgent(),
            "legal_research": LegalResearchAgent(),
            "data_analysis": DataAnalysisAgent(),
            "review": ReviewAgent(),
        }

        # LLM service for intent classification
        self.llm: BaseLLMService = get_llm_service()

        # Load orchestrator few-shot prompt
        self.orchestrator_prompt = self._load_orchestrator_prompt()

        # Build LangGraph workflow
        if LANGGRAPH_AVAILABLE:
            self.workflow = self._build_workflow()
        else:
            print("[WARNING] LangGraph not available. Falling back to keyword-based routing.")
            self.workflow = None

    def _load_orchestrator_prompt(self) -> str:
        """Load few-shot orchestrator prompt from file"""
        prompt_file = Path("backend/prompts/orchestrator_few_shot.txt")

        try:
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                print(f"[WARNING] Orchestrator prompt file not found: {prompt_file}")
                return self._get_default_orchestrator_prompt()
        except Exception as e:
            print(f"[WARNING] Failed to load orchestrator prompt: {e}")
            return self._get_default_orchestrator_prompt()

    def _get_default_orchestrator_prompt(self) -> str:
        """Get default orchestrator prompt"""
        return """당신은 Multi-Agent 시스템의 Orchestrator입니다.
사용자의 질문을 분석하여 적절한 에이전트로 라우팅합니다.

Available Agents:
- citizen_support: 민원 지원
- document_writing: 문서 작성
- legal_research: 법규 검색
- data_analysis: 데이터 분석
- review: 문서 검토

응답 형식: "agent_name|single" 또는 "agent1,agent2|sequential" 또는 "agent1,agent2,agent3|parallel"
"""

    def _build_workflow(self) -> Optional[StateGraph]:
        """Build LangGraph state machine"""
        if not LANGGRAPH_AVAILABLE:
            return None

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("execute_single_agent", self._execute_single_agent)
        workflow.add_node("execute_sequential", self._execute_sequential)
        workflow.add_node("execute_parallel", self._execute_parallel)

        # Define edges
        workflow.set_entry_point("classify_intent")

        workflow.add_conditional_edges(
            "classify_intent",
            self._route_workflow_type,
            {
                "single": "execute_single_agent",
                "sequential": "execute_sequential",
                "parallel": "execute_parallel",
            }
        )

        workflow.add_edge("execute_single_agent", END)
        workflow.add_edge("execute_sequential", END)
        workflow.add_edge("execute_parallel", END)

        return workflow.compile()

    async def _classify_intent_node(self, state: AgentState) -> AgentState:
        """
        Classify user intent using LLM with few-shot examples

        Output format: "agent_name|workflow_type" or "agent1,agent2|workflow_type"
        """
        user_query = state["user_query"]

        # Build classification prompt
        full_prompt = f"{self.orchestrator_prompt}\n\nUser Query: {user_query}\nClassification:"

        try:
            # Use LLM to classify
            response = await self.llm.generate(
                prompt=full_prompt,
                max_tokens=100,
                temperature=0.3  # Low temperature for consistent classification
            )

            # Parse response: "agent_name(s)|workflow_type"
            classification = response.strip()
            agents_part, workflow_part = classification.split("|")

            agent_names = [name.strip() for name in agents_part.split(",")]
            workflow_type = workflow_part.strip()

            state["agent_sequence"] = agent_names
            state["workflow_type"] = workflow_type

            # Set current agent (for single workflow)
            if workflow_type == "single" and agent_names:
                state["current_agent"] = agent_names[0]

            state["execution_log"].append({
                "stage": "classification",
                "agents": agent_names,
                "workflow_type": workflow_type,
                "timestamp": time.time()
            })

        except Exception as e:
            # Fallback to keyword-based classification
            print(f"[Orchestrator] LLM classification failed: {e}. Falling back to keyword-based.")
            self._classify_by_keywords(state)

        return state

    def _classify_by_keywords(self, state: AgentState):
        """Keyword-based fallback classification"""
        query = state["user_query"].lower()

        # Simple keyword matching
        if any(word in query for word in ["전입", "전출", "민원", "절차", "어떻게", "신청"]):
            state["current_agent"] = "citizen_support"
            state["agent_sequence"] = ["citizen_support"]
        elif any(word in query for word in ["보고서", "공문", "안내문", "작성"]):
            state["current_agent"] = "document_writing"
            state["agent_sequence"] = ["document_writing"]
        elif any(word in query for word in ["법령", "조례", "법률", "규정"]):
            state["current_agent"] = "legal_research"
            state["agent_sequence"] = ["legal_research"]
        elif any(word in query for word in ["데이터", "통계", "분석", "추이"]):
            state["current_agent"] = "data_analysis"
            state["agent_sequence"] = ["data_analysis"]
        elif any(word in query for word in ["검토", "확인", "수정"]):
            state["current_agent"] = "review"
            state["agent_sequence"] = ["review"]
        else:
            # Default to citizen_support
            state["current_agent"] = "citizen_support"
            state["agent_sequence"] = ["citizen_support"]

        state["workflow_type"] = "single"

    def _route_workflow_type(self, state: AgentState) -> str:
        """Route to appropriate workflow executor"""
        return state["workflow_type"]

    async def _execute_single_agent(self, state: AgentState) -> AgentState:
        """Execute single agent"""
        agent_name = state["current_agent"]
        agent = self.agents.get(agent_name)

        if not agent:
            state["errors"].append({"agent": agent_name, "error": "Agent not found"})
            return state

        try:
            context = {"conversation_history": state["conversation_history"]}
            response = await agent.process(state["user_query"], context)

            state["agent_outputs"][agent_name] = response
            state["execution_log"].append({
                "agent": agent_name,
                "status": "success",
                "timestamp": time.time()
            })

        except Exception as e:
            state["errors"].append({"agent": agent_name, "error": str(e)})
            state["execution_log"].append({
                "agent": agent_name,
                "status": "error",
                "timestamp": time.time()
            })

        return state

    async def _execute_sequential(self, state: AgentState) -> AgentState:
        """Execute agents sequentially with context sharing (FR-072, FR-077)"""
        agent_sequence = state["agent_sequence"][:5]  # Max 5 agents (FR-079)

        for agent_name in agent_sequence:
            agent = self.agents.get(agent_name)

            if not agent:
                state["errors"].append({"agent": agent_name, "error": "Agent not found"})
                break

            try:
                # Share context from previous agents (FR-077)
                context = {
                    "conversation_history": state["conversation_history"],
                    "previous_outputs": state["agent_outputs"]
                }

                response = await agent.process(state["user_query"], context)
                state["agent_outputs"][agent_name] = response
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "success",
                    "timestamp": time.time()
                })

            except Exception as e:
                # Stop workflow on failure (FR-073)
                state["errors"].append({"agent": agent_name, "error": str(e)})
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "error",
                    "timestamp": time.time()
                })
                break

        return state

    async def _execute_parallel(self, state: AgentState) -> AgentState:
        """Execute agents in parallel (max 3, FR-078)"""
        agent_sequence = state["agent_sequence"][:3]  # Max 3 parallel agents

        # Create parallel tasks
        tasks = []
        for agent_name in agent_sequence:
            agent = self.agents.get(agent_name)
            if agent:
                context = {"conversation_history": state["conversation_history"]}
                tasks.append((agent_name, agent.process(state["user_query"], context)))

        # Execute in parallel
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        # Process results
        for (agent_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                state["errors"].append({"agent": agent_name, "error": str(result)})
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "error",
                    "timestamp": time.time()
                })
            else:
                state["agent_outputs"][agent_name] = result
                state["execution_log"].append({
                    "agent": agent_name,
                    "status": "success",
                    "timestamp": time.time()
                })

        return state

    async def route_and_execute(
        self,
        user_query: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Route query to appropriate workflow and execute

        Args:
            user_query: User's question or request
            context: Optional context dict containing conversation_history

        Returns:
            Dict with execution results:
            {
                "status": "success" | "partial" | "timeout",
                "agent_outputs": {agent_name: response},
                "workflow_type": "single" | "sequential" | "parallel",
                "execution_log": [...],
                "errors": [...],
                "execution_time_ms": int
            }
        """
        if context is None:
            context = {}

        # Initialize state
        initial_state: AgentState = {
            "user_query": user_query,
            "conversation_history": context.get("conversation_history", []),
            "current_agent": "",
            "agent_outputs": {},
            "workflow_type": "single",
            "agent_sequence": [],
            "errors": [],
            "execution_log": []
        }

        start_time = time.time()

        # Execute workflow with streaming (Phase 1.1: ainvoke → astream)
        if self.workflow:
            # LangGraph workflow with streaming
            try:
                final_state = None

                # Stream with timeout
                async def stream_with_timeout():
                    nonlocal final_state
                    # Phase 1.2: Add "messages" for LLM token streaming
                    async for chunk in self.workflow.astream(initial_state, stream_mode=["updates", "messages"]):
                        # chunk is a tuple: (node_name, state_updates)
                        if isinstance(chunk, tuple) and len(chunk) == 2:
                            node_name, state_updates = chunk

                            # Initialize final_state on first chunk
                            if final_state is None:
                                final_state = initial_state.copy()

                            # Update state with new data
                            final_state.update(state_updates)

                await asyncio.wait_for(stream_with_timeout(), timeout=300)

                # Ensure we have a final state
                if final_state is None:
                    raise RuntimeError("Graph execution completed without producing any state")

            except asyncio.TimeoutError:
                return {
                    "status": "timeout",
                    "message": "워크플로우 실행 시간 초과 (5분)",
                    "execution_time_ms": 300000
                }
        else:
            # Fallback to simple execution
            final_state = await self._simple_fallback_execution(initial_state)

        execution_time = time.time() - start_time

        return {
            "status": "success" if not final_state["errors"] else "partial",
            "agent_outputs": final_state["agent_outputs"],
            "workflow_type": final_state["workflow_type"],
            "execution_log": final_state["execution_log"],
            "errors": final_state["errors"],
            "execution_time_ms": int(execution_time * 1000)
        }

    async def _simple_fallback_execution(self, state: AgentState) -> AgentState:
        """Simple fallback execution without LangGraph"""
        self._classify_by_keywords(state)
        return await self._execute_single_agent(state)
