# T037A Quick Start: CPU Performance Validation

## 목적

CPU-only 환경에서 Qwen3-4B-Instruct 모델의 응답 성능이 SC-001 요구사항(P95 ≤12s)을 충족하는지 검증합니다.

## 전제 조건

1. **모델 설치 확인**
   ```bash
   ls -lh models/qwen3-4b-instruct-q4_k_m.gguf
   ```
   - 파일이 있어야 함 (~2.4GB)
   - 없으면 다운로드 필요

2. **Python 의존성 설치**
   ```bash
   cd backend
   pip install llama-cpp-python
   ```

## 실행 방법

### 1️⃣ 스크립트 실행

```bash
# 저장소 루트에서
python3 scripts/validation/test_cpu_performance.py
```

### 2️⃣ 예상 실행 시간

- **모델 로딩**: 30-60초
- **10개 쿼리 × 3회 반복**: 약 5-10분 (CPU 성능에 따라 다름)
- **총 소요 시간**: 약 6-11분

### 3️⃣ 실행 중 출력 예시

```
============================================================
CPU PERFORMANCE VALIDATION - T037A
============================================================

📊 System Information:
   CPU: 13th Gen Intel(R) Core(TM) i5-1340P
   Cores: 16
   RAM: 7.5GB
   OS: Linux 5.15.146.1-microsoft-standard-WSL2

🔄 Loading model: models/qwen3-4b-instruct-q4_k_m.gguf
   Context window: 2048
   Threads: auto
✅ Model loaded in 45.32s

🧪 Running 10 queries × 3 iterations = 30 total tests

[1/10] Q01 (민원_처리)
   Query: 주차 민원이 접수되었습니다. 어떻게 처리해야 하나요?...
      Iteration 1: 8.45s (234 tokens)
      Iteration 2: 8.12s (228 tokens)
      Iteration 3: 8.67s (241 tokens)
   ✓ Average: 8.41s

...

============================================================
📈 PERFORMANCE SUMMARY
============================================================
Total tests: 30
Mean:   9.23s
Median: 9.15s
StdDev: 1.12s
Min:    7.45s
Max:    11.89s
P95:    11.23s

============================================================
SC-001 VALIDATION: P95 ≤ 12s
============================================================
Result: 11.23s
Status: ✅ PASS
```

## 4️⃣ 결과 확인

스크립트 실행 완료 후 다음 파일들이 생성됩니다:

1. **`docs/validation/cpu-performance-validation.md`**
   - 상세한 검증 보고서 (마크다운)
   - SC-001 합격/불합격 판정
   - 시스템 정보, 통계, 권장사항

2. **`docs/validation/cpu-performance-validation.json`**
   - 원시 데이터 (JSON)
   - 추가 분석용

### ✅ PASS 기준

- **P95 응답시간 ≤ 12초**
- 30개 테스트 중 95번째 백분위수가 12초 이하

### ❌ FAIL 시 조치사항

보고서의 "Conclusion" 섹션 참조:
- CPU 성능 확인 (throttling, 주파수)
- 경량 모델로 변경 (Qwen2.5-1.5B)
- GPU 가속 고려 (Phase 13 vLLM)

## 문제 해결

### 오류: "llama-cpp-python not installed"

```bash
cd backend
pip install llama-cpp-python
```

### 오류: "Model not found"

```bash
# 모델 다운로드 (인터넷 연결 필요)
bash scripts/bundle-offline-deps.sh
```

### 성능이 너무 느림 (P95 > 20s)

1. CPU 코어 수 확인
   ```bash
   nproc  # 16+ 권장
   ```

2. 메모리 확인
   ```bash
   free -h  # 8GB+ 필요
   ```

3. CPU 사용률 모니터링
   ```bash
   top -H -p $(pgrep -f test_cpu_performance)
   ```

## 다음 단계

1. ✅ T037A 통과 확인
2. ▶️ T042A: 폐쇄망 배포 검증
3. ▶️ T237A: 한국어 품질 데이터셋 생성
4. ▶️ Phase 3: User Story 1 구현

## 참고

- **SC-001 요구사항**: spec.md 참조
- **Phase 2 완료 확인**: tasks.md Phase 2 모든 항목 [X]
- **Constitution Principle IV**: 단순성 우선 (CPU 기본, GPU 선택)
