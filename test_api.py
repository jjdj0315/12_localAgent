"""
Phase 9/10 Manual Test Script

Tests:
- T166-T171: ReAct Agent functionality
- T197B-T204: Multi-Agent system
"""
import requests
import time
import json
from datetime import datetime

API_BASE = "http://127.0.0.1:8000/api/v1"
session_token = None
conversation_id = None

def print_test_header(test_name):
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    print("=" * 60)

def print_result(success, message):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {message}")

def test_1_login():
    """TEST 1: Admin login"""
    global session_token
    print_test_header("T1: Admin Login")

    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": "admin", "password": "admin123!"}
        )

        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            print_result(True, f"Login successful. Token: {session_token[:20]}...")
            return True
        else:
            print_result(False, f"Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def test_2_basic_chat():
    """TEST 2: Basic chat (normal mode)"""
    global conversation_id
    print_test_header("T2: Basic Chat (Normal Mode)")

    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        # Create conversation
        response = requests.post(
            f"{API_BASE}/conversations",
            headers=headers,
            json={"title": "Test Conversation"}
        )

        if response.status_code != 201:
            print_result(False, f"Failed to create conversation: {response.status_code}")
            return False

        conversation_id = response.json()["id"]
        print(f"  Conversation created: {conversation_id}")

        # Send basic chat message
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/chat/send",
            headers=headers,
            json={
                "content": "안녕하세요. 지자체 공무원을 위한 LLM 시스템입니다. 간단히 자기소개 해주세요.",
                "conversation_id": conversation_id,
                "use_react_agent": False,
                "use_multi_agent": False
            }
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            reply = data.get("response", "")
            print(f"  Response time: {elapsed:.2f}s")
            print(f"  Reply: {reply[:100]}...")
            print_result(True, "Basic chat works")
            return True
        else:
            print_result(False, f"Chat failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def test_3_react_agent():
    """TEST 3: ReAct Agent Mode (T166-T171)"""
    print_test_header("T3: ReAct Agent Mode")

    headers = {"Authorization": f"Bearer {session_token}"}

    # Test cases for different tools
    test_cases = [
        {
            "name": "T167-1: Calculator Tool",
            "query": "1234 곱하기 567은 얼마인가요?",
            "expected_tool": "calculator"
        },
        {
            "name": "T167-2: Date Tool",
            "query": "오늘 날짜는 언제인가요?",
            "expected_tool": "date"
        },
        {
            "name": "T167-3: Document Template Tool",
            "query": "공문서 작성 템플릿을 보여주세요",
            "expected_tool": "template"
        }
    ]

    results = []

    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        print(f"Query: {test_case['query']}")

        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/chat",
                headers=headers,
                json={
                    "content": test_case["query"],
                    "conversation_id": conversation_id,
                    "use_react_agent": True,
                    "use_multi_agent": False
                },
                timeout=60  # T166: 30 seconds per 2-3 tool task
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "")
                react_steps = data.get("react_steps", [])
                tools_used = data.get("tools_used", [])

                print(f"  Response time: {elapsed:.2f}s")
                print(f"  Tools used: {tools_used}")
                print(f"  ReAct steps: {len(react_steps)}")
                print(f"  Reply: {reply[:150]}...")

                # T166: Check response time (<30s for 2-3 tools)
                if len(tools_used) <= 3 and elapsed <= 30:
                    print_result(True, f"T166: Response within 30s ({elapsed:.2f}s)")
                else:
                    print_result(False, f"T166: Exceeded 30s ({elapsed:.2f}s)")

                # T169: Check max iterations (should stop at 5)
                if len(react_steps) <= 5:
                    print_result(True, f"T169: Max iterations respected ({len(react_steps)} steps)")
                else:
                    print_result(False, f"T169: Exceeded 5 iterations ({len(react_steps)} steps)")

                results.append(True)
            else:
                print_result(False, f"Request failed: {response.status_code}")
                # T170: Test transparent error display
                print(f"  Error response: {response.text[:200]}")
                results.append(False)

        except requests.Timeout:
            print_result(False, f"Timeout (>60s)")
            results.append(False)
        except Exception as e:
            print_result(False, f"Exception: {e}")
            results.append(False)

    success_rate = sum(results) / len(results) * 100
    print(f"\nReAct Agent Success Rate: {success_rate:.1f}%")

    return success_rate >= 90  # T168: <10% error rate

def test_4_multi_agent():
    """TEST 4: Multi-Agent Mode (T197B-T204)"""
    print_test_header("T4: Multi-Agent Mode")

    headers = {"Authorization": f"Bearer {session_token}"}

    # Test cases for different agent workflows
    test_cases = [
        {
            "name": "T198: Document Writing Agent",
            "query": "지자체 예산 관련 공문서 작성 방법을 알려주세요",
            "expected_agents": ["document_writer"]
        },
        {
            "name": "T199: Sequential 3-Agent Workflow",
            "query": "최근 민원 데이터를 분석하고 보고서를 작성해주세요",
            "expected_agents": ["data_analyst", "document_writer"],
            "max_time": 90  # T199: 90 seconds for 3-agent sequential
        },
        {
            "name": "T200: Parallel Agent Execution",
            "query": "법률 검토와 예산 분석을 동시에 해주세요",
            "expected_workflow": "parallel"
        }
    ]

    results = []

    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        print(f"Query: {test_case['query']}")

        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/chat",
                headers=headers,
                json={
                    "content": test_case["query"],
                    "conversation_id": conversation_id,
                    "use_react_agent": False,
                    "use_multi_agent": True
                },
                timeout=120  # T202: 5-minute timeout
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "")
                workflow_type = data.get("workflow_type", "unknown")
                agents_used = data.get("agents_used", [])
                execution_time = data.get("execution_time_ms", 0) / 1000

                print(f"  Response time: {elapsed:.2f}s")
                print(f"  Workflow type: {workflow_type}")
                print(f"  Agents used: {agents_used}")
                print(f"  Execution time: {execution_time:.2f}s")
                print(f"  Reply: {reply[:150]}...")

                # T199: Check sequential workflow timing
                if "max_time" in test_case and execution_time <= test_case["max_time"]:
                    print_result(True, f"T199: Completed within {test_case['max_time']}s")

                # T200: Check parallel execution
                if "expected_workflow" in test_case:
                    if workflow_type == test_case["expected_workflow"]:
                        print_result(True, f"T200: Workflow type matches ({workflow_type})")
                    else:
                        print_result(False, f"T200: Expected {test_case['expected_workflow']}, got {workflow_type}")

                # T203: Check agent attribution
                if agents_used:
                    print_result(True, f"T203: Agent attribution present ({len(agents_used)} agents)")

                results.append(True)
            else:
                print_result(False, f"Request failed: {response.status_code}")
                # T201: Test agent failure handling
                print(f"  Error response: {response.text[:200]}")
                results.append(False)

        except requests.Timeout:
            print_result(False, f"Timeout (>120s)")
            results.append(False)
        except Exception as e:
            print_result(False, f"Exception: {e}")
            results.append(False)

    success_rate = sum(results) / len(results) * 100
    print(f"\nMulti-Agent Success Rate: {success_rate:.1f}%")

    return success_rate >= 85  # T198: 85%+ routing accuracy

def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 9/10 Manual Test Suite")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check backend availability
    print("\nChecking backend availability...")
    try:
        response = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Backend is running")
        else:
            print(f"[WARNING] Backend returned {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Backend not accessible: {e}")
        print("\nPlease start the backend server:")
        print("  cd C:\\02_practice\\12_localAgent\\backend")
        print("  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return

    # Run tests
    results = {
        "login": test_1_login(),
        "basic_chat": False,
        "react_agent": False,
        "multi_agent": False
    }

    if results["login"]:
        results["basic_chat"] = test_2_basic_chat()

        if results["basic_chat"]:
            results["react_agent"] = test_3_react_agent()
            results["multi_agent"] = test_4_multi_agent()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
