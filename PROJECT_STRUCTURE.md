# Local LLM Web Application - Project Structure

**Project**: 001-local-llm-webapp (Local Government LLM Chatbot)
**Status**: 244/274 tasks complete (89%)
**Last Updated**: 2025-10-31

---

## Overview

This is an air-gapped, Korean language LLM web application for local government use. The project includes advanced features like multi-agent orchestration, ReAct agents, safety filtering, and comprehensive audit logging.

---

## Root Directory

### Essential Documentation
- **README.md** - Project overview and quick introduction
- **CLAUDE.md** - AI development guidelines and coding standards
- **QUICKSTART.md** - Quick start guide for developers
- **DEPLOYMENT.md** - Deployment overview and instructions
- **DBeaver_연결_가이드.md** - DBeaver database connection guide (Korean)
- **데이터_확인_가이드.md** - Data verification guide (Korean)

### Quick Start Scripts
- **start.bat** - Start application (Docker Compose)
- **stop.bat** - Stop application

### Configuration Files
- **.gitignore** - Git ignore patterns (updated with archive/, scripts/dev/)
- **.env.example** - Environment variable template
- **.env.development** - Development environment configuration
- **.env.production** - Production environment configuration (with 25-item checklist)
- **docker-compose.yml** - Docker orchestration configuration
- **pyproject.toml** - Python project metadata

---

## Backend (`backend/`)

### Core Application (`backend/app/`)

#### API Routes (`app/api/v1/`)
- **auth.py** - Authentication endpoints (login, logout, register)
- **chat.py** - Chat endpoints (/send, /stream) with message limit (T226)
- **documents.py** - Document upload and management
- **conversations.py** - Conversation CRUD operations
- **tags.py** - Tag management with auto-suggestion
- **admin.py** - User management (create, delete, reset password)
- **admin/templates.py** - Template upload for document generation (T209)
- **admin/agents.py** - Agent routing keyword configuration (T210)
- **admin/config.py** - Resource limit configuration (T211)

#### Models (`app/models/`)
- **user.py** - User model with session management
- **admin.py** - Admin model (separate table per FR-033)
- **conversation.py** - Conversation with last_accessed_at, storage_size
- **message.py** - Message model
- **document.py** - Document model with conversation_id FK
- **tag.py** - Tag model with embedding vector

#### Services (`app/services/`)
- **llm_service.py** - LLM integration (llama.cpp with Qwen 2.5 3B)
- **auth_service.py** - Authentication logic with rate limiting (FR-031)
- **tag_service.py** - Semantic tag matching with embeddings (FR-043)
- **storage_service.py** - 10GB quota enforcement and auto-cleanup (FR-020)
- **backup_service.py** - Daily incremental + weekly full backups (FR-042)
- **safety_filter_service.py** - Two-phase safety filter (FR-048, FR-049)
- **react_agent_service.py** - ReAct agent with 6 tools (FR-062)
- **orchestrator_service.py** - Multi-agent orchestrator with 5 agents (FR-070)
- **audit_log_service.py** - Audit logging without PII (FR-083, FR-056)
- **graceful_degradation_service.py** - Fallback strategies (FR-087)

#### Middleware (`app/middleware/`)
- **session_middleware.py** - Session timeout and warning (FR-012)
- **rate_limit_middleware.py** - Rate limiting (60 req/min)
- **data_isolation_middleware.py** - User data isolation (FR-032)
- **resource_limit_middleware.py** - Resource limits (FR-086)

#### Core (`app/core/`)
- **config.py** - Application configuration
- **security.py** - Password hashing (bcrypt cost 12, FR-029)
- **database.py** - Async database connection (SQLAlchemy 2.0)
- **validators.py** - Input validation with 10+ validators (T231)

#### Schemas (`app/schemas/`)
- **auth.py** - Login/register request/response schemas
- **message.py** - Chat request/response schemas
- **conversation.py** - Conversation schemas
- **document.py** - Document upload schemas
- **tag.py** - Tag schemas

