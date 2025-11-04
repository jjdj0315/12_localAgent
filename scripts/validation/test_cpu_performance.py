#!/usr/bin/env python3
"""
CPU Performance Validation Script for T037A

Tests CPU-only baseline performance against SC-001 requirements:
- Target: P95 response time ≤12 seconds
- Model: Qwen3-4B-Instruct GGUF Q4_K_M
- Test set: 10 standard Korean queries, 3 iterations each

Usage:
    python3 scripts/validation/test_cpu_performance.py

Output:
    - Console: Real-time progress and summary
    - docs/validation/cpu-performance-validation.md: Detailed report
"""

import time
import json
import statistics
import sys
import os
from pathlib import Path
from datetime import datetime
import platform

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

try:
    from llama_cpp import Llama
except ImportError:
    print("❌ llama-cpp-python not installed")
    print("   Install: pip install llama-cpp-python")
    sys.exit(1)


# Standard test queries (10 diverse government work scenarios)
TEST_QUERIES = [
    {
        "id": "Q01",
        "category": "민원_처리",
        "query": "주차 민원이 접수되었습니다. 어떻게 처리해야 하나요?"
    },
    {
        "id": "Q02",
        "category": "문서_작성",
        "query": "주민 대상 안내문을 작성해주세요. 재활용 분리수거 방법에 대한 내용입니다."
    },
    {
        "id": "Q03",
        "category": "정책_질문",
        "query": "지방재정법에 따른 예산 편성 절차를 설명해주세요."
    },
    {
        "id": "Q04",
        "category": "일정_계산",
        "query": "2024년 회계연도는 언제부터 언제까지인가요?"
    },
    {
        "id": "Q05",
        "category": "일반_업무",
        "query": "회의록 작성 시 주의사항을 알려주세요."
    },
    {
        "id": "Q06",
        "category": "민원_처리",
        "query": "건축 허가 신청서류에는 무엇이 필요한가요?"
    },
    {
        "id": "Q07",
        "category": "문서_작성",
        "query": "공문서 작성 시 기안 형식을 알려주세요."
    },
    {
        "id": "Q08",
        "category": "정책_질문",
        "query": "지역축제 개최를 위한 행정절차는 무엇인가요?"
    },
    {
        "id": "Q09",
        "category": "일정_계산",
        "query": "오늘부터 30일 후의 영업일은 며칠인가요? (공휴일 제외)"
    },
    {
        "id": "Q10",
        "category": "일반_업무",
        "query": "민원인 응대 시 유의사항을 요약해주세요."
    }
]


def get_system_info():
    """Collect system information for documentation"""
    info = {
        "timestamp": datetime.now().isoformat(),
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu_model": "Unknown",
        "cpu_cores": os.cpu_count(),
        "ram_gb": "Unknown"
    }

    # Try to get CPU model (Linux)
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line:
                    info["cpu_model"] = line.split(':')[1].strip()
                    break
    except:
        pass

    # Try to get RAM (Linux)
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    kb = int(line.split()[1])
                    info["ram_gb"] = f"{kb / 1024 / 1024:.1f}GB"
                    break
    except:
        pass

    return info


