# 사용자 관리 가이드

**대상**: 시스템 관리자
**최종 업데이트**: 2025-11-04
**관련 요구사항**: FR-033, FR-118

---

## 개요

이 문서는 Local LLM Web Application의 사용자 계정 및 관리자 권한 관리 방법을 설명합니다.

## 관리자 권한 모델 (FR-118)

**단일 소스**: `users.is_admin` 플래그가 관리자 권한의 유일한 소스입니다.

### 변경 이력
- **2025-11-04 이전**: `admins` 테이블과 `User.is_admin` 플래그 혼용
- **2025-11-04 이후**: `User.is_admin` 플래그만 사용 (마이그레이션 20251104_remove_admin 적용)

---

## 관리자 생성

### 1. 초기 관리자 (첫 실행 시)

시스템 첫 실행 시 **초기 설정 마법사**가 자동으로 실행됩니다:

```bash
# 애플리케이션 시작
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 브라우저에서 접속
http://localhost:8000/setup
```

**설정 마법사 단계**:
1. 관리자 사용자 이름 입력
2. 관리자 비밀번호 설정 (8자 이상)
3. 시스템 이름 구성
4. 저장 공간 할당

설정 완료 후 `setup.lock` 파일이 생성되어 재실행을 방지합니다.

**관련 요구사항**: FR-034

### 2. 추가 관리자 (데이터베이스 직접 수정)

초기 관리자 생성 후, 추가 관리자는 **데이터베이스를 직접 수정**하여 생성합니다.

#### PostgreSQL 사용 시

```sql
-- 기존 사용자에게 관리자 권한 부여
UPDATE users
SET is_admin = TRUE
WHERE username = 'john.doe';

-- 여러 사용자에게 한 번에 권한 부여
UPDATE users
SET is_admin = TRUE
WHERE username IN ('john.doe', 'jane.smith', 'admin2');
```

#### SQLite 사용 시

```bash
# SQLite DB에 접속
sqlite3 llm_webapp.db

# 관리자 권한 부여
UPDATE users
SET is_admin = 1
WHERE username = 'john.doe';

# 종료
.quit
```

**관련 요구사항**: FR-033

---

## 관리자 권한 확인

### 데이터베이스 쿼리

```sql
-- 모든 관리자 목록 조회
SELECT id, username, email, is_admin, created_at
FROM users
WHERE is_admin = TRUE;

-- 특정 사용자의 관리자 여부 확인
SELECT username, is_admin
FROM users
WHERE username = 'john.doe';
```

### API를 통한 확인

```bash
# 현재 사용자 정보 조회 (세션 토큰 필요)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"

# 응답 예시
{
  "user_id": "uuid-here",
  "username": "admin",
  "is_admin": true
}
```

---

## 관리자 권한 제거

### 기본 제거

```sql
-- 관리자 권한 제거
UPDATE users
SET is_admin = FALSE
WHERE username = 'john.doe';
```

### ⚠️ 자기 권한 제거 방지

사용자는 **자신의 관리자 권한을 제거할 수 없습니다** (애플리케이션 레벨에서 방지).

데이터베이스에서 직접 제거하는 경우:

```sql
-- ❌ 위험: 마지막 관리자 제거 시 시스템 관리 불가
-- 먼저 관리자 수 확인
SELECT COUNT(*) FROM users WHERE is_admin = TRUE;

-- 관리자가 2명 이상일 때만 제거
UPDATE users
SET is_admin = FALSE
WHERE username = 'john.doe'
AND (SELECT COUNT(*) FROM users WHERE is_admin = TRUE) > 1;
```

**권장사항**:
- 최소 2명 이상의 관리자 유지
- 권한 제거 전 다른 관리자 계정으로 접속 가능한지 확인

---

## 관리자 기능

관리자 권한으로 접근 가능한 기능:

### 1. 사용자 관리 (`/admin/users`)
- 새 사용자 생성
- 사용자 계정 비활성화/삭제
- 비밀번호 재설정

### 2. 시스템 통계 (`/admin/stats`)
- 활성 사용자 수
- 총 대화/메시지 수
- 저장 공간 사용량

### 3. 시스템 상태 (`/admin/health`)
- 서버 가동 시간
- LLM 서비스 상태
- 데이터베이스 연결 상태

