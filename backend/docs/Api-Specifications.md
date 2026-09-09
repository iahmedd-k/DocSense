# DocSense — API Specification

> **Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Classification:** Internal — Engineering  
> **Base URL:** `http://localhost:8000/api/v1`

---

## 1. API Overview

DocSense exposes a RESTful API following OpenAPI 3.1 specification. All endpoints are prefixed with `/api/v1`. Authentication is stateless via JWT Bearer tokens.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API ENDPOINT MAP                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Health                                                         │    │
│  │  GET  /health                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Authentication (No Auth Required)                              │    │
│  │  POST /auth/register                                            │    │
│  │  POST /auth/login                                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Authentication (JWT Required)                                  │    │
│  │  GET  /auth/me                                                  │    │
│  │  POST /auth/logout                                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Users (Admin Only)                                             │    │
│  │  GET    /users                                                  │    │
│  │  PATCH  /users/{user_id}/role                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Documents (JWT Required)                                       │    │
│  │  POST   /documents/upload                                       │    │
│  │  GET    /documents                                              │    │
│  │  GET    /documents/{document_id}                                │    │
│  │  GET    /documents/{document_id}/status                         │    │
│  │  DELETE /documents/{document_id}                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Search (JWT Required)                                          │    │
│  │  GET    /search                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Chat (JWT Required)                                            │    │
│  │  POST /chat/citations                                           │    │
│  │  POST /chat/verify                                              │    │
│  │  POST /chat/abstain                                             │    │
│  │  POST /chat/stream                                              │    │
│  │  POST /chat/web-search                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Usage (JWT Required)                                           │    │
│  │  GET    /usage                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication

### 2.1 JWT Token Format

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JWT TOKEN STRUCTURE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Header:                                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  {                                                          │    │
│  │    "alg": "HS256",                                          │    │
│  │    "typ": "JWT"                                             │    │
│  │  }                                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Payload:                                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  {                                                          │    │
│  │    "sub": "123",           // User ID                       │    │
│  │    "exp": 1700000000,      // Expiration timestamp          │    │
│  │    "iat": 1699996400,      // Issued at timestamp           │    │
│  │    "type": "access",       // Token type                    │    │
│  │    "role": "user"          // User role                     │    │
│  │  }                                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Usage:                                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Authentication Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

---

## 3. Error Responses

### 3.1 Standard Error Format

```json
{
  "status_code": 400,
  "message": "Validation failed",
  "errors": [
    {
      "field": "email",
      "message": "Email already registered"
    }
  ]
}
```

### 3.2 Error Codes

```
┌─────────────────────────────────────────────────────────────────────┐
│                       ERROR CODES                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┬────────────────────────────────────────────────────┐   │
│  │  Code   │  Description                                       │   │
│  ├─────────┼────────────────────────────────────────────────────┤   │
│  │  400    │  Bad Request — Invalid input                       │   │
│  │  401    │  Unauthorized — Authentication required            │   │
│  │  403    │  Forbidden — Insufficient permissions               │   │
│  │  404    │  Not Found — Resource doesn't exist                │   │
│  │  409    │  Conflict — Resource already exists                │   │
│  │  422    │  Validation Error — Schema validation failed       │   │
│  │  500    │  Internal Server Error — Unexpected failure        │   │
│  │  503    │  Service Unavailable — External service down       │   │
│  └─────────┴────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Health Endpoint

### `GET /health`

Returns server health status.

**Authentication:** None

**Response:**
```json
{
  "status": "ok"
}
```

**Status Code:** `200 OK`

---

## 5. Authentication Endpoints

### `POST /auth/register`

Register a new user account.

**Authentication:** None

**Request Body:**
```json
{
  "first_name": "string (1-50 chars, required)",
  "last_name": "string (1-50 chars, required)",
  "email": "string (valid email, required)",
  "password": "string (min 8 chars, required)"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

**Errors:**
- `409 Conflict` — Email already registered

---

### `POST /auth/login`

Authenticate an existing user.

**Authentication:** None

**Request Body:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { ... }
}
```

**Errors:**
- `401 Unauthorized` — Invalid email or password
- `403 Forbidden` — Account deactivated

---

### `GET /auth/me`

Get authenticated user profile.

**Authentication:** JWT Required

**Response:** `200 OK`
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-09-01T10:00:00Z",
  "updated_at": "2026-09-01T10:00:00Z"
}
```

**Errors:**
- `401 Unauthorized` — Invalid or expired token

---

### `POST /auth/logout`

Stateless logout (client discards token).

**Authentication:** JWT Required

**Response:** `204 No Content`

---

## 6. User Management Endpoints

### `GET /users`

List all users (admin only).

