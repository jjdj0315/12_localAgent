# Research & Technical Decisions: Local LLM Web Application

**Feature**: Local LLM Web Application for Local Government
**Date**: 2025-10-21
**Status**: Complete

## Overview

This document captures research findings and technical decisions for implementing an air-gapped LLM web application. All decisions prioritize maintainability, offline operation, and minimal hardware requirements for small local government deployment.

---

## 1. LLM Model Selection

### Decision: Meta-Llama-3-8B

**Rationale**:
- **Size**: 8B parameters fit in 16GB VRAM (quantized) - achievable with consumer GPUs
- **Korean Support**: Llama 3 has improved multilingual capabilities including Korean
- **Performance**: Competitive quality vs size tradeoff for general tasks
- **License**: Meta Llama 3 Community License permits commercial use
- **Ecosystem**: Excellent vLLM support with optimizations

**Alternatives Considered**:
- **Llama-3-70B**: Rejected - requires 4x A100 GPUs (~280GB VRAM), beyond "minimal hardware"
- **Mistral-7B**: Good performance but weaker Korean support
- **Korean-specific models (KULLM, Polyglot-Ko)**: Considered but Llama 3's multilingual capabilities + broader ecosystem support preferred
- **Llama-3.1 or Llama-3.2**: Could be evaluated if available and compatible with vLLM

**Implementation Notes**:
- Use 4-bit quantization (GPTQ/AWQ) to fit in 16GB VRAM
- Consider INT8 quantization if 4-bit quality insufficient
- Benchmark Korean response quality during testing phase

---

## 2. Inference Engine

### Decision: vLLM

**Rationale**:
- **Performance**: PagedAttention achieves 24x higher throughput vs HuggingFace Transformers
- **Streaming**: Native support for Server-Sent Events (SSE) streaming
- **Batching**: Continuous batching for multiple concurrent users
- **Memory Efficiency**: Optimized KV cache management critical for limited VRAM
- **Production Ready**: Used by major companies (Anthropic, Databricks, etc.)

**Alternatives Considered**:
- **text-generation-inference (TGI)**: Good alternative, but vLLM has better documentation and Korean community
- **llama.cpp**: Excellent for CPU inference but slower than vLLM on GPU
- **Ray Serve + HuggingFace**: More flexible but adds complexity (Ray cluster management)

**Configuration**:
```yaml
model: meta-llama/Meta-Llama-3-8B
tensor_parallel_size: 1  # Single GPU
max_model_len: 4096      # Context window
max_num_seqs: 16         # Concurrent requests
gpu_memory_utilization: 0.9
```

---

## 3. Document Processing & RAG Strategy

### Decision: LangChain + FAISS (for Phase 3)

**Rationale**:
- **LangChain**: Standard framework for document loading, chunking, and Q&A chains
- **FAISS**: Lightweight, no separate server needed, pure in-memory vector search
- **Embedding Model**: Use smaller model (e.g., sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) for Korean+English
- **Offline**: All models/embeddings pre-downloaded before air-gap deployment

**Alternatives Considered**:
- **ChromaDB**: Easier API but adds another service; FAISS simpler for small scale
- **Pinecone/Weaviate**: Require external services, violates air-gap constraint
- **Simple text search**: Insufficient for semantic "summarize this" queries

**Implementation Approach**:
1. **Phase 1-2**: Simple document upload + full-text extraction (no embeddings)
2. **Phase 3**: Add FAISS embeddings for semantic search if needed
3. **Chunking Strategy**: 500-token chunks with 50-token overlap for context

**Document Formats**:
- **PDF**: `pdfplumber` (better layout/table support than PyPDF2)
- **DOCX**: `python-docx`
- **TXT**: Native Python

---

## 4. Frontend Architecture

### Decision: Next.js 14 (App Router) + React Query

**Rationale**:
- **Next.js 14**: SSR improves perceived performance on first load; App Router is modern standard
- **React Query**: Handles caching, optimistic updates, and streaming data elegantly
- **TypeScript**: Type safety critical for maintainability (small team)
- **TailwindCSS**: Rapid UI development without CSS-in-JS runtime overhead

**Streaming UI Pattern**:
```typescript
// Use Server-Sent Events (SSE) for streaming LLM responses
const eventSource = new EventSource('/api/v1/chat/stream');
eventSource.onmessage = (event) => {
  const token = JSON.parse(event.data);
  appendToMessage(token);
};
```

**Alternatives Considered**:
- **Vue/Nuxt**: Team likely more familiar with React ecosystem
- **SvelteKit**: Less mature ecosystem for enterprise use
- **Plain React (CRA)**: Next.js SSR provides better UX for initial load

---

## 5. Backend Framework

### Decision: FastAPI (no Django)

**Rationale**:
- **Async**: Native async/await for concurrent LLM requests critical for performance
- **Auto API Docs**: OpenAPI/Swagger auto-generated (helps with testing)
- **Pydantic**: Request/response validation reduces bugs
- **Simplicity**: Single framework vs FastAPI+Django reduces complexity