### Database Migrations (`backend/alembic/`)
- **env.py** - Alembic environment configuration
- **versions/** - Migration scripts
  - Initial schema
  - Add last_accessed_at columns
  - Add Tag model with vector embeddings
  - Add Admin model

### Testing (`backend/`)
- **test_llama_load.py** - LLM model loading test
- **test_offline_model_loading.py** - Offline model verification
- **test_offline_embedding_loading.py** - Offline embedding verification
- **verify_python_dependencies.py** - Python dependency checker

---

## Frontend (`frontend/`)

### Application (`frontend/src/app/`)
- **layout.tsx** - Root layout with providers
- **page.tsx** - Landing page
- **chat/page.tsx** - Main chat interface
- **login/page.tsx** - Login page
- **admin/page.tsx** - Admin dashboard
- **admin/advanced-features/page.tsx** - Advanced features dashboard (T215)

### Components (`frontend/src/components/`)

#### UI Components (`components/ui/`)
- **Button.tsx**, **Input.tsx**, **Card.tsx** - Basic UI primitives
- **EmptyState.tsx** - Empty state component with Korean messages

#### Chat Components (`components/chat/`)
- **ChatInterface.tsx** - Main chat UI
- **MessageList.tsx** - Message display
- **MessageInput.tsx** - Message input with validation

#### Admin Components (`components/admin/`)
- **AdvancedFeaturesDashboard.tsx** - 4-tab admin dashboard (T212)
- **AuditLogViewer.tsx** - Audit log viewer with filtering (T213)
- **TemplateManager.tsx** - Template upload and management (T214)
- **UserManagement.tsx** - User CRUD operations

#### Auth Components (`components/auth/`)
- **SessionWarningModal.tsx** - Session timeout warning (FR-012)
- **LoginForm.tsx** - Login form with validation

### Libraries (`frontend/src/lib/`)
- **api.ts** - API client with error handling
- **errorMessages.ts** - Centralized Korean error messages (FR-037)
- **localStorage.ts** - Draft message recovery (FR-013)

### Hooks (`frontend/src/hooks/`)
- **useSessionTimeout.ts** - Session timeout management
- **useChatState.ts** - Chat state management
- **useAuth.ts** - Authentication state

### Configuration
- **package.json** - Node.js dependencies
- **next.config.js** - Next.js configuration
- **tailwind.config.js** - TailwindCSS configuration
- **tsconfig.json** - TypeScript configuration
- **verify-node-dependencies.js** - Node dependency checker

---

## Documentation (`docs/`)

### User Documentation (`docs/user/`)
- **user-guide-ko.md** - Complete user guide in Korean (FR-088)

### Admin Documentation (`docs/admin/`)
- **advanced-features-manual.md** - Advanced features guide (T216)
- **backup-restore-guide.md** - Backup and restore procedures (T217)
- **customization-guide.md** - System customization guide (T218)

### Deployment (`docs/deployment/`)
- **deployment-guide.md** - General deployment guide (T219)
- **air-gapped-deployment.md** - Air-gapped deployment steps (T220)
- **air-gapped-verification-checklist.md** - 13-phase verification (T221)
- **DOCKER_TEST_GUIDE.md** - Docker testing guide

### Testing Documentation (`docs/testing/`)
- **MANUAL_TEST_GUIDE.md** - Manual testing scenarios
- **REACT_TEST_GUIDE.md** - React component testing guide
- **REACT_TEST_CHECKLIST.md** - Frontend test checklist

### Development (`docs/development/`)
- **SECURITY_REVIEW.md** - Security review documentation

---

## Tests (`tests/`)

### Validation Scripts
- **performance_test.py** - Concurrent user performance testing (T236, SC-002)
- **success_criteria_validation.py** - SC-001 to SC-020 validation (T237)
- **korean_quality_test.py** - Korean language quality testing (T238, SC-004)
- **security_audit.py** - 8-phase security audit (T239)
- **final_deployment_check.py** - Comprehensive deployment readiness (T240)

---

## Scripts (`scripts/`)

### Production Scripts
- **offline-install.sh** - Air-gapped installation script (T222)
- **bundle-offline-deps.sh** - Bundle dependencies for offline installation
- **README.md** - Comprehensive scripts documentation

### Backup Scripts (`scripts/backup/`)
- **backup-daily.sh** - Daily incremental backup (FR-042)
- **backup-weekly.sh** - Weekly full backup (FR-042)
- **restore-from-backup.sh** - Restore from backup
- **cleanup-old-backups.sh** - Clean up old backup files

### Development Scripts (`scripts/dev/`)
⚠️ **Note**: This directory is gitignored. Contains legacy/personal dev scripts.
- **start-mvp.bat** - MVP quick start (legacy)
- **start-local-dev.bat** - Local development start
- **stop-mvp.bat** - Stop MVP
- **rebuild.bat** - Rebuild containers
- **test_conversations_api.bat/.sh** - API testing scripts

---

## Specifications (`specs/001-local-llm-webapp/`)

### Planning Documents
- **spec.md** - Complete feature specification with 90+ FRs and 20 SCs
- **plan.md** - Implementation plan with 13 phases
- **tasks.md** - 274 granular tasks (244 complete, 89%)
- **constitution.md** - Project constraints and principles

---

## Archive (`archive/`)

Outdated implementation notes moved here:
- **IMPLEMENTATION_STATUS.md** - Old implementation tracking
- **IMPLEMENTATION_SUMMARY.md** - Old summary
- **PROJECT_STATUS_FINAL.md** - Old final status
- **PHASE5_COMPLETE.md** - Phase 5 completion note
- **PHASE10_STRATEGY.md** - Phase 10 strategy doc
- **START_TEST.md** - Initial test notes
- **QUICKSTART_LOCAL.md** - Duplicate quickstart

---

## Key Statistics

### Code Metrics
- **Backend**: ~50+ Python modules, 15,000+ lines
- **Frontend**: ~30+ TypeScript/React components, 10,000+ lines
- **Documentation**: 7 user/admin guides in Korean
- **Tests**: 5 comprehensive validation scripts

### Feature Completion
- **Core Features**: 100% (244/244 core tasks)
- **Manual Testing**: 0% (26 test scenarios pending)
- **Overall**: 89% (244/274 total tasks)

### Technology Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL 15+
- **Frontend**: TypeScript, React 18+, Next.js 14, TailwindCSS
- **LLM**: llama.cpp (CPU) with Qwen 2.5 3B Instruct GGUF
- **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Deployment**: Docker + Docker Compose

---

## Git Ignore Strategy

The `.gitignore` covers:
- **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `*.log`
- **Node.js**: `node_modules/`, `.next/`, `out/`
- **Environment**: `.env`, `.env.local`, `.env.*.local`
- **Database**: `*.db`, `*.sqlite`, `llm_webapp.db`
- **Models**: `models/*.gguf`, `models/*.bin`, `models/*.safetensors`
- **Test Files**: `*cookies.txt`, `test_*.json`, `test_*.py` (ad-hoc tests)
- **Archive**: `archive/` (outdated docs)
- **IDE**: `.vscode/`, `.idea/`, `*.swp`, `.DS_Store`

---

## Next Steps

### Remaining Work (30 tasks, 11%)
1. **Manual Testing Scenarios (26 tasks)**: T241-T266
   - User story scenarios
   - Admin workflows
   - Error handling
   - Security testing
   - Performance validation

2. **Optional vLLM Tasks (4 tasks)**: T267-T270
   - vLLM service setup (if switching from llama.cpp)

### Deployment Readiness
- Run: `python tests/final_deployment_check.py`
- Complete: `docs/deployment/air-gapped-verification-checklist.md` (13 phases)
- Configure: `.env.production` (25-item checklist)
- Execute: `scripts/offline-install.sh`

---

## Contact & Support

For questions about this project structure, refer to:
- **Technical**: `CLAUDE.md` (development guidelines)
- **User Guide**: `docs/user/user-guide-ko.md`
- **Deployment**: `docs/deployment/deployment-guide.md`
- **Admin**: `docs/admin/advanced-features-manual.md`
