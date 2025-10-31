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

**Version**: 1.0.0 | **Ratified**: 2025-10-22 | **Last Amended**: 2025-10-22