def load_model(model_path, n_ctx=2048, n_threads=None):
    """Load GGUF model with llama.cpp"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    print(f"🔄 Loading model: {model_path}")
    print(f"   Context window: {n_ctx}")
    print(f"   Threads: {n_threads or 'auto'}")

    start = time.time()
    llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=False
    )
    load_time = time.time() - start

    print(f"✅ Model loaded in {load_time:.2f}s")
    return llm, load_time


def run_inference(llm, query, max_tokens=500):
    """Run single inference and measure time"""
    prompt = f"사용자: {query}\n\n답변:"

    start = time.time()
    response = llm(
        prompt,
        max_tokens=max_tokens,
        stop=["사용자:", "\n\n\n"],
        echo=False
    )
    elapsed = time.time() - start

    text = response['choices'][0]['text'].strip()
    tokens = response['usage']['completion_tokens']

    return {
        "text": text,
        "tokens": tokens,
        "time_seconds": elapsed
    }


def run_performance_test(model_path, iterations=3):
    """Run full performance test"""
    print("\n" + "="*60)
    print("CPU PERFORMANCE VALIDATION - T037A")
    print("="*60)

    # Get system info
    sys_info = get_system_info()
    print(f"\n📊 System Information:")
    print(f"   CPU: {sys_info['cpu_model']}")
    print(f"   Cores: {sys_info['cpu_cores']}")
    print(f"   RAM: {sys_info['ram_gb']}")
    print(f"   OS: {sys_info['os']} {sys_info['os_version']}")

    # Load model
    llm, load_time = load_model(model_path)

    # Run tests
    print(f"\n🧪 Running {len(TEST_QUERIES)} queries × {iterations} iterations = {len(TEST_QUERIES) * iterations} total tests\n")

    results = []
    all_times = []

    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] {test['id']} ({test['category']})")
        print(f"   Query: {test['query'][:60]}...")

        test_times = []

        for iteration in range(1, iterations + 1):
            result = run_inference(llm, test['query'])
            test_times.append(result['time_seconds'])
            all_times.append(result['time_seconds'])

            print(f"      Iteration {iteration}: {result['time_seconds']:.2f}s ({result['tokens']} tokens)")

        avg_time = statistics.mean(test_times)
        print(f"   ✓ Average: {avg_time:.2f}s\n")

        results.append({
            "id": test['id'],
            "category": test['category'],
            "query": test['query'],
            "times": test_times,
            "avg_time": avg_time,
            "min_time": min(test_times),
            "max_time": max(test_times)
        })

    # Calculate statistics
    stats = {
        "mean": statistics.mean(all_times),
        "median": statistics.median(all_times),
        "stdev": statistics.stdev(all_times) if len(all_times) > 1 else 0,
        "min": min(all_times),
        "max": max(all_times),
        "p95": statistics.quantiles(all_times, n=20)[18] if len(all_times) >= 2 else all_times[0]  # 95th percentile
    }

    # Print summary
    print("="*60)
    print("📈 PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Total tests: {len(all_times)}")
    print(f"Mean:   {stats['mean']:.2f}s")
    print(f"Median: {stats['median']:.2f}s")
    print(f"StdDev: {stats['stdev']:.2f}s")
    print(f"Min:    {stats['min']:.2f}s")
    print(f"Max:    {stats['max']:.2f}s")
    print(f"P95:    {stats['p95']:.2f}s")

    # SC-001 validation
    sc001_pass = stats['p95'] <= 12.0
    print(f"\n{'='*60}")
    print(f"SC-001 VALIDATION: P95 ≤ 12s")
    print(f"{'='*60}")
    print(f"Result: {stats['p95']:.2f}s")
    print(f"Status: {'✅ PASS' if sc001_pass else '❌ FAIL'}")

    return {
        "system_info": sys_info,
        "model_path": model_path,
        "model_load_time": load_time,
        "test_queries": len(TEST_QUERIES),
        "iterations": iterations,
        "results": results,
        "statistics": stats,
        "sc001_pass": sc001_pass
    }


def save_report(data, output_path):
    """Save validation report in markdown format"""
    report = f"""# CPU Performance Validation Report - T037A

**Status**: {'✅ PASS' if data['sc001_pass'] else '❌ FAIL'}
**Date**: {data['system_info']['timestamp']}
**Model**: {Path(data['model_path']).name}

## SC-001 Requirement

**Requirement**: System responds to single-user queries with P95 latency ≤12 seconds on CPU-only deployment

**Result**: P95 = {data['statistics']['p95']:.2f}s
**Status**: {'✅ PASS - Meets SC-001' if data['sc001_pass'] else '❌ FAIL - Exceeds SC-001 threshold'}

## Test Environment

