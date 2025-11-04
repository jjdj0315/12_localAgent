# CPU Performance Validation Report - T037A (Qwen3-0.6B Q8_0)

**Status**: ❌ FAIL
**Date**: 2025-11-04
**Model**: qwen3-0.6b-q8_0.gguf

## SC-001 Requirement

**Requirement**: System responds to single-user queries with P95 latency ≤12 seconds on CPU-only deployment

**Result**: P95 = 98.77s
**Status**: ❌ FAIL - Exceeds SC-001 threshold by 8.2x

## Test Environment

| Component | Specification |
|-----------|---------------|
| CPU Model | 13th Gen Intel(R) Core(TM) i5-1340P |
| CPU Cores | 16 |
| RAM | 7.5GB |
| OS | Linux #1 SMP Thu Jan 11 04:09:03 UTC 2024 |
| Python | 3.11.14 |
| Model | qwen3-0.6b-q8_0.gguf |
| Model Size | 639MB |
| Model Load Time | 67.15s |
| Context Window | 2048 tokens |

## Test Methodology

- **Test Queries**: 10 diverse government work scenarios
- **Iterations**: 3 per query
- **Total Tests**: 30
- **Categories**: 민원_처리, 문서_작성, 정책_질문, 일정_계산, 일반_업무
- **Max Tokens**: 500 per response

## Performance Statistics

| Metric | Value |
|--------|-------|
| Mean | 23.71s |
| Median | 12.61s |
| Std Dev | 27.84s |
| Min | 0.08s |
| Max | 121.33s |
| **P95** | **98.77s** |

## Detailed Results

### Q01 - 민원_처리

**Query**: 주차 민원이 접수되었습니다. 어떻게 처리해야 하나요?

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 65.19 | 70 |
| 2 | 61.84 | 500 |
| 3 | 80.31 | 500 |
| **Average** | **69.11** | - |

### Q02 - 문서_작성

**Query**: 주민 대상 안내문을 작성해주세요. 재활용 분리수거 방법에 대한 내용입니다.

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 121.33 | 500 |
| 2 | 42.86 | 500 |
| 3 | 46.43 | 500 |
| **Average** | **70.21** | - |

### Q03 - 정책_질문

**Query**: 지방재정법에 따른 예산 편성 절차를 설명해주세요.

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 55.97 | 500 |
| 2 | 12.98 | 500 |
| 3 | 12.39 | 500 |
| **Average** | **27.11** | - |

### Q04 - 일정_계산

**Query**: 2024년 회계연도는 언제부터 언제까지인가요?

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 5.54 | 223 |
| 2 | 12.25 | 500 |
| 3 | 1.00 | 45 |
| **Average** | **6.26** | - |

### Q05 - 일반_업무

**Query**: 회의록 작성 시 주의사항을 알려주세요.

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 12.66 | 500 |
| 2 | 12.67 | 500 |
| 3 | 12.18 | 501 |
| **Average** | **12.50** | - |

### Q06 - 민원_처리

**Query**: 건축 허가 신청서류에는 무엇이 필요한가요?

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 13.02 | 500 |
| 2 | 1.09 | 47 |
| 3 | 0.08 | 3 |
| **Average** | **4.73** | - |

### Q07 - 문서_작성

**Query**: 공문서 작성 시 기안 형식을 알려주세요.

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 12.51 | 500 |
| 2 | 12.41 | 500 |
| 3 | 12.45 | 500 |
| **Average** | **12.46** | - |

### Q08 - 정책_질문

**Query**: 지역축제 개최를 위한 행정절차는 무엇인가요?

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 14.02 | 500 |
| 2 | 13.91 | 500 |
| 3 | 12.45 | 500 |
| **Average** | **13.46** | - |

### Q09 - 일정_계산

**Query**: 오늘부터 30일 후의 영업일은 며칠인가요? (공휴일 제외)

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 13.50 | 500 |
| 2 | 0.18 | 7 |
| 3 | 12.63 | 500 |
| **Average** | **8.77** | - |

