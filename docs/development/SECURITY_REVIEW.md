# 🔍 보안 및 안정성 검토 보고서

**프로젝트**: Local LLM Web Application
**검토 날짜**: 2025-01-24
**검토자**: Claude Code (자동 분석)

---

## 🚨 심각한 보안 취약점 (CRITICAL)

### 1. **쿠키 보안 설정 부적절** 🔴
**파일**: `backend/app/api/v1/auth.py:44-53`

**문제**:
```python
response.set_cookie(
    key="session_token",
    value=session.session_token,
    httponly=False,  # ❌ Allow JS access for debugging
    secure=False,    # ❌ HTTP localhost
    samesite="lax",
    max_age=30 * 60,
)
```

**위험도**: 🔴 **CRITICAL**
- `httponly=False`: JavaScript에서 쿠키 접근 가능 → **XSS 공격에 취약**
- `secure=False`: HTTPS 없이 쿠키 전송 → **중간자 공격(MITM)에 취약**

**영향**:
- 공격자가 XSS를 통해 세션 토큰 탈취 가능
- 평문 HTTP에서 세션 토큰 노출 (폐쇄망이어도 내부 공격자에게 취약)

**해결책**:
```python
response.set_cookie(
    key="session_token",
    value=session.session_token,
    httponly=True,   # ✅ XSS 방어
    secure=True,     # ✅ HTTPS 강제 (프로덕션)
    samesite="strict",  # ✅ CSRF 방어 강화
    max_age=30 * 60,
)
```

---

### 2. **기본 SECRET_KEY 사용** 🔴
**파일**: `backend/app/core/config.py:25-27`

**문제**:
```python
SECRET_KEY: str = os.getenv(
    "SECRET_KEY", "your-secret-key-change-in-production-please"  # ❌
)
```

**위험도**: 🔴 **CRITICAL**
- 환경 변수 없으면 예측 가능한 기본값 사용
- 프로덕션 배포 시 그대로 사용될 위험

**영향**:
- 세션 토큰 위조 가능
- 인증 우회 가능

**해결책**:
```python
SECRET_KEY: str = os.getenv("SECRET_KEY")  # ✅ 필수 설정

# 또는 startup에서 검증
if settings.SECRET_KEY == "your-secret-key-change-in-production-please":
    raise ValueError("SECRET_KEY must be changed in production!")
```

---

### 3. **데이터베이스 기본 비밀번호** 🟠
**파일**: `docker-compose.yml:9, 28`

**문제**:
```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}  # ❌
```

**위험도**: 🟠 **HIGH**
- 환경 변수 미설정 시 "changeme" 사용
- 폐쇄망이라도 내부자 공격에 취약

**해결책**:
```yaml
# 기본값 제거, 필수 환경 변수로 설정
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

# 또는 startup 스크립트에서 검증
if [ "$POSTGRES_PASSWORD" == "changeme" ]; then
    echo "ERROR: Change default database password!"
    exit 1
fi
```

---

## ⚠️ 보안 우려사항 (HIGH)

### 4. **Rate Limiting 없음** 🟠
**파일**: 전체 API 엔드포인트

**문제**:
- 로그인 엔드포인트에 Rate Limiting 없음
- Brute-force 공격 가능

**영향**:
- 비밀번호 무차별 대입 공격
- DoS 공격 가능

**해결책**:
```python
# slowapi 또는 fastapi-limiter 사용
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # ✅ 분당 5회 제한
async def login(...):
    ...
```

---

### 5. **CORS 설정 너무 관대** 🟠
**파일**: `backend/app/main.py:16-23`

**문제**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # ❌ 모든 메서드 허용
    allow_headers=["*"],  # ❌ 모든 헤더 허용
    expose_headers=["*"], # ❌ 모든 헤더 노출
)
```

**위험도**: 🟠 **HIGH** (프로덕션 환경)
- 개발 편의를 위해 모든 것 허용
- 의도하지 않은 API 호출 가능

**해결책**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # ✅ 명시적 허용
    allow_headers=["Content-Type", "Authorization"],  # ✅ 필요한 것만
    expose_headers=[],  # ✅ 필요한 것만
)
```

---

### 6. **에러 메시지 정보 노출** 🟡
**파일**: 여러 API 엔드포인트

**문제**:
```python
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"문서 업로드 중 오류가 발생했습니다: {str(e)}"  # ❌ 스택 트레이스 노출
    )
```

**위험도**: 🟡 **MEDIUM**
- 내부 구현 세부사항 노출
- 공격자에게 시스템 정보 제공

**해결책**:
```python
except Exception as e:
    logger.error(f"Document upload failed: {e}")  # ✅ 로그에만 기록
    raise HTTPException(
        status_code=500,
        detail="문서 업로드 중 오류가 발생했습니다"  # ✅ 일반적 메시지
    )
```

---

## 💡 개선 권장사항 (MEDIUM)

### 7. **세션 정리 스케줄러 미구현** 🟡
**파일**: `backend/app/services/auth_service.py:167-186`

**문제**:
- `cleanup_expired_sessions()` 함수 정의됨
- 하지만 자동 실행 스케줄러 없음

**영향**:
- 만료된 세션이 DB에 계속 쌓임
- 성능 저하 및 스토리지 낭비

**해결책**:
```python
# backend/app/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        cleanup_expired_sessions_job,
        trigger="interval",
        hours=1  # 1시간마다 정리
    )
    scheduler.start()

async def cleanup_expired_sessions_job():
    async with get_db() as db:
        await auth_service.cleanup_expired_sessions(db)
```

