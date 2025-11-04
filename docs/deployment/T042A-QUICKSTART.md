# T042A Quick Start: Air-Gapped Deployment Validation

## 목적

Constitution Principle I (Air-Gapped First) 준수를 검증합니다.
시스템이 인터넷 연결 없이 완전히 독립적으로 작동하는지 확인합니다.

## 검증 항목

1. ✓ 모든 AI 모델 로컬 디스크에서 로드
2. ✓ ReAct 도구 데이터 파일 접근 가능
3. ✓ Multi-Agent 프롬프트 로드 성공
4. ✓ 모델 로딩 시간 <60초 (SC-020)
5. ✓ 기본 LLM 추론 작동
6. ✓ 네트워크 격리 상태 확인

## 전제 조건

### 1️⃣ 오프라인 의존성 번들 생성 (T008A)

**인터넷 연결이 가능한 환경에서** 먼저 실행:

```bash
# Bash 버전 (Linux)
bash scripts/bundle-offline-deps.sh

# PowerShell 버전 (Windows)
powershell -ExecutionPolicy Bypass -File scripts/bundle-offline-deps.ps1
```

이 스크립트는 다음을 다운로드합니다:
- Python 패키지 (requirements.txt)
- Qwen3-4B-Instruct GGUF 모델
- toxic-bert 모델
- sentence-transformers 모델

### 2️⃣ Python 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

주요 의존성:
- llama-cpp-python
- sentence-transformers
- transformers
- torch (CPU version)

## 실행 방법

### 1️⃣ 기본 검증 (네트워크 연결 상태)

```bash
# 저장소 루트에서
python3 scripts/validation/test_airgapped_deployment.py
```

### 2️⃣ 완전 폐쇄망 검증 (권장)

**실제 폐쇄망 환경 시뮬레이션**:

#### Linux:
```bash
# 네트워크 인터페이스 비활성화
sudo ifconfig eth0 down

# 또는 iptables로 차단
sudo iptables -A OUTPUT -j DROP

# 검증 실행
python3 scripts/validation/test_airgapped_deployment.py

# 네트워크 복구
sudo ifconfig eth0 up
# 또는
sudo iptables -F
```

#### Windows:
```powershell
# 네트워크 어댑터 비활성화
Disable-NetAdapter -Name "이더넷" -Confirm:$false

# 검증 실행
python3 scripts/validation/test_airgapped_deployment.py

# 네트워크 복구
Enable-NetAdapter -Name "이더넷"
```

### 3️⃣ 예상 실행 시간

- **모델 존재 확인**: 1-2초
- **모델 로딩 테스트**: 30-60초
- **기본 추론 테스트**: 5-10초
- **총 소요 시간**: 약 1-2분

## 출력 예시

```
============================================================
AIR-GAPPED DEPLOYMENT VALIDATION - T042A
============================================================

Constitution Principle I: Air-Gapped First
Validating system can operate without internet connectivity

🔍 [Models] Model Files Exist
   Verify all AI models are present in local filesystem
   ✅ PASS: Found 2 models: Qwen3-4B-Instruct (2441MB), Qwen2.5-1.5B-Instruct (Fallback) (1989MB) (0.01s)

🔍 [Models] Sentence Transformers Model
   Verify embedding model for tag matching and semantic search
   ✅ PASS: Model loaded (paraphrase-multilingual-MiniLM-L12-v2, dim=384) (2.34s)

🔍 [Models] Toxic-BERT Model
   Verify safety filter ML model (unitary/toxic-bert)
   ✅ PASS: Model loaded (unitary/toxic-bert) (1.89s)

🔍 [Data Files] ReAct Tool Data Files
   Verify Korean holidays and document templates exist
   ✅ PASS: Found 4 files (0.00s)

🔍 [Data Files] Multi-Agent Prompt Files
   Verify agent prompt templates load from backend/prompts/
   ✅ PASS: Found 5 agent prompts (0.00s)

🔍 [Performance] Model Loading Performance
   Verify Qwen3-4B loads within 60 seconds (SC-020)
   ✅ PASS: Loaded in 42.31s (SC-020: <60s) (42.31s)

🔍 [Functionality] Basic Inference Test
   Verify LLM can generate response to simple query
   ✅ PASS: Generated 23 tokens: '안녕하세요! 무엇을 도와드릴까요?' (8.45s)

🔍 [Network] Network Isolation Status
   Check if network connectivity is disabled
   ⚠️  WARNING: Network is ENABLED - For true air-gapped validation, disable network interface (1.02s)

============================================================
VALIDATION SUMMARY
============================================================
Total Checks: 8
✅ Passed: 7
❌ Failed: 0
⚠️  Errors: 0

⚠️  PARTIAL PASS - Network still enabled (for development)

📄 Report: docs/deployment/air-gapped-validation-report.md
```