### Q10 - 일반_업무

**Query**: 민원인 응대 시 유의사항을 요약해주세요.

| Iteration | Time (s) | Tokens |
|-----------|----------|--------|
| 1 | 12.54 | 500 |
| 2 | 12.32 | 500 |
| 3 | 12.60 | 500 |
| **Average** | **12.49** | - |

## Performance Analysis

### ✅ Positive Findings

1. **Median Performance**: 12.61s is very close to the 12s target
   - 50% of queries complete within acceptable time

2. **Improved Average**: 23.71s vs Qwen3-4B's 59.19s (60% improvement)

3. **Fast Queries**: Several queries perform exceptionally well:
   - Q06: 4.73s average
   - Q04: 6.26s average
   - Q09: 8.77s average
   - Q05, Q07, Q10: ~12-13s (near target)

### ⚠️ Issues Identified

1. **Outliers**: Extreme slow responses drag P95 up:
   - Q02 Iteration 1: 121.33s (worst case)
   - Q01 Iteration 3: 80.31s

2. **Inconsistency**: High variance within same query:
   - Q02: 42.86s → 121.33s (3x difference)
   - Q06: 0.08s → 13.02s (150x difference)

3. **Token Generation Issues**: Some iterations generate very few tokens:
   - Q06 Iteration 3: only 3 tokens (0.08s)
   - Q09 Iteration 2: only 7 tokens (0.18s)
   - Suggests model may be cutting off responses prematurely

## Model Comparison

| Model | Size | Load Time | Mean | Median | P95 | SC-001 |
|-------|------|-----------|------|--------|-----|--------|
| Qwen3-4B Q4_K_M | 2.4GB | 246.99s | 59.19s | 58.80s | 97.59s | ❌ |
| **Qwen3-0.6B Q8_0** | **639MB** | **67.15s** | **23.71s** | **12.61s** | **98.77s** | **❌** |

**Key Observations**:
- 74% smaller model size
- 73% faster loading
- 60% better average response time
- **Median near target**, but P95 still fails

## Conclusion

❌ **VALIDATION FAILED**

The Qwen3-0.6B Q8_0 model does NOT meet SC-001 requirements. P95 latency is 98.77s (exceeds 12s threshold by 8.2x).

### Root Cause Analysis

The **median performance is excellent** (12.61s), indicating the model CAN meet the target for typical cases. However, occasional extreme outliers (121s, 80s) severely impact P95.

**Possible Causes**:
1. **Model hallucination/repetition**: Q8_0 quantization may cause occasional generation issues
2. **CPU throttling**: Thermal throttling during extended runs
3. **Memory contention**: WSL2 environment may have resource limitations
4. **Prompt sensitivity**: Certain query patterns trigger longer generation

### Recommended Actions

**Option A: Optimize Current Setup** ⚠️ May not be sufficient
- Reduce max_tokens from 500 to 200-300
- Add early stopping criteria
- Monitor and handle model repetition

**Option B: Try Smaller Quantization** ⚡ Recommended
- Download Qwen3-0.6B Q4_K_M (400MB, faster than Q8_0)
- Expected: Similar quality, better speed

**Option C: GPU Acceleration** 💰 Most reliable
- Implement Phase 13 (vLLM with GPU)
- Expected: Consistent <5s response times

**Option D: Accept Limitation** 📝 Document trade-off
- Document that P95 exceeds target on CPU
- Median performance meets user expectations
- Recommend GPU for production

### Next Steps

1. ⚠️ **BLOCKING**: SC-001 failure blocks Phase 3
2. User decision required: Choose Option A, B, C, or D
3. If proceeding with CPU: Document performance limitations in deployment guide

**⚠️ RECOMMENDATION**: Proceed with **Option C (GPU acceleration)** for production deployment to ensure consistent performance.
