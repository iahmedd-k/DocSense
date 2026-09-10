# DocSense — Requirements Specification

> **Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Classification:** Internal — Engineering

---

## 1. Document Purpose

This document defines the functional and non-functional requirements for the DocSense platform. It serves as the authoritative reference for feature implementation, acceptance criteria, and quality assurance.

---

## 2. Requirement Traceability Matrix

```
┌──────────────┬──────────────────────────────────────────────────────┐
│  Requirement │  Feature                                            │
│     ID       │                                                     │
├──────────────┼──────────────────────────────────────────────────────┤
│  FR-001      │  User Registration                                  │
│  FR-002      │  User Login                                         │
│  FR-003      │  JWT Token Authentication                           │
│  FR-004      │  User Profile                                       │
│  FR-005      │  Logout (Client-Side Token Invalidation)            │
│  FR-006      │  Role-Based Access Control                          │
│  FR-007      │  Admin User Management                              │
│  FR-008      │  Document Upload                                    │
│  FR-009      │  Document Listing                                   │
│  FR-010      │  Document Retrieval                                 │
│  FR-011      │  Document Deletion                                  │
│  FR-012      │  Document Processing Status                         │
│  FR-013      │  PDF Text Extraction                                │
│  FR-014      │  Structure-Aware Chunking                           │
│  FR-015      │  Vector Embedding Generation                        │
│  FR-016      │  Hybrid Search (Vector + Lexical)                   │
│  FR-017      │  Reciprocal Rank Fusion                             │
│  FR-018      │  Cross-Encoder Reranking                            │
│  FR-019      │  Evidence Grading                                   │
│  FR-020      │  Corrective Retrieval Loop                          │
│  FR-021      │  Citation Generation                                │
│  FR-022      │  Answer Verification                                │
│  FR-023      │  Abstention Decision                                │
│  FR-024      │  Streaming Response                                 │
│  FR-025      │  Usage Tracking                                     │
│  FR-026      │  Web Search Fallback                                │
│  FR-027      │  Composed RAG Pipeline                              │
└──────────────┴──────────────────────────────────────────────────────┘
```

---

## 3. Functional Requirements

### 3.1 Authentication & Authorization

#### FR-001: User Registration

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Endpoint** | `POST /api/v1/auth/register` |

**Description:**  
New users can create an account with first name, last name, email, and password.

**Acceptance Criteria:**
- Email must be unique across the system
- Password is hashed with bcrypt before storage
- Default role is `user`
- Returns JWT access token + user profile
- Email validation via `email-validator` library

**Request Schema:**
```json
{
  "first_name": "string (1-50 chars)",
  "last_name": "string (1-50 chars)",
  "email": "string (valid email format)",
  "password": "string (min 8 chars)"
}
```

**Response Schema:**
```json
{
  "access_token": "string (JWT)",
  "token_type": "bearer",
  "user": {
    "id": "integer",
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "role": "user | admin",
    "is_active": "boolean",
    "is_verified": "boolean",
    "created_at": "datetime (ISO 8601)"
  }
}
```

---

#### FR-002: User Login

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Endpoint** | `POST /api/v1/auth/login` |

**Description:**  
Existing users authenticate with email and password to receive a JWT access token.

**Acceptance Criteria:**
- Validates email exists in database
- Verifies password against stored bcrypt hash
- Checks `is_active` flag
- Returns JWT access token + user profile

---

#### FR-003: JWT Token Authentication

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Implementation** | `app/core/security.py` |

**Description:**  
Stateless authentication using HS256-signed JWT tokens.

**Acceptance Criteria:**
- Token contains: `sub` (user ID), `exp`, `iat`, `type: "access"`, `role`
- Default expiry: 60 minutes (configurable)
- Token passed via `Authorization: Bearer <token>` header
- Invalid/expired tokens return 401 Unauthorized

---

#### FR-004: User Profile

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoint** | `GET /api/v1/auth/me` |

**Description:**  
Authenticated users can retrieve their own profile information.

**Acceptance Criteria:**
- Requires valid JWT token
- Returns full user profile (excluding password hash)
- Ownership isolation: users can only see their own profile