## 결과 확인

### ✅ 성공 기준

- 모든 필수 검사 통과 (Models, Data Files, Performance, Functionality)
- Network 검사는 경고만 표시 (개발 환경에서는 정상)

### ❌ 실패 시 조치

#### 문제 1: "Model not found"

```bash
# 오프라인 번들 스크립트 실행 확인
ls -lh models/

# 모델 파일이 없으면 다시 다운로드
bash scripts/bundle-offline-deps.sh
```

#### 문제 2: "llama-cpp-python not installed"

```bash
cd backend
pip install llama-cpp-python
```

#### 문제 3: "sentence-transformers failed to load"

```bash
pip install sentence-transformers transformers torch
```

#### 문제 4: "Korean holidays not found"

```bash
# 파일 위치 확인
ls backend/data/korean_holidays.json

# 없으면 템플릿에서 복사
cp backend/data/korean_holidays.json.example backend/data/korean_holidays.json
```

#### 문제 5: "Templates not found"

```bash
# 디렉토리 확인
ls backend/templates/

# 템플릿 파일 생성 (공문서, 보고서, 안내문)
# 이미 T153에서 생성되었어야 함
```

#### 문제 6: "Agent prompts not found"

```bash
# 디렉토리 확인
ls backend/prompts/

# 프롬프트 파일 생성 (citizen_support, document_writing, etc.)
# 이미 T176에서 생성되었어야 함
```

## 완전 폐쇄망 배포 준비

### 1️⃣ 번들 생성 (인터넷 연결 환경)

```bash
# 1. 의존성 번들
bash scripts/bundle-offline-deps.sh

# 2. 결과 확인
ls offline_packages/
ls models/

# 3. 압축
tar -czf airgap-bundle.tar.gz offline_packages/ models/ backend/data/ backend/templates/ backend/prompts/
```

### 2️⃣ 폐쇄망 서버로 전송

```bash
# USB 드라이브 또는 물리 매체로 전송
# 예: /media/usb/airgap-bundle.tar.gz
```

### 3️⃣ 폐쇄망 서버에서 설치

```bash
# 1. 압축 해제
tar -xzf airgap-bundle.tar.gz

# 2. Python 패키지 설치
cd offline_packages
pip install --no-index --find-links=. -r ../backend/requirements.txt

# 3. 검증 실행
cd ..
python3 scripts/validation/test_airgapped_deployment.py

# 4. 네트워크 차단 후 재검증 (선택)
sudo ifconfig eth0 down
python3 scripts/validation/test_airgapped_deployment.py
sudo ifconfig eth0 up
```

## 다음 단계

1. ✅ T042A 통과 확인
2. ▶️ T237A: 한국어 품질 데이터셋 생성
3. ▶️ Phase 3: User Story 1 구현 시작

## 참고

- **Constitution Principle I**: Air-Gapped First (NON-NEGOTIABLE)
- **SC-020**: 모델 로딩 <60초
- **FR-081**: 모든 AI 모델 로컬 번들
- **FR-082**: CPU-only 실행 지원

## 문제 해결

### Q: "Network warning" 메시지가 나오는데 정상인가요?

A: 개발 환경에서는 정상입니다. 실제 폐쇄망 배포 시에는 물리적으로 네트워크를 차단해야 합니다.

### Q: 모든 검사가 통과했는데 다음 단계는?

A: T042A 완료! tasks.md에서 [X] 체크하고 Phase 3로 진행하세요.

### Q: 검사 실패 시 Phase 3로 진행해도 되나요?

A: **절대 안 됩니다.** Constitution Principle I은 NON-NEGOTIABLE입니다. 모든 검사가 통과해야 합니다.
