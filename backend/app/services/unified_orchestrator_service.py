"""
Unified Orchestrator with 3-Way Intelligent Routing

Unifies ReAct Agent and Multi-Agent systems into single intelligent architecture.

Routing Paths:
1. Direct Path: Base LLM responds to clear and simple queries (0.5-1s)
2. Reasoning Path: Intent clarification for ambiguous queries (1-3s)
3. Specialized Path: Multi-agent system with domain experts (5-15s)

Requirements: FR-129 to FR-136
Success Criteria: SC-046 to SC-051
"""

import time
from enum import Enum
from typing import TypedDict, Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[WARNING] LangGraph not installed. Install with: pip install langgraph langchain-core")

from .llm_service_factory import get_llm_service
from .base_llm_service import BaseLLMService
from .orchestrator_service import MultiAgentOrchestrator
from .semantic_router import semantic_router


class RouteType(str, Enum):
    """Routing decision types (FR-129)"""
    DIRECT = "direct"
    REASONING = "reasoning"
    SPECIALIZED = "specialized"


class UnifiedAgentState(TypedDict):
    """
    Unified state for LangGraph workflow (FR-134)

    Tracks the complete lifecycle of query processing across all 3 paths.
    """
    # Input
    query: str
    conversation_history: List[Dict[str, str]]
    user_id: Optional[str]

    # Classification
    route: str  # "direct" | "reasoning" | "specialized"
    complexity: str  # "simple" | "ambiguous" | "complex"
    classification_confidence: float
    classification_method: str  # "keyword" | "llm"

    # Reasoning Path
    clarified_intent: Optional[str]
    missing_context: List[str]
    refined_query: Optional[str]
    rerouted_to: Optional[str]  # "direct" | "specialized"

    # Specialized Path
    agent_type: Optional[str]
    agent_sequence: List[str]
    agent_outputs: Dict[str, str]
    tools_used: List[str]

    # Output
    final_response: str
    processing_time_ms: int

    # Logging
    execution_log: List[Dict[str, Any]]
    error: Optional[str]


