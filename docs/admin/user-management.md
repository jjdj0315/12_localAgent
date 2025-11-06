# 사용자 관리 가이드

## 관리자 권한 관리 (FR-118)

### 개요

관리자 권한은 `User.is_admin` 플래그로 관리됩니다. 이 필드가 **단일 진실 공급원(Single Source of Truth)**입니다.

### 관리자 권한 부여

**SQL 명령어:**

```sql
-- 관리자 권한 부여
UPDATE users SET is_admin = TRUE WHERE username = 'admin_username';
```

**주의사항:**
- 권한 부여 전에 사용자가 존재하는지 확인
- 최소 1명의 관리자는 항상 유지해야 함

### 관리자 권한 해제

**SQL 명령어:**

```sql
-- 관리자 권한 해제
UPDATE users SET is_admin = FALSE WHERE username = 'admin_username';
```

**주의사항:**
- ⚠️ **자기 자신의 권한 해제 금지**: 현재 로그인한 관리자는 본인의 권한을 해제할 수 없음
- 최소 1명의 관리자 유지 필요

### 설정 마법사 예외 (FR-034)

초기 설정 시에는 `/api/v1/setup/` 엔드포인트가 관리자 인증 없이 접근 가능합니다.

**예외 조건:**
- 데이터베이스에 사용자가 0명일 때
- 첫 관리자 계정 생성 허용

### 관리자 목록 조회

**SQL 쿼리:**

```sql
-- 모든 관리자 조회
SELECT id, username, email, created_at
FROM users
WHERE is_admin = TRUE
ORDER BY created_at;
```

### 권한 검증

모든 관리자 엔드포인트는 `get_current_admin()` dependency를 사용합니다.

**에러 메시지:**
- 권한 없음: "관리자 권한이 필요합니다."
- HTTP 상태: 403 Forbidden

### 마이그레이션 이력

**20251105_remove_admin**: Admin 테이블 제거, User.is_admin으로 통합
- 기존 admins 테이블의 데이터를 User.is_admin으로 동기화
- 역방향 마이그레이션 지원 (다운그레이드 시 admins 테이블 재생성)

### 보안 권장사항

1. **정기 감사**: 관리자 계정 목록 주기적 검토
2. **최소 권한 원칙**: 필요한 사용자에게만 관리자 권한 부여
3. **권한 해제 로그**: 권한 변경 시 로그 기록 (향후 구현)
4. **비밀번호 정책**: 관리자 계정은 강력한 비밀번호 사용

### 참고 자료

- 프로젝트 명세: `specs/001-local-llm-webapp/spec.md` (FR-033, FR-118)
- API 문서: `backend/app/api/deps.py` (get_current_admin 구현)