**Authentication:** JWT Required + Admin Role

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-09-01T10:00:00Z"
  },
  {
    "id": 2,
    "first_name": "Admin",
    "last_name": "User",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "is_verified": true,
    "created_at": "2026-09-01T09:00:00Z"
  }
]
```

**Errors:**
- `401 Unauthorized` — Invalid or missing token
- `403 Forbidden` — User is not an admin

---

### `PATCH /users/{user_id}/role`

Update a user's role (admin only).

**Authentication:** JWT Required + Admin Role

**Path Parameters:**
- `user_id` (integer) — Target user ID

**Request Body:**
```json
{
  "role": "admin | user"
}
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "role": "admin",
  "is_active": true,
  "is_verified": true,
  "created_at": "2026-09-01T11:00:00Z"
}
```

**Errors:**
- `401 Unauthorized` — Invalid or missing token
- `403 Forbidden` — User is not an admin
- `404 Not Found` — User not found

---

## 7. Document Endpoints

### `POST /documents/upload`

Upload a PDF document for processing.

**Authentication:** JWT Required

**Request:** `multipart/form-data`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF file (max 10MB) |

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "original_filename": "technical-spec.pdf",
  "storage_url": "https://res.cloudinary.com/...",
  "mime_type": "application/pdf",
  "file_size": 1048576,
  "status": "completed",
  "created_at": "2026-09-01T10:00:00Z",
  "updated_at": "2026-09-01T10:00:30Z"
}
```

**Processing Pipeline:**
```
Upload → Validate → Cloudinary → Parse → Chunk → Embed → Store → Complete
```

**Errors:**
- `400 Bad Request` — Invalid file type or size
- `401 Unauthorized` — Invalid or missing token
- `422 Validation Error` — File validation failed

---

### `GET /documents`

List authenticated user's documents.

**Authentication:** JWT Required

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 1,
    "original_filename": "technical-spec.pdf",
    "storage_url": "https://res.cloudinary.com/...",
    "mime_type": "application/pdf",
    "file_size": 1048576,
    "status": "completed",
    "created_at": "2026-09-01T10:00:00Z",
    "updated_at": "2026-09-01T10:00:30Z"
  }
]
```

---

### `GET /documents/{document_id}`

Get a specific document.

**Authentication:** JWT Required (owner only)

**Path Parameters:**
- `document_id` (integer) — Document ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "original_filename": "technical-spec.pdf",
  "storage_url": "https://res.cloudinary.com/...",
  "mime_type": "application/pdf",
  "file_size": 1048576,
  "status": "completed",
  "created_at": "2026-09-01T10:00:00Z",
  "updated_at": "2026-09-01T10:00:30Z"
}
```

**Errors:**
- `404 Not Found` — Document not found or not owned by user

---

### `GET /documents/{document_id}/status`

Get document processing status.

**Authentication:** JWT Required (owner only)

**Path Parameters:**
- `document_id` (integer) — Document ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "completed",
  "created_at": "2026-09-01T10:00:00Z",
  "updated_at": "2026-09-01T10:00:30Z"
}
```

**Status Values:**
- `uploaded` — File uploaded, processing not started
- `processing` — Pipeline actively processing
- `completed` — Processing finished successfully
- `failed` — Processing failed (check logs)

---

### `DELETE /documents/{document_id}`

Delete a document and all associated data.

**Authentication:** JWT Required (owner only)

**Path Parameters:**
- `document_id` (integer) — Document ID

**Response:** `204 No Content`

**Cascading Effects:**
- Deletes all `document_chunks` for this document
- Deletes file from Cloudinary storage

**Errors:**
- `404 Not Found` — Document not found or not owned by user

---

## 8. Search Endpoint

### `GET /search`

Search documents using vector, lexical, or hybrid retrieval.

**Authentication:** JWT Required

**Query Parameters:**
| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `query` | string | — | Yes | Search query text |
| `method` | string | `hybrid` | No | `vector`, `lexical`, or `hybrid` |
| `top_k` | integer | `10` | No | Number of results (max 50) |
| `rerank` | boolean | `false` | No | Enable cross-encoder reranking |

**Response:** `200 OK`
```json
{
  "query": "What is the main algorithm?",
  "method": "hybrid",
  "results": [
    {
      "chunk_id": 42,
      "document_id": 1,
      "page_number": 5,
      "content": "The main algorithm uses a hybrid approach combining...",
      "content_type": "text",
      "score": 0.92,
      "metadata": {}
    },
    {
      "chunk_id": 87,
      "document_id": 1,
      "page_number": 12,
      "content": "Implementation details of the core algorithm...",
      "content_type": "heading",
      "score": 0.85,
      "metadata": {}
    }
  ],
  "total_results": 2
}
```

**Search Methods:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Method        │  Backend           │  Ranking                      │
├────────────────┼────────────────────┼───────────────────────────────┤
│  vector        │  pgvector cosine   │  Cosine distance              │
│  lexical       │  PostgreSQL FTS    │  ts_rank                      │
│  hybrid        │  Both + RRF        │  Reciprocal Rank Fusion       │
└────────────────┴────────────────────┴───────────────────────────────┘
```