---

#### FR-005: Logout

| Attribute | Value |
|-----------|-------|
| **Priority** | P2 — Medium |
| **Endpoint** | `POST /api/v1/auth/logout` |

**Description:**  
Stateless logout — client discards token. Server returns 204 No Content.

**Acceptance Criteria:**
- No server-side token revocation (stateless)
- Returns HTTP 204 No Content
- Client must discard token locally

---

#### FR-006: Role-Based Access Control

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Implementation** | `app/core/deps.py` |

**Description:**  
Two-tier role system: `user` and `admin`.

| Role | Permissions |
|------|-------------|
| `user` | Upload/manage own documents, search, chat |
| `admin` | All user permissions + list users, update user roles |

---

#### FR-007: Admin User Management

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoints** | `GET /api/v1/users`, `PATCH /api/v1/users/{id}/role` |

**Description:**  
Administrators can list all users and modify user roles.

**Acceptance Criteria:**
- Requires admin role
- `GET /users` returns all users (excluding password hashes)
- `PATCH /users/{id}/role` updates target user's role
- Admin cannot demote themselves

---

### 3.2 Document Management

#### FR-008: Document Upload

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Endpoint** | `POST /api/v1/documents/upload` |

**Description:**  
Users upload PDF files that are stored, parsed, chunked, embedded, and indexed.

**Acceptance Criteria:**
- Accepts PDF files only (extension + MIME validation)
- Maximum file size: 10MB (configurable)
- Files stored in Cloudinary with unique keys
- Database record created with status `uploaded`
- Full processing pipeline triggered synchronously:
  1. PDF text extraction (page-by-page)
  2. Structure-aware chunking (500 chars, 50 overlap)
  3. Vector embedding generation (768 dimensions)
  4. Chunk persistence with embeddings
  5. Status updated to `completed` or `failed`

**Processing Flow:**
```
┌─────────┐   ┌───────────┐   ┌───────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐
│ Upload  │──▶│ Validate  │──▶│ Store     │──▶│ Parse    │──▶│ Chunk     │──▶│ Embed    │
│ PDF     │   │ MIME/Size │   │ Cloudinary│   │ pypdf    │   │ Structure │   │ HF API   │
└─────────┘   └───────────┘   └───────────┘   └──────────┘   └───────────┘   └──────────┘
                                                                               │
                                                                               ▼
                                                                          ┌──────────┐
                                                                          │ Persist  │
                                                                          │ pgvector │
                                                                          └──────────┘
```

---

#### FR-009: Document Listing

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoint** | `GET /api/v1/documents` |

**Description:**  
Users can list their own uploaded documents with metadata.

**Acceptance Criteria:**
- Returns only documents owned by the authenticated user
- Includes: id, filename, status, file_size, mime_type, created_at, updated_at
- Sorted by creation date (newest first)

---

#### FR-010: Document Retrieval

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoint** | `GET /api/v1/documents/{document_id}` |

**Description:**  
Users can retrieve details of a specific document.

**Acceptance Criteria:**
- Ownership isolation: users can only access their own documents
- Returns full document metadata
- 404 if document not found or not owned by user

---

#### FR-011: Document Deletion

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoint** | `DELETE /api/v1/documents/{document_id}` |

**Description:**  
Users can delete documents and all associated data.

**Acceptance Criteria:**
- Ownership isolation
- Cascading deletion: document + all chunks + Cloudinary file
- Returns 204 No Content on success

---

#### FR-012: Document Processing Status

| Attribute | Value |
|-----------|-------|
| **Priority** | P2 — Medium |
| **Endpoint** | `GET /api/v1/documents/{document_id}/status` |

**Description:**  
Users can check the processing status of an uploaded document.

**Status Lifecycle:**
```
uploaded ──▶ processing ──▶ completed
                │
                └──────▶ failed
```

---

### 3.3 Document Processing Pipeline

#### FR-013: PDF Text Extraction

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Service** | `app/services/pdf_parser_service.py` |

**Description:**  
Extract text content from PDF documents page-by-page using `pypdf`.

**Acceptance Criteria:**
- Page-by-page extraction preserving page numbers
- Returns list of page content objects with page number and text