**Django Evaluation**:
- **Considered for**: Built-in admin panel for user management
- **Rejected because**:
  - FastAPI can achieve same with custom admin UI (React-based)
  - Django's sync nature conflicts with async LLM calls
  - Two frameworks = more dependencies, complexity

**Admin Panel Strategy**: Build custom React-based admin UI (reuse frontend components)

**Alternatives Considered**:
- **Flask**: Lacks async support, less modern
- **Django Ninja**: Adds FastAPI-like features to Django but still sync core
- **aiohttp**: Lower-level, less batteries-included

---

## 6. Database & ORM

### Decision: PostgreSQL + SQLAlchemy 2.0

**Rationale**:
- **PostgreSQL**: ACID compliance, JSON support (for metadata), full-text search for Korean
- **SQLAlchemy 2.0**: Async support, mature ORM, excellent migration tools (Alembic)
- **Schema Design**: Normalize user, conversations, messages, documents

**Alternatives Considered**:
- **SQLite**: Too limited for concurrent writes (10+ users)
- **MongoDB**: Overkill for relational data, harder to maintain for small teams
- **MySQL**: PostgreSQL has better JSON/full-text support

**Performance Considerations**:
- Index conversation_id, user_id for fast filtering
- Use PostgreSQL full-text search for conversation search (Korean text)
- Partitioning if messages table grows >10M rows (unlikely for 50 users)

---

## 7. Authentication & Session Management

### Decision: Session-based auth with HTTP-only cookies

**Rationale**:
- **Session-based**: Simpler than JWT for same-origin app
- **HTTP-only cookies**: Mitigates XSS attacks
- **Secure flag**: HTTPS enforced (even on internal network)
- **Redis/DB sessions**: Store in PostgreSQL (no Redis needed for 50 users)

**Government Integration**:
- **LDAP/Active Directory**: Support via `python-ldap` or `ldap3` library
- **Fallback**: Local password-based auth if AD not available
- **Implementation**: Abstract auth backend to support both methods

**Password Security**:
- **bcrypt**: Industry standard, slow hashing (10-12 rounds)
- **Alternative**: argon2 (modern, more secure, but bcrypt more familiar)

**Alternatives Considered**:
- **JWT**: Adds complexity (token refresh, storage), unnecessary for web app
- **OAuth2**: Overkill for internal app, no external providers in air-gap
- **Keycloak**: Too heavyweight for 50 users

---

## 8. Deployment & Containerization

### Decision: Docker Compose (single server)

**Rationale**:
- **Docker**: Consistent deployment, all dependencies bundled for air-gap
- **Docker Compose**: Orchestrates 3-4 services (frontend, backend, LLM, DB) on one server
- **No Kubernetes**: Overkill for single server, adds operational complexity

**Service Architecture**:
```yaml
services:
  postgres:
    image: postgres:15
  backend:
    build: ./backend
    depends_on: [postgres]
  llm-service:
    build: ./llm-service
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  frontend:
    build: ./frontend
    depends_on: [backend]
  nginx:  # Optional reverse proxy
    image: nginx:alpine
    depends_on: [frontend, backend]
```

**Air-Gap Deployment Process**:
1. **Preparation (internet-connected machine)**:
   - Build all Docker images
   - Download Llama-3-8B model weights
   - Package as tar files
2. **Transfer**: USB/physical media to air-gapped server
3. **Deploy**: `docker load` images, `docker-compose up`

**Alternatives Considered**:
- **Bare metal**: Harder to maintain Python/Node dependencies
- **VM-based**: Docker provides better isolation + portability
- **Kubernetes**: Too complex for single server

---

## 9. Streaming Response Implementation

### Decision: Server-Sent Events (SSE)

**Rationale**:
- **Simplicity**: HTTP-based, no WebSocket complexity
- **Browser Support**: Native EventSource API
- **vLLM Integration**: vLLM supports SSE out of the box
- **Error Handling**: Automatic reconnection in EventSource

