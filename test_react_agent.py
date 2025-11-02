# -*- coding: utf-8 -*-
"""
ReAct Agent 테스트 스크립트
"""
import requests

API_BASE = "http://localhost:8000/api/v1"

# 로그인
login_response = requests.post(
    f"{API_BASE}/auth/login",
    json={"username": "admin", "password": "admin123!"}
)
token = login_response.json()["session_token"]
headers = {"Authorization": f"Bearer {token}"}

# ReAct Agent 테스트
print("=== ReAct Agent 테스트 ===")
response = requests.post(
    f"{API_BASE}/chat/send",
    headers=headers,
    json={
        "content": "오늘 날짜는 무엇인가요?",  # 날짜 도구를 사용할 쿼리
        "use_react_agent": True  # ReAct 에이전트 활성화
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