---

#### FR-014: Structure-Aware Chunking

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Service** | `app/services/chunking_service.py` |

**Description:**  
Split extracted text into chunks while preserving document structure.

**Acceptance Criteria:**
- Detects: headings, lists, tables, text paragraphs
- Default chunk size: 500 characters (configurable)
- Default overlap: 50 characters (configurable)
- Tables preserve headers in each sub-chunk
- Lists grouped until size limit reached
- Content type labels: `text`, `heading`, `list`, `table`

**Chunking Strategy:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Input Document                            │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Heading │  │  List   │  │  Table  │  │  Text   │      │
│  │  "##    │  │  • item │  │  col1   │  │  para-  │      │
│  │  Intro" │  │  • item │  │  col2   │  │  graph  │      │
│  │         │  │  • item │  │  ...    │  │  text"  │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
│       │             │            │              │           │
│       ▼             ▼            ▼              ▼           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Chunk 1 │  │ Chunk 2 │  │ Chunk 3 │  │ Chunk 4 │      │
│  │heading  │  │list     │  │table    │  │text     │      │
│  │500 chars│  │500 chars│  │500 chars│  │500 chars│      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

#### FR-015: Vector Embedding Generation

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Service** | `app/services/embedding_service.py` |

**Description:**  
Generate 768-dimensional vector embeddings for document chunks using HuggingFace API.

**Acceptance Criteria:**
- Model: `Snowflake/snowflake-arctic-embed-m` (configurable)
- Dimension: 768
- Batch processing for efficiency
- Provider pattern for extensibility
- Lazy initialization of provider

---

### 3.4 Search & Retrieval

#### FR-016: Hybrid Search

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Endpoint** | `GET /api/v1/search` |
| **Service** | `app/services/retrieval_service.py` |

**Description:**  
Search documents using vector, lexical, or hybrid retrieval.

**Acceptance Criteria:**
- Three modes: `vector`, `lexical`, `hybrid` (default)
- Query parameters: `query` (required), `method`, `top_k` (default: 10), `rerank` (bool)
- Vector mode: cosine similarity via pgvector
- Lexical mode: PostgreSQL full-text search with `websearch_to_tsquery`
- Hybrid mode: both vector + lexical with RRF fusion
- Ownership isolation: search only within user's documents

**Search Architecture:**
```
                    ┌─────────────────┐
                    │    User Query   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼──────┐ ┌────▼──────┐
     │ Vector Search │ │ Lexical   │ │  Hybrid   │
     │ (pgvector     │ │ Search    │ │  (RRF     │
     │  cosine)      │ │ (FTS +    │ │   Fusion) │
     │               │ │  ts_rank) │ │           │
     └────────┬──────┘ └────┬──────┘ └────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Optional       │
                    │  Reranking      │
                    │  (Cross-Encoder)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Ranked Results │
                    └─────────────────┘
```

---

#### FR-017: Reciprocal Rank Fusion

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Service** | `app/services/rrf_service.py` |

**Description:**  
Fuse results from vector and lexical search using Reciprocal Rank Fusion.

**Acceptance Criteria:**
- Formula: `RRF(d) = Σ(1 / (k + rank(d)))` where k=60
- Deduplicates by chunk_id
- Results sorted by descending RRF score

---

#### FR-018: Cross-Encoder Reranking

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Service** | `app/services/reranking_service.py` |

**Description:**  
Rerank search results using a cross-encoder model for higher quality relevance scoring.

**Acceptance Criteria:**
- Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Lazy-loaded singleton model instance
- Scores each (query, content) pair via sigmoid
- Fetches extra candidates (top_k × multiplier) before reranking
- Max results capped at 20 (configurable)

---

### 3.5 RAG Pipeline

#### FR-019: Evidence Grading

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Service** | `app/services/evidence_grader_service.py` |

**Description:**  
LLM-based assessment of evidence sufficiency for answering a query.

**Acceptance Criteria:**
- Top-k evidence chunks sent to LLM (default: 4)
- Returns structured verdict:
  - `sufficient`: boolean
  - `confidence_score`: 0.0–1.0
  - `reason`: explanation
  - `missing_information`: list of gaps