### 4. 메트릭 히스토리 (`/admin/metrics`)
- 시계열 메트릭 그래프
- CSV/PDF 내보내기
- 기간 비교 분석

### 5. 태그 관리 (`/admin/tags`)
- 조직 전체 태그 생성/수정/삭제
- 태그 사용 통계 확인

### 6. 안전 필터 관리 (Phase 8, Optional)
- 필터 규칙 추가/편집
- 필터링 통계 확인
- 카테고리별 활성화/비활성화

---

## 권한 검증 방식

### 코드 레벨 (backend/app/api/deps.py)

```python
async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    관리자 권한 검증 의존성

    데이터 격리 (FR-032):
    모든 API 라우트는 이 의존성을 통해 자동으로 user_id 필터링 적용.
    미들웨어 불필요 - 의존성 레벨에서 격리 보장.

    예시:
    - GET /conversations/{id}: conversation.user_id == current_user.id 검증
    - DELETE /documents/{id}: document.user_id == current_user.id 검증
    """
    if not current_user.is_admin:  # ✅ User.is_admin이 단일 소스
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다."
        )
    return current_user
```

### 라우트 보호 예시

```python
from app.api.deps import get_current_admin

@router.get("/admin/users")
async def list_users(
    _: dict = Depends(get_current_admin)  # 관리자만 접근 가능
):
    # ... 구현
```

---

## 문제 해결

### Q1: 모든 관리자 계정이 잠겼어요
**A**: 데이터베이스에 직접 접속하여 새 관리자 생성:

```sql
-- 기존 사용자를 관리자로 승격
UPDATE users SET is_admin = TRUE WHERE username = 'emergency_admin';

-- 또는 새 관리자 사용자 생성 (비밀번호는 bcrypt로 해시 필요)
-- bcrypt 해시 생성: python -c "import bcrypt; print(bcrypt.hashpw(b'password123', bcrypt.gensalt(rounds=12)).decode())"
INSERT INTO users (id, username, password_hash, is_admin, created_at)
VALUES (
    gen_random_uuid(),
    'emergency_admin',
    '$2b$12$...hashed_password...',
    TRUE,
    NOW()
);
```

### Q2: 관리자 권한이 적용되지 않아요
**A**: 확인 사항:
1. 데이터베이스에서 `is_admin = TRUE` 확인
2. 세션 재로그인 (캐시된 세션 정보 갱신)
3. 애플리케이션 재시작

```bash
# 세션 확인
SELECT * FROM sessions WHERE user_id = (
    SELECT id FROM users WHERE username = 'john.doe'
);

# 기존 세션 삭제 후 재로그인
DELETE FROM sessions WHERE user_id = (
    SELECT id FROM users WHERE username = 'john.doe'
);
```

### Q3: setup.lock 파일을 삭제하면 어떻게 되나요?
**A**:
- ⚠️ **위험**: 초기 설정 마법사가 다시 활성화됨
- 기존 데이터는 유지되나 새 설정이 기존 설정을 덮어쓸 수 있음
- **권장하지 않음**: 관리자 추가는 데이터베이스 직접 수정 방식 사용

---

## 보안 권장사항

1. **최소 권한 원칙**: 필요한 사용자에게만 관리자 권한 부여
2. **강력한 비밀번호**: 관리자 계정은 특히 강력한 비밀번호 사용 (12자 이상)
3. **정기 감사**: 분기별로 관리자 목록 검토
4. **백업 관리자**: 최소 2명 이상의 관리자 계정 유지
5. **접근 로그**: `/admin` 엔드포인트 접근 기록 주기적 확인

```sql
-- 최근 관리자 활동 확인 (세션 기록)
SELECT u.username, s.created_at, s.expires_at, s.last_activity
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE u.is_admin = TRUE
ORDER BY s.last_activity DESC
LIMIT 10;
```

---

## 관련 문서

- [배포 가이드](../deployment/deployment-guide.md)
- [보안 감사](../../backend/tests/security_audit.py)
- [API 문서](http://localhost:8000/docs) (애플리케이션 실행 후 접속)
- [사양서](../../specs/001-local-llm-webapp/spec.md) - FR-033, FR-034, FR-118