class UnifiedOrchestrator:
    """
    Unified 3-Way Routing Orchestrator (FR-129)

    Intelligently routes queries to optimal execution path:
    - Direct: Clear queries → Base LLM (fast)
    - Reasoning: Ambiguous queries → Clarify intent → Reroute
    - Specialized: Complex tasks → Multi-agent system

    Performance targets (FR-135):
    - Direct path P95 < 1.5s
    - Reasoning path 1-3s
    - Specialized path 5-15s
    - Keyword classification < 10ms
    """

    def __init__(self):
        """Initialize unified orchestrator with keyword dictionaries and LangGraph workflow"""
        # LLM service for base generation and classification
        self.llm: BaseLLMService = get_llm_service()

        # Multi-agent orchestrator for specialized path (lazy init)
        self._multi_agent: Optional[MultiAgentOrchestrator] = None

        # Keyword dictionaries for fast classification (FR-130)
        self.route_keywords = {
            RouteType.DIRECT: {
                # Clear & simple queries
                "greetings": ["안녕", "감사", "고마워", "반가워"],
                "definitions": ["이란", "무엇", "뭐야", "설명", "정의", "의미"],
                "simple_questions": ["어디", "언제", "누구", "왜", "어떻게"],
            },
            RouteType.REASONING: {
                # Ambiguous intent (verb without object)
                "vague_actions": ["해줘", "좀", "부탁", "도와", "확인", "알아봐", "처리"],
            },
            RouteType.SPECIALIZED: {
                # Clearly complex tasks requiring domain expertise
                "document_tasks": ["작성", "보고서", "공문", "문서", "초안"],
                "legal_tasks": ["법령", "조례", "규정", "법률", "조항"],
                "analysis_tasks": ["분석", "데이터", "통계", "집계", "요약"],
                "review_tasks": ["검토", "확인", "점검", "심사"],
            }
        }

        # Build LangGraph main workflow (FR-134)
        if LANGGRAPH_AVAILABLE:
            self.graph = self._build_main_graph()
        else:
            print("[ERROR] LangGraph is required for UnifiedOrchestrator")
            self.graph = None

    @property
    def multi_agent(self) -> MultiAgentOrchestrator:
        """Lazy initialization of multi-agent orchestrator"""
        if self._multi_agent is None:
            self._multi_agent = MultiAgentOrchestrator()
        return self._multi_agent

    def _build_main_graph(self) -> Any:
        """
        Build LangGraph main workflow (FR-134, T342)

        Graph structure:
        START → classify → (direct_node | reasoning_node | specialized_node) → finalize → END

        Nodes:
        - classify: Fast keyword + LLM fallback classification
        - direct_node: Base LLM response
        - reasoning_node: Intent clarification → reroute
        - specialized_node: Multi-agent execution
        - finalize: Response aggregation and logging
        """
        # Create state graph
        workflow = StateGraph(UnifiedAgentState)

        # Add nodes (will implement in T343-T351)
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("direct_node", self._direct_node)
        workflow.add_node("reasoning_node", self._reasoning_node)
        workflow.add_node("specialized_node", self._specialized_node)
        workflow.add_node("finalize", self._finalize_node)

        # Set entry point
        workflow.set_entry_point("classify")

        # Add conditional edges from classify to execution nodes
        workflow.add_conditional_edges(
            "classify",
            self._route_decision,
            {
                "direct": "direct_node",
                "reasoning": "reasoning_node",
                "specialized": "specialized_node",
            }
        )

        # Add edges from execution nodes to finalize
        workflow.add_edge("direct_node", "finalize")
        workflow.add_edge("reasoning_node", "finalize")
        workflow.add_edge("specialized_node", "finalize")

        # Add edge from finalize to END
        workflow.add_edge("finalize", END)

        # Compile workflow
        return workflow.compile()

    # ============================================================
    # Classification Implementation (T343-T346)
    # ============================================================

    def _fast_classify(self, query: str) -> Tuple[str, float]:
        """
        Fast keyword-based classification (T343, FR-130)

        Performance target: < 10ms average (SC-048)

        Returns:
            (route, confidence) tuple
        """
        query_lower = query.lower().strip()
        query_len = len(query)

        # Count keyword matches per route
        scores = {
            RouteType.DIRECT: 0,
            RouteType.REASONING: 0,
            RouteType.SPECIALIZED: 0,
        }

        # Score each route based on keyword presence
        for route_type, categories in self.route_keywords.items():
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        scores[route_type] += 1

        # High-confidence shortcuts (FR-130)
        # 1. Short greeting queries → Direct (high confidence)
        if query_len < 10 and scores[RouteType.DIRECT] > 0:
            return (RouteType.DIRECT, 0.95)

        # 2. Ambiguous pattern (vague verbs) + short query → Reasoning
        if query_len < 15 and scores[RouteType.REASONING] > 0:
            return (RouteType.REASONING, 0.9)

        # 3. Multiple clearly complex keywords → Specialized
        if scores[RouteType.SPECIALIZED] >= 2:
            return (RouteType.SPECIALIZED, 0.85)

        # Calculate confidence based on score distribution
        total_score = sum(scores.values())
        if total_score == 0:
            # No keyword matches → Default to Direct with low confidence (LLM fallback)
            return (RouteType.DIRECT, 0.3)

        # Find route with highest score
        max_route = max(scores, key=scores.get)
        max_score = scores[max_route]
        confidence = max_score / total_score if total_score > 0 else 0.3

        return (max_route, confidence)

    async def _llm_classify(self, query: str) -> Tuple[str, float]:
        """
        LLM-based classification fallback (T344, FR-130)

        Used when keyword classification confidence < 0.7

        Returns:
            (route, confidence) tuple
        """
        classification_prompt = f"""사용자 쿼리의 의도가 명확한지 분석하고 적절한 경로를 분류하세요.

분류 기준:
1. DIRECT - 의도가 명확하고 단순한 질문
   - 인사말, 감사 표현
   - 설명이나 정의 요청
   - 간단한 질문 (예: "LLM이란?", "오늘 날짜 알려줘")

2. REASONING - 의도가 애매하여 명확화가 필요한 질문
   - 막연한 요청 (예: "분석해줘", "검색해줘", "도와줘")
   - 구체적인 대상이나 맥락 없는 동사
   - 사용자가 무엇을 원하는지 불분명

3. SPECIALIZED - 전문 영역의 복잡한 작업
   - 문서 작성 (보고서, 공문, 초안)
   - 법령 검색 및 해석
   - 데이터 분석
   - 검토 작업

사용자 쿼리: "{query}"

위 쿼리를 분석하여 하나의 단어로 응답하세요: DIRECT, REASONING, SPECIALIZED 중 하나만 답변하세요."""

        try:
            # Call LLM with low temperature for consistent classification
            response = await self.llm.generate(
                prompt=classification_prompt,
                max_tokens=10,
                temperature=0.1
            )

            response_upper = response.strip().upper()

            # Parse response for route keywords
            if "DIRECT" in response_upper:
                return (RouteType.DIRECT, 0.8)
            elif "REASONING" in response_upper:
                return (RouteType.REASONING, 0.8)
            elif "SPECIALIZED" in response_upper:
                return (RouteType.SPECIALIZED, 0.8)
            else:
                # Fallback to DIRECT with low confidence
                print(f"[WARNING] LLM classification returned unexpected response: {response}")
                return (RouteType.DIRECT, 0.5)

        except Exception as e:
            print(f"[ERROR] LLM classification failed: {str(e)}")
            # Default to DIRECT path on error
            return (RouteType.DIRECT, 0.5)

    async def _classify_node(self, state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Classification node (T345)

        Uses Semantic Router for fast classification:
        1. Keyword matching (< 1ms, 90% hit rate)
        2. Embedding similarity fallback (< 10ms)

        Replaces slow LLM classification (0.5s) with deterministic routing (0.002s avg).
        """
        start_time = time.time()
        query = state["query"]

        # Use Semantic Router for classification (keyword + embedding)
        route = semantic_router.classify(query)

        # Semantic Router uses 2-stage classification internally
        # We can infer the method from timing (keyword is <1ms, embedding is ~10ms)
        classification_time_ms = int((time.time() - start_time) * 1000)
        classification_method = "keyword" if classification_time_ms < 5 else "embedding"

        # Confidence is high for deterministic routing (no LLM uncertainty)
        confidence = 0.95

        # Map route to complexity
        complexity_map = {
            "direct": "simple",
            "reasoning": "ambiguous",
            "specialized": "complex",
        }

        # Update state
        state["route"] = route
        state["classification_confidence"] = confidence
        state["classification_method"] = classification_method
        state["complexity"] = complexity_map.get(route, "simple")

        # Log classification step
        state["execution_log"].append({
            "stage": "classify",
            "method": classification_method,
            "route": route,
            "confidence": confidence,
            "time_ms": classification_time_ms,
        })

        return state

    def _route_decision(self, state: UnifiedAgentState) -> str:
        """
        Route decision function for conditional edges (T346)

        Returns: "direct" | "reasoning" | "specialized"
        """
        return state["route"]

    # ============================================================
    # Execution Paths (T347-T351)
    # ============================================================

    async def _direct_node(self, state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Direct path execution (T347, FR-131)

        Performance target: P95 < 1.5s (SC-047)
        """
        start_time = time.time()

        try:
            query = state["query"]
            history = state.get("conversation_history", [])

            # Build simple prompt with conversation history (last 5 messages)
            recent_history = history[-5:] if len(history) > 5 else history

            # Format conversation context
            context_str = ""
            if recent_history:
                context_str = "\n\n이전 대화:\n"
                for msg in recent_history:
                    role = "사용자" if msg.get("role") == "user" else "AI"
                    content = msg.get("content", "")
                    context_str += f"{role}: {content}\n"

            # Build prompt with clear instructions
            prompt = f"""당신은 한국어로 대화하는 친절한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요.
{context_str}

사용자: {query}

AI:"""

            # Call base LLM with standard parameters
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )

            state["final_response"] = response.strip()

            # Log execution
            execution_time_ms = int((time.time() - start_time) * 1000)
            state["execution_log"].append({
                "stage": "direct_execution",
                "status": "success",
                "time_ms": execution_time_ms,
            })

        except Exception as e:
            error_msg = f"Direct path execution failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            state["final_response"] = "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
            state["error"] = error_msg

            # Log failure
            execution_time_ms = int((time.time() - start_time) * 1000)
            state["execution_log"].append({
                "stage": "direct_execution",
                "status": "error",
                "error": error_msg,
                "time_ms": execution_time_ms,
            })

        return state

    async def _clarify_intent(self, query: str, history: List) -> Dict:
        """
        Intent clarification helper (T348, FR-132)

        Returns clarification dict with:
        - clarified_intent
        - missing_context
        - complexity
        - recommended_route
        - agent_type
        - refined_query
        """
        import json

        # Format conversation history
        history_str = ""
        if history:
            history_str = "\n대화 기록:\n"
            for msg in history[-3:]:  # Last 3 messages for context
                role = "사용자" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"

        # Build clarification prompt
        clarification_prompt = f"""사용자의 애매한 요청을 분석하여 진짜 의도를 파악하세요.
{history_str}

사용자 쿼리: "{query}"

다음 질문에 답하세요:
1. 사용자의 실제 의도는 무엇인가요?
2. 어떤 정보/맥락이 빠져있나요?
3. 이것은 단순한 질문인가요, 아니면 복잡한 작업인가요?
4. 복잡한 작업이라면 어떤 전문가(agent)가 필요한가요?

JSON 형식으로만 답변하세요:
{{
    "clarified_intent": "사용자가 실제로 원하는 것",
    "missing_context": ["빠진 정보1", "빠진 정보2"],
    "complexity": "simple" 또는 "complex",
    "recommended_route": "direct" 또는 "specialized",
    "agent_type": null 또는 "rag" 또는 "data_analysis" 또는 "document_writing" 등,
    "refined_query": "명확하게 다시 작성한 쿼리"
}}"""

        # Retry policy: max 3 attempts with exponential backoff
        max_retries = 3
        retry_delays = [0.1, 0.2, 0.4]  # seconds

        for attempt in range(max_retries):
            try:
                # Call LLM with retry logic
                response = await self.llm.generate(
                    prompt=clarification_prompt,
                    max_tokens=300,
                    temperature=0.3
                )

                # Parse JSON response
                response_clean = response.strip()
                # Extract JSON if wrapped in markdown code blocks
                if "```json" in response_clean:
                    response_clean = response_clean.split("```json")[1].split("```")[0].strip()
                elif "```" in response_clean:
                    response_clean = response_clean.split("```")[1].split("```")[0].strip()

                clarification = json.loads(response_clean)

                # Validate required fields
                required_fields = ["clarified_intent", "complexity", "recommended_route", "refined_query"]
                if all(field in clarification for field in required_fields):
                    # Ensure missing_context is a list
                    if "missing_context" not in clarification:
                        clarification["missing_context"] = []
                    if "agent_type" not in clarification:
                        clarification["agent_type"] = None

                    return clarification
                else:
                    print(f"[WARNING] Clarification missing required fields: {clarification}")
                    # Continue to retry

            except json.JSONDecodeError as e:
                print(f"[WARNING] Intent clarification JSON parse error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                # Continue to retry
            except Exception as e:
                print(f"[WARNING] Intent clarification LLM call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                # Continue to retry

            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                time.sleep(retry_delays[attempt])

        # All retries exhausted - fallback
        print(f"[ERROR] Intent clarification failed after {max_retries} attempts. Falling back to direct path.")
        return {
            "clarified_intent": query,
            "missing_context": ["사용자 의도를 명확히 파악할 수 없습니다"],
            "complexity": "simple",
            "recommended_route": "direct",
            "agent_type": None,
            "refined_query": query,
        }

    async def _reasoning_node(self, state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Reasoning path execution (T349, FR-132)

        Clarifies ambiguous intent then reroutes to direct or specialized.
        NOTE: Does NOT execute tools directly.
        """
        start_time = time.time()

        try:
            query = state["query"]
            history = state.get("conversation_history", [])

            # Call intent clarification
            clarification = await self._clarify_intent(query, history)

            # Update state with clarification results
            state["clarified_intent"] = clarification.get("clarified_intent", query)
            state["missing_context"] = clarification.get("missing_context", [])
            state["refined_query"] = clarification.get("refined_query", query)

            recommended_route = clarification.get("recommended_route", "direct")
            complexity = clarification.get("complexity", "simple")

            # Reroute based on clarification
            if complexity == "simple" or recommended_route == "direct":
                # Reroute to direct path
                state["rerouted_to"] = "direct"

                # If missing context identified, ask user for clarification
                if state["missing_context"]:
                    missing_items = ", ".join(state["missing_context"])
                    state["final_response"] = f"요청을 명확히 파악하지 못했습니다. 구체적으로 알려주세요: {missing_items}"
                else:
                    # Execute direct LLM call with refined query
                    refined_query = state["refined_query"]
                    recent_history = history[-5:] if len(history) > 5 else history

                    # Format conversation context
                    context_str = ""
                    if recent_history:
                        context_str = "\n\n이전 대화:\n"
                        for msg in recent_history:
                            role = "사용자" if msg.get("role") == "user" else "AI"
                            content = msg.get("content", "")
                            context_str += f"{role}: {content}\n"

                    prompt = f"""당신은 한국어로 대화하는 친절한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요.
{context_str}

사용자: {refined_query}

AI:"""

                    response = await self.llm.generate(
                        prompt=prompt,
                        max_tokens=1000,
                        temperature=0.7
                    )
                    state["final_response"] = response.strip()

            else:
                # Reroute to specialized path
                state["rerouted_to"] = "specialized"
                state["agent_type"] = clarification.get("agent_type")

                # Call multi-agent orchestrator
                refined_query = state["refined_query"]
                agent_type = state["agent_type"]

                try:
                    # Execute multi-agent system with forced agent type
                    result = await self.multi_agent.route_and_execute(
                        user_query=refined_query,
                        forced_agent=agent_type,
                        context={"conversation_history": history}
                    )

                    # Update state with agent results
                    state["final_response"] = result.get("response", "")
                    state["agent_sequence"] = result.get("agents_used", [])
                    state["agent_outputs"] = result.get("agent_outputs", {})
                    state["tools_used"] = result.get("tools_used", [])

                except Exception as agent_error:
                    print(f"[ERROR] Multi-agent execution failed: {str(agent_error)}")
                    # Fallback to direct path
                    state["final_response"] = "일반 모드로 처리합니다. " + str(agent_error)
                    state["error"] = f"Agent execution failed: {str(agent_error)}"

            # Log reasoning step
            reasoning_time_ms = int((time.time() - start_time) * 1000)
            state["execution_log"].append({
                "stage": "intent_clarification",
                "clarified_intent": state["clarified_intent"],
                "rerouted_to": state["rerouted_to"],
                "agent_type": state.get("agent_type"),
                "time_ms": reasoning_time_ms,
            })

        except Exception as e:
            error_msg = f"Reasoning path execution failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            state["final_response"] = "요청을 명확히 파악하지 못했습니다. 구체적으로 알려주세요: 무엇을 도와드릴까요?"
            state["error"] = error_msg
            state["rerouted_to"] = "direct"  # Fallback to direct

            # Log failure
            reasoning_time_ms = int((time.time() - start_time) * 1000)
            state["execution_log"].append({
                "stage": "intent_clarification",
                "status": "error",
                "error": error_msg,
                "time_ms": reasoning_time_ms,
            })

        return state

    async def _specialized_node(self, state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Specialized path execution (T350, FR-133)

        Invokes multi-agent orchestrator for complex tasks.
        Agents autonomously use tools via internal ReAct pattern.
        """
        start_time = time.time()

        try:
            query = state["query"]
            history = state.get("conversation_history", [])

            # Call multi-agent orchestrator
            result = await self.multi_agent.route_and_execute(
                user_query=query,
                context={"conversation_history": history}
            )

            # Combine agent outputs with attribution
            agent_outputs = result.get("agent_outputs", {})
            if agent_outputs:
                combined_response = ""
                for agent_name, output in agent_outputs.items():
                    combined_response += f"[{agent_name}]\n{output}\n\n"
                combined_response = combined_response.rstrip()
            else:
                combined_response = result.get("response", "")

            # Update state
            state["final_response"] = combined_response
            state["agent_sequence"] = result.get("agents_used", [])
            state["agent_outputs"] = agent_outputs
            state["tools_used"] = result.get("tools_used", [])

            # Determine workflow type from result
            workflow_type = result.get("workflow_type", "single")
            state["agent_outputs"]["workflow_type"] = workflow_type  # Store in state

            # Log execution
            specialized_time_ms = int((time.time() - start_time) * 1000)
            state["execution_log"].append({
                "stage": "specialized_execution",
                "workflow": workflow_type,
                "agents": state["agent_sequence"],
                "tools": state["tools_used"],
                "time_ms": specialized_time_ms,
            })

        except Exception as e:
            error_msg = f"Specialized path execution failed: {str(e)}"
            print(f"[ERROR] {error_msg}")

            # Fallback to direct path
            try:
                # Attempt direct LLM response as fallback
                recent_history = state.get("conversation_history", [])[-5:]
                context_str = ""
                if recent_history:
                    context_str = "\n\n이전 대화:\n"
                    for msg in recent_history:
                        role = "사용자" if msg.get("role") == "user" else "AI"
                        content = msg.get("content", "")
                        context_str += f"{role}: {content}\n"

                prompt = f"""당신은 한국어로 대화하는 친절한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요.
{context_str}

사용자: {state["query"]}

AI:"""

                fallback_response = await self.llm.generate(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.7
                )

                state["final_response"] = "일반 모드로 처리합니다.\n\n" + fallback_response.strip()

            except Exception as fallback_error:
                print(f"[ERROR] Fallback to direct path also failed: {str(fallback_error)}")
                state["final_response"] = "죄송합니다. 요청 처리 중 오류가 발생했습니다."

            state["error"] = error_msg

            # Log failure
            specialized_time_ms = int((time.time() - start_time) * 1000)
            state["execution_log"].append({
                "stage": "specialized_execution",
                "status": "error",
                "error": error_msg,
                "time_ms": specialized_time_ms,
            })

        return state

    async def _finalize_node(self, state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Finalize node (T351)

        Aggregates response, calculates metrics, logs execution.
        """
        # Validate final response exists
        if not state.get("final_response"):
            print("[WARNING] No final_response in state, setting fallback message")
            state["final_response"] = "죄송합니다. 응답을 생성할 수 없었습니다."

        # Calculate total processing time from execution log
        total_time_ms = 0
        for log_entry in state.get("execution_log", []):
            total_time_ms += log_entry.get("time_ms", 0)

        state["processing_time_ms"] = total_time_ms

        # Determine success status
        success = state.get("error") is None

        # Optional debug mode: append route emoji to response
        debug_mode = False  # Can be enabled via config
        if debug_mode:
            route_emojis = {
                RouteType.DIRECT: "⚡",
                RouteType.REASONING: "🤔",
                RouteType.SPECIALIZED: "👥",
            }
            emoji = route_emojis.get(state.get("route"), "")
            if emoji:
                state["final_response"] += f"\n\n{emoji}"

        # Append final log entry
        state["execution_log"].append({
            "stage": "finalize",
            "total_time_ms": total_time_ms,
            "route": state.get("route"),
            "success": success,
        })

        # Session 2025-11-10 clarification: Explicit memory cleanup (FR-129, FR-135)
        # 대용량 필드 명시적 삭제로 메모리 누수 방지
        # state 자체는 LangGraph가 invoke() 반환 후 Python GC가 자동 해제
        large_fields = ["retrieved_documents", "tool_results", "intermediate_steps", "conversation_history"]
        for field in large_fields:
            if field in state:
                del state[field]

        return state

    # ============================================================
    # Public API (T352)
    # ============================================================

    async def route_and_execute(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for unified orchestrator (T352)

        Args:
            query: User query string
            conversation_history: Recent messages for context
            user_id: User ID for logging

        Returns:
            {
                "response": str,
                "route_taken": str,
                "processing_time_ms": int,
                "execution_log": list,
            }
        """
        if not LANGGRAPH_AVAILABLE or not self.graph:
            raise RuntimeError("LangGraph not available. Cannot execute unified orchestrator.")

        # Initialize state
        initial_state: UnifiedAgentState = {
            "query": query,
            "conversation_history": conversation_history or [],
            "user_id": user_id,
            "route": RouteType.DIRECT,
            "complexity": "simple",
            "classification_confidence": 0.0,
            "classification_method": "keyword",
            "clarified_intent": None,
            "missing_context": [],
            "refined_query": None,
            "rerouted_to": None,
            "agent_type": None,
            "agent_sequence": [],
            "agent_outputs": {},
            "tools_used": [],
            "final_response": "",
            "processing_time_ms": 0,
            "execution_log": [],
            "error": None,
        }

        # Execute LangGraph workflow
        start_time = time.time()
        try:
            final_state = await self.graph.ainvoke(initial_state)
            final_state["processing_time_ms"] = int((time.time() - start_time) * 1000)

            return {
                "response": final_state["final_response"],
                "route_taken": final_state["route"],
                "processing_time_ms": final_state["processing_time_ms"],
                "execution_log": final_state["execution_log"],
                "error": final_state.get("error"),
            }
        except Exception as e:
            error_msg = f"Unified orchestrator execution failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {
                "response": "죄송합니다. 요청 처리 중 오류가 발생했습니다.",
                "route_taken": "error",
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "execution_log": [],
                "error": error_msg,
            }
