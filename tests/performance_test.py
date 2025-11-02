# -*- coding: utf-8 -*-
"""
Performance Test Suite (T236)

Tests system performance with concurrent users per SC-002:
- Run with 10 concurrent users
- Verify <20% performance degradation
- Measure response times, throughput, error rates

Usage:
    python tests/performance_test.py

Requirements:
    - System must be running (docker-compose up)
    - pip install locust requests
"""

import time
import statistics
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

# Test configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
NUM_CONCURRENT_USERS = 10
TEST_DURATION_SECONDS = 60
WARMUP_REQUESTS = 5

# Performance thresholds (SC-002)
MAX_DEGRADATION_PERCENT = 20  # <20% degradation allowed


class PerformanceTest:
    """Performance test coordinator"""

    def __init__(self):
        self.results = {
            "baseline": {},
            "concurrent": {},
            "degradation": {}
        }

    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)

    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", json_data: dict = None) -> float:
        """
        Test single endpoint and return response time

        Returns:
            Response time in milliseconds
        """
        start_time = time.time()

        try:
            if method == "GET":
                async with session.get(f"{API_BASE_URL}{endpoint}") as response:
                    await response.text()
                    status = response.status
            elif method == "POST":
                async with session.post(f"{API_BASE_URL}{endpoint}", json=json_data) as response:
                    await response.text()
                    status = response.status

            elapsed_ms = (time.time() - start_time) * 1000

            if status >= 400:
                print(f"  �  {endpoint}: HTTP {status}")
                return -1

            return elapsed_ms

        except Exception as e:
            print(f"  L {endpoint}: {e}")
            return -1

    async def run_baseline_test(self):
        """Run baseline test (single user)"""
        self.print_header("Phase 1: Baseline Performance (Single User)")

        async with aiohttp.ClientSession() as session:
            # Warmup
            print("\nWarming up...")
            for _ in range(WARMUP_REQUESTS):
                await self.test_endpoint(session, "/health")

            # Test endpoints
            endpoints = [
                ("/health", "GET", None),
                ("/health/detailed", "GET", None),
                # Note: Protected endpoints require authentication
                # Add more endpoints as needed
            ]

            print("\nTesting endpoints...")
            for endpoint, method, data in endpoints:
                times = []

                for i in range(10):
                    elapsed = await self.test_endpoint(session, endpoint, method, data)
                    if elapsed > 0:
                        times.append(elapsed)

                if times:
                    avg_time = statistics.mean(times)
                    min_time = min(times)
                    max_time = max(times)
                    p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max_time

                    self.results["baseline"][endpoint] = {
                        "avg": avg_time,
                        "min": min_time,
                        "max": max_time,
                        "p95": p95_time
                    }

                    print(f"   {endpoint}")
                    print(f"     Avg: {avg_time:.2f}ms | Min: {min_time:.2f}ms | Max: {max_time:.2f}ms | P95: {p95_time:.2f}ms")

    async def run_concurrent_test(self):
        """Run concurrent test (multiple users)"""
        self.print_header(f"Phase 2: Concurrent Performance ({NUM_CONCURRENT_USERS} Users)")

        async def user_session(user_id: int):
            """Simulate single user session"""
            async with aiohttp.ClientSession() as session:
                times = []
                errors = 0

                for _ in range(10):
                    elapsed = await self.test_endpoint(session, "/health")
                    if elapsed > 0:
                        times.append(elapsed)
                    else:
                        errors += 1

                return times, errors

        print(f"\nRunning {NUM_CONCURRENT_USERS} concurrent users...")

        # Run concurrent users
        tasks = [user_session(i) for i in range(NUM_CONCURRENT_USERS)]
        results = await asyncio.gather(*tasks)

        # Aggregate results
        all_times = []
        total_errors = 0

        for times, errors in results:
            all_times.extend(times)
            total_errors += errors

        if all_times:
            avg_time = statistics.mean(all_times)
            min_time = min(all_times)
            max_time = max(all_times)
            p95_time = statistics.quantiles(all_times, n=20)[18] if len(all_times) >= 20 else max_time

            self.results["concurrent"]["/health"] = {
                "avg": avg_time,
                "min": min_time,
                "max": max_time,
                "p95": p95_time,
                "errors": total_errors,
                "total_requests": len(all_times) + total_errors
            }

            print(f"\n   Concurrent Test Results:")
            print(f"     Avg: {avg_time:.2f}ms | Min: {min_time:.2f}ms | Max: {max_time:.2f}ms | P95: {p95_time:.2f}ms")
            print(f"     Errors: {total_errors}/{len(all_times) + total_errors}")

    def calculate_degradation(self):
        """Calculate performance degradation"""
        self.print_header("Phase 3: Performance Degradation Analysis")

        baseline_avg = self.results["baseline"].get("/health", {}).get("avg", 0)
        concurrent_avg = self.results["concurrent"].get("/health", {}).get("avg", 0)

        if baseline_avg > 0 and concurrent_avg > 0:
            degradation_percent = ((concurrent_avg - baseline_avg) / baseline_avg) * 100

            self.results["degradation"] = {
                "baseline_avg_ms": baseline_avg,
                "concurrent_avg_ms": concurrent_avg,
                "degradation_percent": degradation_percent,
                "threshold_percent": MAX_DEGRADATION_PERCENT,
                "passed": degradation_percent < MAX_DEGRADATION_PERCENT
            }

            print(f"\nBaseline (1 user):     {baseline_avg:.2f}ms")
            print(f"Concurrent ({NUM_CONCURRENT_USERS} users): {concurrent_avg:.2f}ms")
            print(f"Degradation:           {degradation_percent:.2f}%")
            print(f"Threshold:             <{MAX_DEGRADATION_PERCENT}%")

            if degradation_percent < MAX_DEGRADATION_PERCENT:
                print(f"\n PASSED: Performance degradation within acceptable limits (SC-002)")
            else:
                print(f"\nL FAILED: Performance degradation exceeds {MAX_DEGRADATION_PERCENT}% threshold")

        else:
            print("L Unable to calculate degradation (missing baseline or concurrent data)")

    def print_summary(self):
        """Print test summary"""
        self.print_header("Performance Test Summary")

        print("\nTest Configuration:")
        print(f"  - API URL: {API_BASE_URL}")
        print(f"  - Concurrent Users: {NUM_CONCURRENT_USERS}")
        print(f"  - Test Duration: {TEST_DURATION_SECONDS}s")

        print("\nResults:")
        if self.results["degradation"].get("passed"):
            print("   Performance test PASSED")
            print(f"   Degradation: {self.results['degradation']['degradation_percent']:.2f}% (threshold: <{MAX_DEGRADATION_PERCENT}%)")
        else:
            print("  L Performance test FAILED")

        print("\nRecommendations:")
        if self.results["degradation"].get("degradation_percent", 0) > 10:
            print("  - Consider increasing CPU/memory resources")
            print("  - Review database query performance")
            print("  - Enable connection pooling")
            print("  - Consider using GPU for LLM inference")

    async def run_all_tests(self):
        """Run all performance tests"""
        print("=" * 60)
        print("PERFORMANCE TEST SUITE (T236)")
        print("Success Criterion SC-002: <20% degradation with 10 concurrent users")
        print("=" * 60)

        await self.run_baseline_test()
        await self.run_concurrent_test()
        self.calculate_degradation()
        self.print_summary()


def main():
    """Main entry point"""
    test = PerformanceTest()
    asyncio.run(test.run_all_tests())


if __name__ == "__main__":
    main()