| Component | Specification |
|-----------|---------------|
| CPU Model | {data['system_info']['cpu_model']} |
| CPU Cores | {data['system_info']['cpu_cores']} |
| RAM | {data['system_info']['ram_gb']} |
| OS | {data['system_info']['os']} {data['system_info']['os_version']} |
| Python | {data['system_info']['python_version']} |
| Model | {Path(data['model_path']).name} |
| Model Load Time | {data['model_load_time']:.2f}s |
| Context Window | 2048 tokens |

## Test Methodology

- **Test Queries**: {data['test_queries']} diverse government work scenarios
- **Iterations**: {data['iterations']} per query
- **Total Tests**: {data['test_queries'] * data['iterations']}
- **Categories**: 민원_처리, 문서_작성, 정책_질문, 일정_계산, 일반_업무
- **Max Tokens**: 500 per response

## Performance Statistics

| Metric | Value |
|--------|-------|
| Mean | {data['statistics']['mean']:.2f}s |
| Median | {data['statistics']['median']:.2f}s |
| Std Dev | {data['statistics']['stdev']:.2f}s |
| Min | {data['statistics']['min']:.2f}s |
| Max | {data['statistics']['max']:.2f}s |
| **P95** | **{data['statistics']['p95']:.2f}s** |

## Detailed Results

"""

    # Add individual test results
    for result in data['results']:
        report += f"### {result['id']} - {result['category']}\n\n"
        report += f"**Query**: {result['query']}\n\n"
        report += f"| Iteration | Time (s) |\n"
        report += f"|-----------|----------|\n"
        for i, t in enumerate(result['times'], 1):
            report += f"| {i} | {t:.2f} |\n"
        report += f"| **Average** | **{result['avg_time']:.2f}** |\n\n"

    # Conclusion
    report += f"""## Conclusion

"""

    if data['sc001_pass']:
        report += f"""✅ **VALIDATION PASSED**

The CPU-only baseline performance meets SC-001 requirements with P95 latency of {data['statistics']['p95']:.2f}s (≤12s threshold).

**Recommendations**:
- ✅ Proceed to Phase 3 (User Story 1 implementation)
- ✅ CPU-only deployment is viable for production
- Consider Phase 13 (vLLM GPU) if concurrent user count exceeds 5 users

**Next Steps**:
1. Complete T042A (air-gapped deployment validation)
2. Proceed with Phase 3 user story implementation
"""
    else:
        report += f"""❌ **VALIDATION FAILED**

The CPU-only baseline performance does NOT meet SC-001 requirements. P95 latency is {data['statistics']['p95']:.2f}s (exceeds 12s threshold).

**Required Actions**:
1. ⚠️ BLOCK Phase 3 until resolved
2. Investigate performance bottlenecks:
   - Check CPU frequency/throttling
   - Verify thread count optimization
   - Test with different quantization (Q5_K_M, Q8_0)
3. Consider hardware upgrade or Phase 13 (GPU acceleration)

**Options**:
- Option A: Upgrade CPU (16+ cores recommended)
- Option B: Reduce model size (try Qwen2.5-1.5B-Instruct)
- Option C: Implement Phase 13 vLLM with GPU acceleration
"""

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding='utf-8')
    print(f"\n📄 Report saved: {output_path}")


def main():
    """Main execution"""
    # Find model
    model_path = Path("models/qwen3-4b-instruct-q4_k_m.gguf")

    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("\nPlease ensure Qwen3-4B-Instruct GGUF model is in models/ directory")
        return 1

    try:
        # Run performance test
        results = run_performance_test(str(model_path), iterations=3)

        # Save report
        output_path = Path("docs/validation/cpu-performance-validation.md")
        save_report(results, output_path)

        # Save raw JSON for analysis
        json_path = Path("docs/validation/cpu-performance-validation.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"📄 Raw data saved: {json_path}")

        # Return exit code
        return 0 if results['sc001_pass'] else 1

    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