**Implementation**:
```python
# Backend (FastAPI)
@router.get("/chat/stream")
async def stream_chat(prompt: str):
    async def generate():
        async for token in llm_service.stream(prompt):
            yield f"data: {json.dumps({'token': token})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Alternatives Considered**:
- **WebSockets**: Two-way communication unnecessary for LLM streaming
- **Long polling**: Inefficient, higher latency
- **HTTP/2 Server Push**: Browser support inconsistent

---

## 10. Testing Strategy

### Decision: Multi-layer testing approach

**Test Pyramid**:
1. **Unit Tests** (70%): Fast, isolated tests for services/utilities
2. **Integration Tests** (20%): API contract tests, DB interactions
3. **E2E Tests** (10%): Critical user flows (login, chat, upload)

**Frontend Testing**:
- **Jest + React Testing Library**: Component unit tests
- **MSW (Mock Service Worker)**: Mock API responses
- **Playwright**: E2E tests for critical paths

**Backend Testing**:
- **pytest + pytest-asyncio**: Async test support
- **pytest-mock**: Mock vLLM service for fast tests
- **TestClient (FastAPI)**: Integration tests without running server

**Contract Testing**:
- **OpenAPI validation**: Ensure frontend/backend match API spec
- **Pydantic**: Runtime request/response validation

---

## 11. Monitoring & Observability (Air-Gap Constraints)

### Decision: Structured logging + local metrics

**Rationale**:
- **No external services**: Prometheus/Grafana require setup effort
- **Start simple**: Structured JSON logs to files
- **Phase 2 addition**: Add Prometheus + Grafana if needed

**Logging Strategy**:
- **Backend**: Python `structlog` (JSON output)
- **Frontend**: Console logging (errors sent to backend)
- **LLM Service**: vLLM native logging
- **Log aggregation**: Simple log rotation (logrotate)

**Metrics to Track** (admin dashboard):
- Active users (from session table)
- Queries per day/week
- Average response time
- Error rate
- Storage usage
- GPU utilization (nvidia-smi)

**Alternatives Considered**:
- **ELK Stack**: Too heavyweight for 50 users
- **Grafana Loki**: Simpler than ELK but still adds complexity
- **Cloud services**: Violates air-gap requirement

---

## 12. Performance Optimization Strategy

### Decision: Optimize iteratively based on metrics

**Initial Optimizations**:
1. **vLLM config**: Tune `gpu_memory_utilization`, `max_num_seqs`
2. **Database**: Add indexes on foreign keys, timestamps
3. **Frontend**: Code splitting, lazy loading for admin panel
4. **Caching**: React Query caches conversation list

**If performance insufficient**:
1. **Model quantization**: Try INT8 vs 4-bit tradeoff
2. **Response streaming**: Perceived speed >actual speed
3. **Connection pooling**: PostgreSQL connection pool (20-40 connections)
4. **Redis caching**: Add Redis for session storage if DB bottleneck

**Monitoring**:
- Target: 95% of queries <5s total (spec allows 10s)
- Measure: P50, P95, P99 latencies
- Tools: Python `time` module, structured logs

---

## 13. Security Considerations (Air-Gap Environment)

### Decision: Defense in depth despite air-gap

**Key Measures**:
1. **Input Validation**: Pydantic schemas, file type validation
2. **SQL Injection**: SQLAlchemy ORM prevents (no raw SQL)
3. **XSS**: React escapes by default, HTTP-only cookies
4. **CSRF**: SameSite cookies + CSRF tokens for state-changing ops
5. **File Upload**: Magic number validation (not just extension), size limits
6. **Password Storage**: bcrypt with salt

**Less Critical (air-gap protected)**:
- DDoS protection: Limited to internal users
- Rate limiting: Nice-to-have but not critical for 50 users
- HTTPS: Important for MITM prevention even on internal network

**Audit Trail**:
- Log authentication events (success/failure)
- Log admin actions (user creation/deletion)
- Log document uploads (who, when, filename)

---

## 14. Korean Language Optimization

### Decision: UTF-8 throughout, PostgreSQL full-text search

**Database**:
- PostgreSQL encoding: UTF-8
- Full-text search: Use `to_tsvector` with Korean text
- Collation: `ko_KR.UTF-8` for Korean sorting

**LLM**:
- Llama 3 tokenizer handles Korean (BPE with Unicode)
- Verify Korean quality during testing
- Fallback: If quality poor, consider Korean-specific model

**Frontend**:
- Next.js i18n: Support Korean UI labels
- Font: System fonts (Noto Sans KR via CDN cache for offline)

**Testing**:
- Include Korean test cases in all text processing
- Verify special characters (한글, punctuation) handled correctly

---

## 15. Development Workflow & Maintainability

### Decision: Simple tooling, extensive documentation

**Development Tools**:
- **Backend**: Poetry for dependency management, Black for formatting, Ruff for linting
- **Frontend**: npm, ESLint, Prettier
- **Pre-commit hooks**: Format + lint checks

**Documentation Requirements**:
- **README.md**: Setup instructions (for air-gap deployment)
- **API documentation**: Auto-generated OpenAPI (FastAPI)
- **Architecture diagrams**: Mermaid diagrams in docs/
- **Deployment guide**: Step-by-step for IT staff

**Code Quality**:
- Type hints required (Python + TypeScript)
- Docstrings for public functions
- Tests required for new features (CI checks if possible)

---

## Research Summary

All technical unknowns have been resolved with concrete decisions prioritizing:
1. **Maintainability**: Single framework choices (FastAPI only, no Django)
2. **Offline operation**: All dependencies bundled, no external calls
3. **Hardware minimalism**: Llama-3-8B + vLLM optimizations fit 16GB GPU
4. **Performance**: Streaming responses, async backend, optimized inference
5. **Security**: Defense-in-depth despite air-gap environment

**Risk Mitigation**:
- **Korean quality**: Test early with Llama 3; fallback to Korean model if needed
- **Hardware fit**: Quantize model (4-bit) to ensure 16GB VRAM sufficient
- **Complexity**: Avoid Django, Kubernetes, Redis initially; add if proven necessary

Ready to proceed to **Phase 1: Data Model & Contracts**.
