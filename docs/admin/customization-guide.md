# 커스터마이징 가이드

**대상**: 시스템 관리자  
**마지막 업데이트**: 2025-10-31  
**버전**: 1.0

## 개요

이 문서는 Local LLM 웹 애플리케이션의 커스터마이징 방법과 각 설정 변경의 적용 시점을 설명합니다.

---

## 설정 변경 효과 시점 (FR-084)

| 설정 카테고리 | 설정 이름 | 효과 시점 | 비고 |
|--------------|----------|----------|------|
| **안전 필터** | 키워드 패턴 | 즉시 | 재시작 불필요 |
| 안전 필터 | 카테고리 활성화/비활성화 | 즉시 | 재시작 불필요 |
| 안전 필터 | ML 신뢰도 임계값 | 즉시 | 재시작 불필요 |
| **에이전트 시스템** | 라우팅 모드 (LLM/키워드) | 즉시 | 재시작 불필요 (FR-076) |
| 에이전트 시스템 | 에이전트 활성화/비활성화 | 즉시 | 재시작 불필요 |
| 에이전트 시스템 | 키워드 패턴 | 즉시 | 재시작 불필요 |
| **ReAct 도구** | 도구 활성화/비활성화 | 즉시 | 재시작 불필요 |
| **리소스 제한** | 동시 실행 제한 | 재시작 필요 | 미들웨어 초기화 |
| **문서 템플릿** | .jinja2 파일 업로드 | 즉시 | 다음 사용 시 로드 |
| **LLM 백엔드** | llama.cpp ↔ vLLM 전환 | 재시작 필요 | 서비스 초기화 |
| **에이전트 프롬프트** | 프롬프트 파일 수정 | 재시작 필요 | 프롬프트 캐시 |
| **환경 변수** | .env 파일 수정 | 재시작 필요 | 애플리케이션 설정 |

---

## 1. 문서 템플릿 커스터마이징

### 1.1 템플릿 파일 구조

템플릿 위치: `/backend/templates/`

기본 제공 템플릿:
```
templates/
├── 공문서.jinja2
├── 보고서.jinja2
└── 안내문.jinja2
```

### 1.2 새 템플릿 추가

#### 관리자 패널에서 업로드
1. 관리자 패널 > 템플릿 관리
2. "템플릿 업로드" 클릭
3. .jinja2 파일 선택
4. 업로드 (즉시 사용 가능)

#### 파일 시스템에 직접 추가
```bash
# 템플릿 파일 생성
cat > /backend/templates/custom_template.jinja2 << 'EOF'
---
제목: {{ title }}
작성자: {{ author }}
날짜: {{ date }}

{{ content }}

---
담당자: {{ manager }}
부서: {{ department }}
EOF

# 권한 설정
chmod 644 /backend/templates/custom_template.jinja2
```

#### 템플릿 변수

사용 가능한 변수:
- `{{ title }}` - 문서 제목
- `{{ author }}` - 작성자
- `{{ date }}` - 작성 날짜
- `{{ content }}` - 본문 내용
- `{{ department }}` - 부서명
- `{{ manager }}` - 담당자

### 1.3 템플릿 테스트

```python
# Python에서 템플릿 렌더링 테스트
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('/backend/templates/'))
template = env.get_template('custom_template.jinja2')

output = template.render(
    title="테스트 문서",
    author="홍길동",
    date="2025-10-31",
    content="본문 내용입니다.",
    department="총무과",
    manager="김철수"
)

print(output)
```

---

## 2. 에이전트 라우팅 키워드 편집

### 2.1 키워드 기반 라우팅

#### 현재 키워드 패턴 확인
```bash
# API로 현재 키워드 조회
GET /api/v1/admin/agents/citizen_support/keywords
```

#### 키워드 패턴 수정

관리자 패널에서:
1. 멀티 에이전트 > 에이전트 관리
2. 에이전트 선택
3. "키워드 편집" 클릭
4. 키워드 추가/삭제
5. 저장 (즉시 적용)

API로:
```bash
PUT /api/v1/admin/agents/citizen_support/keywords
Content-Type: application/json

{
  "keywords": [
    "민원",
    "건의",
    "불만",
    "답변 작성",
    "시민 문의"
  ]
}
```

### 2.2 에이전트별 키워드 예시

#### 민원 지원 에이전트
```
민원, 건의, 불만, 답변 작성, 시민 문의, 민원인
```

#### 문서 작성 에이전트
```
문서 작성, 보고서, 공문, 초안, 안내문, 정책 문서
```

#### 법규 검색 에이전트
```
법규, 조례, 규정, 법령, 법적 근거, 관련 법
```

#### 데이터 분석 에이전트
```
데이터 분석, 통계, 그래프, 차트, 엑셀, CSV
```

#### 검토 에이전트
```
검토, 확인, 오류, 수정, 개선, 피드백
```

---

## 3. 리소스 제한 조정

### 3.1 현재 제한 확인

```bash
# 현재 리소스 제한 조회
GET /api/v1/admin/config/resource-limits
```

응답:
```json
{
  "max_react_sessions": 10,
  "max_agent_workflows": 5,
  "request_timeout_seconds": 300
}
```

### 3.2 제한 변경

```bash
PUT /api/v1/admin/config/resource-limits
Content-Type: application/json

{
  "max_react_sessions": 15,
  "max_agent_workflows": 7,
  "request_timeout_seconds": 600
}
```

**주의**: 변경 후 재시작 필요
```bash
docker-compose restart backend
```

### 3.3 권장 설정

서버 사양별 권장 설정:

| CPU 코어 | RAM | max_react_sessions | max_agent_workflows |
|---------|-----|-------------------|---------------------|
| 4 core  | 8GB | 5 | 3 |
| 8 core  | 16GB | 10 | 5 |
| 16 core | 32GB | 20 | 10 |

---

## 4. 안전 필터 커스터마이징

### 4.1 키워드 리스트 관리

#### 키워드 추가
```bash
POST /api/v1/admin/safety-filter/keywords
Content-Type: application/json

{
  "category": "violence",
  "keywords": ["새로운 키워드1", "새로운 키워드2"]
}
```

#### 키워드 삭제
```bash
DELETE /api/v1/admin/safety-filter/keywords
Content-Type: application/json

{
  "category": "violence",
  "keywords": ["오탐지_키워드"]
}
```

### 4.2 카테고리별 키워드 파일

키워드 파일 위치: `/backend/data/safety_filter/`

```
safety_filter/
├── violence_keywords.txt
├── sexual_keywords.txt
├── hate_keywords.txt
├── dangerous_keywords.txt
└── pii_patterns.json
```

파일 수정 후 즉시 적용 (재시작 불필요)

### 4.3 PII 패턴 커스터마이징

`pii_patterns.json`:
```json
{
  "주민등록번호": "\d{6}-\d{7}",
  "전화번호": "0\d{1,2}-\d{3,4}-\d{4}",
  "이메일": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
}
```

새 패턴 추가:
```json
{
  "사업자등록번호": "\d{3}-\d{2}-\d{5}"
}
```

---

## 5. LLM 백엔드 전환

### 5.1 llama.cpp (CPU 전용)

`.env` 파일:
```bash
LLM_BACKEND=llama_cpp
LLM_MODEL_PATH=/models/Qwen2.5-3B-Instruct-Q4_K_M.gguf
```

장점:
- CPU만으로 실행 가능
- 설정 단순
- 메모리 사용량 낮음

### 5.2 vLLM (GPU 가속)

`.env` 파일:
```bash
LLM_BACKEND=vllm
LLM_MODEL_PATH=/models/Qwen2.5-1.5B-Instruct
VLLM_GPU_MEMORY_UTILIZATION=0.9
VLLM_MAX_NUM_SEQS=16
```

장점:
- 빠른 응답 속도
- 높은 동시 처리량
- 배치 처리 최적화

**전환 후 재시작 필수**:
```bash
docker-compose down
docker-compose up -d
```

---

## 6. 에이전트 프롬프트 수정

### 6.1 프롬프트 파일 위치

`/backend/prompts/`

```
prompts/
├── citizen_support.txt
├── document_writing.txt
├── legal_research.txt
├── data_analysis.txt
├── review.txt
└── orchestrator_few_shot.txt
```

### 6.2 프롬프트 수정 예시

`citizen_support.txt`:
```
당신은 지방 정부의 민원 지원 AI 에이전트입니다.

역할:
- 시민 민원을 분석하고 공감하는 답변 초안 작성
- 존댓말 사용 (반말 금지)
- 모든 질문 요소에 답변

지침:
1. 민원인의 감정 파악
2. 관련 법규 및 정책 확인
3. 명확하고 친절한 답변 작성
4. 후속 조치 안내

예시:
...
```

### 6.3 프롬프트 테스트

프롬프트 수정 후:
1. 백엔드 재시작
2. 테스트 쿼리 실행
3. 출력 품질 확인
4. 필요 시 반복 조정

---

## 7. 환경 변수 설정

### 7.1 주요 환경 변수

`.env` 파일:
```bash
# 데이터베이스
DATABASE_URL=postgresql://user:pass@localhost:5432/llm_webapp

# LLM 설정
LLM_BACKEND=llama_cpp
LLM_MODEL_PATH=/models/model.gguf

# 세션 설정
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS=3

# 저장소
PER_USER_QUOTA_GB=10

# 안전 필터
SAFETY_FILTER_ENABLED=true
ML_THRESHOLD=0.7

# ReAct
MAX_REACT_SESSIONS=10

# 멀티 에이전트
MAX_AGENT_WORKFLOWS=5
AGENT_ROUTING_MODE=llm  # 또는 keyword
```

### 7.2 환경 변수 변경 적용

```bash
# .env 파일 수정 후
docker-compose down
docker-compose up -d
```

---

## 8. 백업 일정 커스터마이징

### 8.1 Cron 설정 수정

`/etc/cron.d/llm-backup`:
```cron
# 일일 백업 시간 변경 (오전 2시 → 오전 3시)
0 3 * * * root /opt/llm-webapp/scripts/backup-daily.sh

# 주간 백업 요일 변경 (일요일 → 토요일)
0 2 * * 6 root /opt/llm-webapp/scripts/backup-weekly.sh
```

### 8.2 백업 보관 기간 변경

`cleanup-old-backups.sh`:
```bash
# 30일 → 60일
find /backup/daily -name "*.dump" -mtime +60 -delete
```

---

## 9. 모범 사례

### 9.1 변경 전 체크리스트
- [ ] 백업 생성
- [ ] 테스트 환경에서 먼저 테스트
- [ ] 변경 사항 문서화
- [ ] 롤백 계획 수립

### 9.2 변경 후 검증
- [ ] 애플리케이션 로그 확인
- [ ] 헬스 체크 통과 확인
- [ ] 기능 테스트 수행
- [ ] 성능 모니터링

### 9.3 롤백 절차
1. 이전 설정 복원
2. 애플리케이션 재시작
3. 헬스 체크 확인
4. 로그 검토

---

## 10. 문의

커스터마이징 관련 문의는 시스템 관리자에게 연락하세요.
