# API Contracts

This directory contains the API contract specifications for the Local LLM Web Application.

## Files

- **api-spec.yaml**: OpenAPI 3.1.0 specification defining all REST API endpoints

## Viewing the Specification

### Online (with internet):
```bash
# Using Swagger UI
npx swagger-ui-dist --port 8080
# Then open http://localhost:8080 and paste api-spec.yaml content
```

### Offline (air-gapped environment):
```bash
# Generate static HTML documentation
npx @redocly/cli build-docs api-spec.yaml --output api-docs.html

# Or use Swagger UI standalone
# Download swagger-ui-dist and serve api-spec.yaml locally
```

## API Overview

**Base URL**: `http://<server-ip>:8000/api/v1`

### Endpoint Categories

1. **Authentication** (`/auth/*`)
   - Login, logout, session management
   - Session-based auth with HTTP-only cookies

2. **Chat** (`/chat/*`)
   - `/chat/send`: Non-streaming LLM responses
   - `/chat/stream`: Streaming LLM responses (SSE)

3. **Conversations** (`/conversations/*`)
   - CRUD operations for conversation management
   - List, create, update, delete conversations
   - Retrieve conversation with full message history

4. **Documents** (`/documents/*`)
   - Upload documents (PDF, TXT, DOCX)
   - List and delete user documents
   - Max 50MB per file

5. **Admin** (`/admin/*`)
   - User management (create, delete, password reset)
   - System statistics and health metrics
   - Admin-only endpoints (requires `is_admin=true`)

## Authentication

All endpoints except `/auth/login` require authentication via session cookie.

**Login Flow**:
1. POST `/auth/login` with username + password
2. Receive `session_token` cookie (HTTP-only, Secure, SameSite=Strict)
3. Include cookie in all subsequent requests (automatic for same-origin)

**Session Expiration**: 30 minutes of inactivity

## Request/Response Formats

### Content Types
- Request: `application/json` (except file uploads: `multipart/form-data`)
- Response: `application/json`
- Streaming: `text/event-stream` (SSE)

### Error Format
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": { /* optional additional info */ }
}
```

### Common HTTP Status Codes
- `200 OK`: Successful GET/POST/PATCH
- `201 Created`: Resource created (POST)
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid session
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: Resource already exists (e.g., duplicate username)
- `413 Payload Too Large`: File exceeds 50MB
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded

## Streaming Responses

The `/chat/stream` endpoint uses **Server-Sent Events (SSE)** for real-time token streaming.

**Event Types**:
- `token`: LLM generated token
- `done`: Response complete
- `error`: Error occurred during generation

**Example**:
```
event: token
data: {"token": "안녕"}

event: token
data: {"token": "하세요"}

event: done
data: {"conversation_id": "uuid", "message_id": "uuid"}
```

**Client-side (JavaScript)**:
```javascript
const eventSource = new EventSource('/api/v1/chat/stream', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    content: "행정 업무 질문"
  })
});

eventSource.addEventListener('token', (event) => {
  const data = JSON.parse(event.data);
  console.log(data.token);
});

eventSource.addEventListener('done', (event) => {
  const data = JSON.parse(event.data);
  eventSource.close();
});
```

## Admin Endpoints

Restricted to users with `is_admin=true`. Returns `403 Forbidden` for regular users.

### Key Admin Functions:
- **User Management**: Create/delete accounts, reset passwords
- **System Monitoring**: Active users, query counts, response times
- **Health Metrics**: CPU/GPU/memory usage, uptime, LLM status

## Validation Rules

### User Input
- **Username**: 3-100 chars, alphanumeric + hyphen/underscore
- **Password**: Min 8 chars, 1 uppercase, 1 lowercase, 1 number
- **Conversation Title**: Max 255 chars
- **Tags**: Max 10 per conversation, each max 50 chars
- **Message Content**: Max 10,000 chars (user queries)
- **LLM Response**: Max 4,000 chars (enforced by backend)

### File Uploads
- **Formats**: PDF, TXT, DOCX
- **Max Size**: 50MB (52,428,800 bytes)
- **Validation**: Magic number check (not just extension)

## Rate Limiting

(Phase 2 feature - not implemented initially)

Suggested limits:
- Login: 5 attempts per 15 minutes per IP
- Chat: 30 queries per minute per user
- Document upload: 10 files per hour per user

## Testing the API

### Using curl:
```bash
# Login
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "employee001", "password": "SecurePass123"}'

# Get conversations (using saved cookie)
curl -b cookies.txt http://localhost:8000/api/v1/conversations

# Send chat message
curl -b cookies.txt -X POST http://localhost:8000/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": null, "content": "안녕하세요"}'

# Upload document
curl -b cookies.txt -X POST http://localhost:8000/api/v1/documents \
  -F "file=@document.pdf"
```

### Using Python (requests):
```python
import requests

session = requests.Session()

# Login
response = session.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "employee001", "password": "SecurePass123"}
)
print(response.json())

# Get conversations
response = session.get("http://localhost:8000/api/v1/conversations")
print(response.json())

# Send chat message
response = session.post(
    "http://localhost:8000/api/v1/chat/send",
    json={
        "conversation_id": None,
        "content": "행정 업무 질문"
    }
)
print(response.json())
```

## Contract Testing

The OpenAPI specification serves as the contract between frontend and backend.

**Validation Tools**:
- **Backend**: FastAPI auto-validates requests/responses against Pydantic schemas
- **Frontend**: Use generated TypeScript types from OpenAPI spec
- **Testing**: Use `openapi-spec-validator` to validate spec file

**Generating TypeScript Types**:
```bash
npx openapi-typescript api-spec.yaml --output types.ts
```

## Changelog

**v1.0.0** (2025-10-21):
- Initial API specification
- Authentication, chat, conversations, documents, admin endpoints
- SSE streaming support for LLM responses
- Session-based authentication

## Future Enhancements

Potential additions (not in current spec):
- WebSocket support for bidirectional communication
- Bulk operations (delete multiple conversations)
- Conversation export (PDF, JSON)
- Advanced search with filters
- LDAP/AD authentication integration
- Audit log endpoints
- System configuration endpoints (admin)
