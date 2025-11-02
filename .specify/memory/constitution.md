<!--
================================================================================
SYNC IMPACT REPORT - Constitution Amendment
================================================================================
Version Change: 1.0.0 → 1.1.0
Date: 2025-11-01
Amendment Type: MINOR (new principle added)

Modified Principles:
- ADDED: Principle VI - Windows 개발 환경 호환성

Added Sections:
- § VI: Windows 개발 환경 호환성 (MUST 등급)
  - 경로 처리, 명령어 호환성, 파일 인코딩, Docker 활용
  - 개발 도구 권장사항 및 금지사항 명시

Removed Sections:
- None

Templates Requiring Updates:
- ✅ .specify/templates/plan-template.md - Constitution Check 섹션 검토 완료
- ✅ .specify/templates/spec-template.md - 영향 없음 (기술 중립적 템플릿)
- ✅ .specify/templates/tasks-template.md - Path Conventions 검토 완료
- ⚠ specs/001-local-llm-webapp/plan.md - Windows 환경 고려사항 추가 권장
- ⚠ specs/001-local-llm-webapp/tasks.md - Windows 호환 명령어 검증 필요

Follow-up TODOs:
1. 기존 코드에서 하드코딩된 Unix 경로 확인 및 수정
2. 스크립트 파일 PowerShell 버전 작성 또는 크로스 플랫폼 변환
3. .gitattributes 파일 추가하여 CRLF 처리 정책 명시 권장

Version Bump Rationale:
- MINOR 버전 증가: 새로운 원칙(Principle VI) 추가로 거버넌스 확장
- 기존 원칙 변경 없음 (backward compatible)
- 구현에 영향: Windows 환경 고려사항 필수 적용
================================================================================
-->

# Local LLM Web Application Constitution

## Core Principles

### I. Air-Gap Compatibility (NON-NEGOTIABLE)
**MUST**: Every component, library, and service operates without internet connectivity
- No external API calls, CDNs, or cloud services
- All dependencies bundled in deployment artifacts
- Documentation includes offline deployment procedures

**Rationale**: Government closed-network environment requirement (FR-001)

### II. Korean Language Support (MANDATORY)
**MUST**: All user-facing elements support Korean language
- UI labels and messages in Korean
- Error messages in Korean
- LLM must process Korean queries and generate Korean responses
- Documentation provided in Korean for end users

**Rationale**: Primary user base is Korean-speaking government employees (FR-014, Assumption #4)

### III. Security & Privacy First
**MUST**: User data isolation and session security
- Users can only access their own conversations and documents (FR-011)
- Session timeout enforced (30 minutes, FR-012)
- Password hashing required (bcrypt/argon2)
- Admin actions require elevated privileges

**Rationale**: Government data sensitivity and multi-user environment

### IV. Simplicity Over Optimization
**SHOULD**: Prioritize maintainability over performance optimization
- Monolithic deployment preferred over microservices
- Established libraries over custom implementations (vLLM, LangChain, React Query)
- Clear separation of concerns (frontend/backend/LLM service)

**Rationale**: Small IT team, limited maintenance resources (Assumption #8)

### V. Testability & Observability
**SHOULD**: Enable debugging in air-gapped environment
- Structured logging for troubleshooting
- Clear error messages for users
- Health check endpoints for monitoring
- Independent manual testing per user story acceptance scenarios
- Automated tests not required for MVP; focus on functional validation

**Rationale**: Limited external support; self-service debugging required. Manual testing via acceptance scenarios provides sufficient validation for small-scale deployment.

### VI. Windows 개발 환경 호환성
**MUST**: Windows 운영체제 환경에서 개발 및 테스트
- 경로 구분자: 백슬래시(`\`) 또는 `os.path.join()` 사용 (하드코딩된 `/` 금지)
- 명령어: PowerShell/CMD 호환 명령어 사용 (bash 전용 명령어 금지)
- 파일 인코딩: UTF-8 BOM 없이 저장 (한글 깨짐 방지)
- 줄바꿈: CRLF(`\r\n`) 처리 가능하도록 구현
- Docker: Windows용 Docker Desktop 활용 (WSL2 백엔드 권장)
- 환경변수: `.env` 파일 Windows 경로 형식 지원

**개발 도구 권장사항**:
- IDE: VSCode (Windows 네이티브) 또는 PyCharm
- Python: Windows Installer로 설치된 Python 3.11+
- Git: Git for Windows (CRLF 자동 변환 설정 권장)
- Terminal: PowerShell 7+ 또는 Windows Terminal

**금지사항**:
- Unix 전용 명령어 직접 실행 (예: `chmod`, `ln -s`)
- 하드코딩된 Unix 경로 (예: `/usr/local/bin`)
- Bash 스크립트에만 의존하는 빌드/배포 프로세스

**Rationale**: 개발 환경이 Windows 운영체제이므로 모든 개발/테스트 작업이 Windows에서 원활하게 실행되어야 함. 클라이언트도 Windows 워크스테이션 사용 (plan.md L155 참조).

## Quality Gates

### Pre-Implementation Gates
- [ ] Constitution compliance verified
- [ ] All edge cases converted to functional requirements with error handling
- [ ] Storage limits and retention policy defined

### Pre-Deployment Gates (Per User Story)
- [ ] Independent test scenarios from spec.md passed
- [ ] Manual acceptance testing completed for each user story per spec.md acceptance scenarios (MANDATORY)
- [ ] Korean language functionality verified
- [ ] User isolation verified (multi-user stories)
- [ ] Air-gap deployment tested (no internet required)

### Production Readiness Gates
- [ ] 99% uptime monitoring configured (SC-006)
- [ ] Database backup/restore procedures tested
- [ ] Korean user manual and admin manual complete
- [ ] Load testing with 10 concurrent users passed (SC-002)

## Governance

**Authority**: This constitution supersedes implementation preferences. Violations require explicit justification in `plan.md` Complexity Tracking table.

**Amendments**: Changes require updating this file AND regenerating affected artifacts (`/speckit.plan`, `/speckit.tasks`).

**Enforcement**: Use `/speckit.analyze` to verify compliance before implementation phases.

**Version**: 1.1.0 | **Ratified**: 2025-10-22 | **Last Amended**: 2025-11-01