**Errors:**
- `401 Unauthorized` — Invalid or missing token
- `422 Validation Error` — Invalid query parameters

---

## 9. Chat Endpoints

### `POST /chat/citations`

Generate page/source citations for a grounded answer.

**Authentication:** JWT Required

**Request Body:**
```json
{
  "query": "string (required)",
  "evidence": [
    {
      "chunk_id": 42,
      "content": "string",
      "page_number": 5,
      "document_id": 1
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "answer": "The algorithm uses a hybrid approach...",
  "citations": [
    {
      "text": "hybrid approach combining vector and lexical search",
      "source": {
        "document_id": 1,
        "page_number": 5,
        "chunk_id": 42
      }
    }
  ]
}
```

---

### `POST /chat/verify`

Verify answer and citations against evidence.

**Authentication:** JWT Required

**Request Body:**
```json
{
  "query": "string",
  "answer": "string",
  "evidence": [...],
  "citations": [...]
}
```

**Response:** `200 OK`
```json
{
  "verified": true,
  "confidence": 0.95,
  "issues": [],
  "suggestions": []
}
```

---

### `POST /chat/abstain`

Decide whether to abstain from answering.

**Authentication:** JWT Required

**Request Body:**
```json
{
  "query": "string",
  "evidence": [...],
  "evidence_verdict": {
    "sufficient": false,
    "confidence_score": 0.3,
    "reason": "Insufficient evidence to answer confidently",
    "missing_information": ["specific algorithm details"]
  }
}
```

**Response:** `200 OK`
```json
{
  "should_abstain": true,
  "reason": "Insufficient evidence to provide an accurate answer",
  "confidence": 0.85
}
```

---

### `POST /chat/stream`

Stream grounded LLM response via Server-Sent Events.

**Authentication:** JWT Required

**Request Body:**
```json
{
  "query": "string",
  "evidence": [...],
  "use_web_search": false
}
```

**Response:** `200 OK` (SSE Stream)
```
data: {"token": "The", "done": false}
data: {"token": " algorithm", "done": false}
data: {"token": " uses", "done": false}
data: {"token": " a", "done": false}
data: {"token": " hybrid", "done": false}
data: {"token": " approach", "done": false}
data: {"token": "", "done": true}
```

---

### `POST /chat/web-search`

External web search via DuckDuckGo.

**Authentication:** JWT Required

**Request Body:**
```json
{
  "query": "string (required)"
}
```

**Response:** `200 OK`
```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "title": "Machine Learning - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "snippet": "Machine learning is a subset of artificial intelligence..."
    }
  ]
}
```

---

## 10. Usage Endpoint

### `GET /usage`

Get user's current usage and quota information.

**Authentication:** JWT Required

**Response:** `200 OK`
```json
{
  "user_id": 1,
  "document_count": 5,
  "chunk_count": 250,
  "quotas": {
    "max_documents": -1,
    "max_chunks": -1
  }
}
```

**Note:** `-1` indicates unlimited quota.

---

## 11. Rate Limiting

```
┌─────────────────────────────────────────────────────────────────────┐
│                      RATE LIMITING                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Current Status: NOT IMPLEMENTED                                     │
│                                                                     │
│  Recommended Limits (for future implementation):                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Endpoint Category      │  Rate Limit                       │    │
│  ├─────────────────────────┼───────────────────────────────────┤    │
│  │  Auth (register/login)  │  10 requests/minute per IP        │    │
│  │  Document Upload        │  5 requests/minute per user       │    │
│  │  Search                 │  60 requests/minute per user      │    │
│  │  Chat                   │  20 requests/minute per user      │    │
│  │  Admin                  │  30 requests/minute per user      │    │
│  └─────────────────────────┴───────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 12. CORS Configuration

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CORS CONFIGURATION                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Environment Variable: CORS_ORIGINS                                 │
│  Default: ["*"] (allow all origins)                                 │
│                                                                     │
│  Production Recommendation:                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  CORS_ORIGINS=["https://docsense.example.com"]              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Allowed Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS            │
│  Allowed Headers: Authorization, Content-Type                       │
│  Allow Credentials: true                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 13. Interactive API Documentation

```
┌─────────────────────────────────────────────────────────────────────┐
│                   SWAGGER / OPENAPI                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FastAPI auto-generates interactive API documentation:              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Swagger UI:  http://localhost:8000/docs                    │    │
│  │  ReDoc:       http://localhost:8000/redoc                   │    │
│  │  OpenAPI JSON: http://localhost:8000/openapi.json           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Features:                                                          │
│  • Try-it-out interface for all endpoints                           │
│  • Schema visualization                                             │
│  • Authentication token injection                                   │
│  • Request/response examples                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Next: [06-testing-strategy.md](./06-testing-strategy.md) — Testing approach & coverage*