---

#### FR-020: Corrective Retrieval Loop

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Service** | `app/services/corrective_retrieval_service.py` |

**Description:**  
Self-correcting retrieval pipeline that refines queries when evidence is insufficient.

**Acceptance Criteria:**
- Bounded loop with max 2 attempts (configurable)
- Stops when: evidence sufficient, max attempts reached, or query stalls (same query twice)
- Preserves provenance from initial retrieval
- Generates corrective queries via LLM

**Loop Flow:**
```
┌────────────────────────────────────────────────────────────┐
│  Attempt 1: Retrieve → Grade → Insufficient?              │
│                                         │                  │
│                                         ▼                  │
│  Attempt 2: Refine Query → Retrieve → Grade → Sufficient? │
│                                            │               │
│                                            ▼               │
│                                       Return Results       │
└────────────────────────────────────────────────────────────┘
```

---

#### FR-021: Citation Generation

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoint** | `POST /api/v1/chat/citations` |

**Description:**  
Generate page/source citations linking answer spans to source documents.

**Acceptance Criteria:**
- LLM generates JSON citations
- Each citation links answer text to source document + page number
- Citations are verifiable against retrieved evidence

---

#### FR-022: Answer Verification

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoint** | `POST /api/v1/chat/verify` |

**Description:**  
Verify that generated answers are supported by retrieved evidence.

**Acceptance Criteria:**
- LLM checks answer support against evidence
- Verifies citation correctness
- Returns verification verdict

---

#### FR-023: Abstention Decision

| Attribute | Value |
|-----------|-------|
| **Priority** | P2 — Medium |
| **Endpoint** | `POST /api/v1/chat/abstain` |

**Description:**  
Decide whether to abstain from answering when evidence is insufficient.

**Acceptance Criteria:**
- LLM evaluates evidence sufficiency
- Returns abstention decision with reason
- Prevents hallucinated answers

---

#### FR-024: Streaming Response

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — High |
| **Endpoint** | `POST /api/v1/chat/stream` |

**Description:**  
Stream LLM responses using Server-Sent Events (SSE).

**Acceptance Criteria:**
- Uses FastAPI `StreamingResponse`
- SSE format for real-time token delivery
- Supports evidence-grounded streaming answers

---

#### FR-025: Usage Tracking

| Attribute | Value |
|-----------|-------|
| **Priority** | P2 — Medium |
| **Endpoint** | `GET /api/v1/usage` |

**Description:**  
Track user's document count, chunk count, and quota information.

**Acceptance Criteria:**
- Returns: document count, chunk count
- Quota limits (currently unlimited: -1)
- Ownership-scoped to authenticated user

---

#### FR-026: Web Search Fallback

| Attribute | Value |
|-----------|-------|
| **Priority** | P3 — Low |
| **Endpoint** | `POST /api/v1/chat/web-search` |

**Description:**  
Optional external web search via DuckDuckGo for supplementary information.

**Acceptance Criteria:**
- HTML scraping via httpx
- Returns search results as structured data
- Optional — not part of core RAG pipeline

---

#### FR-027: Composed RAG Pipeline

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — Critical |
| **Endpoint** | `POST /api/v1/chat/rag` |

**Description:**  
Single composed end-to-end RAG pipeline: query analysis (expansion /
decomposition) → hybrid retrieval + RRF + reranking → evidence grading →
corrective retrieval → grounded generation → citation generation →
verification → bounded answer revision → answer or hard abstention.

**Acceptance Criteria:**
- Query analysis expands multi-keyword questions and decomposes multi-part
  questions into retrieval variants (Flow 3)
- Runs hybrid (vector + lexical) retrieval with RRF fusion and cross-encoder
  reranking per retrieval query
- Grades evidence sufficiency before generation and runs a corrective
  retrieval loop when insufficient (Flow 4)
- Generates a grounded answer with page/source citations
- Verifies support and citations, then revises the answer in a bounded loop
  when verification fails (Flow 4)
- Automatically abstains (hard abstention) when evidence is insufficient or
  verification cannot be satisfied — never returns an ungrounded answer
  (Flow 5)