---

### 8. **파일 업로드 경로 검증 없음** 🟡
**파일**: `backend/app/services/document_service.py`

**문제**:
- 파일명 검증은 있지만 경로 traversal 공격 방어 부족
- `../../etc/passwd` 같은 파일명 가능성

**해결책**:
```python
import os
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    # 경로 구분자 제거
    filename = os.path.basename(filename)
    # 위험한 문자 제거
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # 파일명 길이 제한
    filename = filename[:255]
    return filename
```

---

### 9. **LLM 서비스 장애 처리 부족** 🟡
**파일**: `backend/app/services/llm_service.py`

**문제**:
- LLM 서비스 다운 시 timeout만 의존
- 사용자에게 명확한 오류 메시지 없음

**해결책**:
```python
try:
    response = await client.post(...)
except httpx.TimeoutException:
    raise HTTPException(
        status_code=503,
        detail="AI 서비스가 일시적으로 사용 불가능합니다. 잠시 후 다시 시도해주세요."
    )
except httpx.ConnectError:
    raise HTTPException(
        status_code=503,
        detail="AI 서비스에 연결할 수 없습니다. 관리자에게 문의하세요."
    )
```

---

### 10. **로깅 민감 정보 노출 위험** 🟡
**전체 코드베이스**

**문제**:
- 비밀번호, 세션 토큰이 로그에 기록될 위험

**해결책**:
```python
# 로깅 시 민감 정보 마스킹
def mask_sensitive_data(data: dict) -> dict:
    sensitive_keys = ['password', 'session_token', 'secret_key']
    return {
        k: '***' if k.lower() in sensitive_keys else v
        for k, v in data.items()
    }

logger.info(f"Login attempt: {mask_sensitive_data(credentials)}")
```

---

## ✅ 잘된 보안 구현

### 1. **비밀번호 해싱** ✅
- bcrypt 사용 (12 rounds)
- 안전한 salt 생성

### 2. **SQLAlchemy ORM 사용** ✅
- Parameterized queries로 SQL injection 방어
- 직접 SQL 작성 없음

### 3. **사용자 데이터 격리** ✅
- WHERE user_id 필터링
- 교차 접근 차단

### 4. **세션 만료 처리** ✅
- 30분 타임아웃
- 자동 갱신 (슬라이딩 윈도우)

### 5. **파일 타입 검증** ✅
- Magic number 체크
- 확장자 검증

---

## 📋 우선순위별 조치 사항

### 🔴 즉시 수정 필요 (프로덕션 배포 전 필수)
1. **쿠키 보안 설정** (`httponly=True`, `secure=True`)
2. **SECRET_KEY 검증** (기본값 사용 시 에러)
3. **DB 비밀번호 검증** (기본값 사용 시 에러)

### 🟠 빠른 시일 내 수정 (1주일 내)
4. **Rate Limiting 추가** (로그인 엔드포인트)
5. **CORS 설정 최소화**
6. **에러 메시지 일반화**

### 🟡 개선 권장 (1개월 내)
7. **세션 정리 스케줄러 구현**
8. **파일 업로드 경로 검증 강화**
9. **LLM 서비스 장애 처리 개선**
10. **로깅 민감 정보 마스킹**

---

## 🎯 권장 조치 코드

### 빠른 수정 패치

```python
# backend/app/api/v1/auth.py
response.set_cookie(
    key="session_token",
    value=session.session_token,
    httponly=True,   # ✅ 수정
    secure=True,     # ✅ 수정 (HTTPS 필수)
    samesite="strict",  # ✅ 수정
    max_age=30 * 60,
    path="/",
)
```

```python
# backend/app/main.py (startup 이벤트)
@app.on_event("startup")
async def validate_config():
    if settings.SECRET_KEY == "your-secret-key-change-in-production-please":
        raise RuntimeError("❌ SECRET_KEY must be changed in production!")
    if settings.DEBUG and os.getenv("ENV") == "production":
        raise RuntimeError("❌ DEBUG must be False in production!")
```

```yaml
# docker-compose.yml
backend:
  environment:
    SECRET_KEY: ${SECRET_KEY}  # 기본값 제거
```

---

## 📊 보안 점수

| 항목 | 점수 | 상태 |
|------|------|------|
| 인증/인가 | 7/10 | 🟡 보통 |
| 데이터 보호 | 8/10 | 🟢 양호 |
| 입력 검증 | 8/10 | 🟢 양호 |
| 세션 관리 | 6/10 | 🟡 보통 |
| 에러 처리 | 6/10 | 🟡 보통 |
| 로깅/모니터링 | 5/10 | 🟠 미흡 |
| **전체** | **6.7/10** | **🟡 보통** |

---

## 🔒 최종 권장사항

### 프로덕션 배포 전 필수 조치:
1. ✅ 쿠키 보안 설정 수정
2. ✅ SECRET_KEY 필수 검증 추가
3. ✅ 데이터베이스 비밀번호 검증 추가
4. ✅ HTTPS 적용 (nginx + SSL/TLS)
5. ✅ Rate Limiting 구현

### 배포 후 1개월 내 개선:
- 세션 정리 스케줄러
- 보안 로깅 강화
- 에러 처리 개선
- 침입 탐지 모니터링

**결론**: 현재 코드는 개발 환경에서는 작동하지만, **프로덕션 배포 시 위의 치명적 이슈 3개를 반드시 수정해야 합니다.**
