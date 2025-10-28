#!/usr/bin/env python3
"""Test LLM functionality"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Login
login_data = {"username": "admin", "password": "admin123!"}
session = requests.Session()
response = session.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Login: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# Send chat message
conversation_id = "5ec16361-4b62-429f-a6fe-383a3bec0ea9"
chat_data = {
    "conversation_id": conversation_id,
    "content": "안녕하세요! 간단한 자기소개 해주세요."
}

print("\n\nSending message...")
response = session.post(f"{BASE_URL}/chat/send", json=chat_data)
print(f"Chat: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print(f"Error: {response.text}")
