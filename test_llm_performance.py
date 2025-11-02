# -*- coding: utf-8 -*-
"""
Simple LLM Performance Test for T204A
Tests actual chat response time with 10 concurrent users
"""

import requests
import time
import asyncio
import aiohttp
from statistics import mean

API_BASE = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123!"
NUM_USERS = 10

async def test_single_user():
    """Test single user LLM response time"""
    print("\n=== Testing Single User ===")

    # Login
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/auth/login",
                               json={"username": USERNAME, "password": PASSWORD}) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status}")
                return None
            data = await resp.json()
            token = data.get("session_token") or data.get("access_token")
            if not token:
                print(f"No token in response: {data}")
                return None

        headers = {"Authorization": f"Bearer {token}"}

        # Send chat message and measure time
        start = time.time()
        async with session.post(f"{API_BASE}/chat/send",
                               json={"content": "안녕하세요, 간단한 테스트입니다"},
                               headers=headers,
                               timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status not in (200, 201):
                resp_text = await resp.text()
                print(f"Chat failed: {resp.status} - {resp_text}")
                return None
            await resp.json()

        elapsed = time.time() - start
        print(f"Response time: {elapsed:.2f}s")
        return elapsed

async def test_concurrent_users():
    """Test 10 concurrent users"""
    print(f"\n=== Testing {NUM_USERS} Concurrent Users ===")

    async def user_session(user_id):
        try:
            # Login
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_BASE}/auth/login",
                                       json={"username": USERNAME, "password": PASSWORD}) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    token = data.get("session_token") or data.get("access_token")

                headers = {"Authorization": f"Bearer {token}"}

                # Send chat message
                start = time.time()
                async with session.post(f"{API_BASE}/chat/send",
                                       json={"content": f"사용자 {user_id} 테스트"},
                                       headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status not in (200, 201):
                        return None
                    await resp.json()

                elapsed = time.time() - start
                print(f"  User {user_id}: {elapsed:.2f}s")
                return elapsed
        except Exception as e:
            print(f"  User {user_id} error: {e}")
            return None

    # Run all users concurrently
    tasks = [user_session(i) for i in range(NUM_USERS)]
    results = await asyncio.gather(*tasks)

    # Filter out failures
    successful = [r for r in results if r is not None]

    if successful:
        avg_time = mean(successful)
        print(f"\nConcurrent Results:")
        print(f"  Successful: {len(successful)}/{NUM_USERS}")
        print(f"  Average time: {avg_time:.2f}s")
        print(f"  Min: {min(successful):.2f}s")
        print(f"  Max: {max(successful):.2f}s")
        return avg_time
    else:
        print("All concurrent requests failed")
        return None

async def main():
    print("=" * 60)
    print("T204A: CPU Performance Validation")
    print("Target: 8-12s response time with 10 concurrent users")
    print("=" * 60)

    # Test single user
    single_time = await test_single_user()

    if single_time is None:
        print("\nSingle user test failed - cannot proceed")
        return

    # Test concurrent users
    concurrent_time = await test_concurrent_users()

    if concurrent_time is None:
        print("\nConcurrent test failed")
        return

    # Decision
    print("\n" + "=" * 60)
    print("T204A Decision Gate Analysis")
    print("=" * 60)
    print(f"Single user time: {single_time:.2f}s")
    print(f"Concurrent (10 users) avg time: {concurrent_time:.2f}s")

    if concurrent_time <= 12:
        print("\n✓ PASS: CPU performance acceptable (≤12s)")
        print("  Decision: Stay with llama.cpp (Phase 10)")
        print("  Rationale: Meets performance requirements without GPU")
    else:
        print("\n✗ FAIL: CPU performance exceeds 12s threshold")
        print("  Decision: Migrate to vLLM (Phase 13)")
        print("  Rationale: GPU acceleration needed for acceptable latency")

if __name__ == "__main__":
    asyncio.run(main())