- Returns a single composed response with `abstained` flag
- LLM failures during analysis/citations degrade gracefully without breaking
  the pipeline

**Response Schema:**
```json
{
  "query": "string",
  "query_analysis": {
    "original_query": "string",
    "expanded_queries": ["string"],
    "sub_queries": ["string"],
    "rationale": "string"
  },
  "evidence": ["ChunkResult"],
  "verdict": "EvidenceVerdict",
  "answer": "string | null",
  "citations": ["SourceCitation"],
  "verification": "VerificationResponse | null",
  "abstained": "boolean",
  "abstention_reason": "string | null",
  "abstention_suggestion": "string",
  "corrective_queries": ["string"],
  "corrective_attempts": "integer",
  "revision_attempts": "integer"
}
```

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR-001 | API response time (CRUD) | < 200ms | p95 latency |
| NFR-002 | Search latency (hybrid) | < 2s | p95 latency |
| NFR-003 | Answer generation (full RAG) | < 10s | end-to-end |
| NFR-004 | Document upload (1MB PDF) | < 30s | processing time |
| NFR-005 | Concurrent users | 50+ | simultaneous sessions |

### 4.2 Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-006 | Document storage | 10,000+ documents |
| NFR-007 | Chunk storage | 1,000,000+ chunks |
| NFR-008 | Embedding index | HNSW with pgvector |
| NFR-009 | Database connections | Connection pooling |

### 4.3 Security

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-010 | Password hashing | bcrypt (salt + hash) |
| NFR-011 | Token security | HS256 JWT, configurable expiry |
| NFR-012 | Data isolation | Ownership-scoped queries |
| NFR-013 | CORS | Configurable allowed origins |
| NFR-014 | File validation | MIME type + extension check |
| NFR-015 | File size limits | Configurable max (default 10MB) |

### 4.4 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-016 | Error handling | Global exception handlers |
| NFR-017 | Graceful degradation | Provider pattern for external services |
| NFR-018 | Data integrity | Cascading deletes, FK constraints |
| NFR-019 | Logging | Structured logging with levels |

### 4.5 Maintainability

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-020 | Code organization | Layered architecture (API → Service → Repository → Model) |
| NFR-021 | Configuration | Pydantic Settings with `.env` support |
| NFR-022 | Database migrations | Alembic with versioned scripts |
| NFR-023 | Testing | pytest with 117+ test cases |
| NFR-024 | Documentation | API docs via OpenAPI/Swagger |

### 4.6 Compliance

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-025 | Data privacy | Users cannot access other users' data |
| NFR-026 | Audit trail | created_at/updated_at timestamps |
| NFR-027 | Role management | Admin-only role modifications |

---

## 5. Constraints

| Constraint | Description |
|------------|-------------|
| **PDF Only** | Current implementation supports PDF files only |
| **Synchronous Processing** | Document processing runs synchronously in the upload request |
| **No Background Queue** | No Celery/Redis task queue for async processing |
| **Stateless Auth** | No server-side token revocation (logout is client-side) |
| **Single Tenant** | Single-tenant deployment model |
| **External Dependencies** | Requires HuggingFace API, Groq API, Cloudinary |

---

## 6. Assumptions

1. Users have reliable internet access for API calls
2. PDF files contain extractable text (not scanned images)
3. HuggingFace and Groq APIs maintain >99.9% uptime
4. PostgreSQL with pgvector extension is available
5. Cloudinary account has sufficient storage quota

---

## 7. Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115.6 | Web framework |
| SQLAlchemy | 2.0.36 | ORM |
| pgvector | 0.3.6 | Vector search |
| Alembic | 1.14.0 | Migrations |
| pypdf | 6.16.2 | PDF parsing |
| python-jose | 3.3.0 | JWT tokens |
| passlib | 1.7.4 | Password hashing |
| cloudinary | 1.46.2 | File storage |
| transformers | ≥4.40.0 | Cross-encoder |
| torch | ≥2.0.0 | ML runtime |

---

*Next: [03-system-architecture.md](./03-system-architecture.md) — Detailed system architecture*
