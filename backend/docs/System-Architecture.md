# DocSense — System Architecture

> **Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Classification:** Internal — Engineering

---

## 1. Architecture Overview

DocSense follows a **layered architecture** pattern with clear separation of concerns across API, Service, Repository, and Model layers. The system employs the **Provider pattern** for external service integrations, enabling swapping of LLM, embedding, and reranking providers without modifying core business logic.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│                         (Web Browser / API Client)                          │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ HTTPS / REST
                                      │ Authorization: Bearer <JWT>
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                              API LAYER                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Router (/api/v1)                                              │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │ │
│  │  │  Auth    │ │  Users   │ │ Documents│ │  Search  │ │   Chat   │   │ │
│  │  │Endpoints │ │Endpoints │ │Endpoints │ │Endpoints │ │Endpoints │   │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Dependencies: get_current_user, require_role, get_db                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                            SERVICE LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │  AuthService │ │DocumentService│ │RetrievalSvc  │ │  ChatService │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │  ChunkingSvc │ │EmbeddingSvc  │ │RerankingSvc  │ │  RRFService  │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │EvidenceGrade │ │QueryRefineSvc│ │CorrectiveSvc │ │  LLMService  │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                  │ │
│  │  │ StorageSvc   │ │PDFParserSvc  │ │  UsageSvc    │                  │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Provider Pattern (Abstract Base → Concrete Implementation)            │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │ │
│  │  │EmbeddingProvider│  │  ChatProvider   │  │CrossEncoderProv │       │ │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘       │ │
│  │           │                    │                    │                  │ │
│  │  ┌────────▼────────┐  ┌───────▼─────────┐  ┌──────▼──────────┐      │ │
│  │  │HuggingFaceEmbed │  │ GroqChatProvider│  │SentenceTransformer│     │ │
│  │  │dingProvider     │  │                 │  │CrossEncoder      │      │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                         REPOSITORY LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌──────────────┐ ┌───────────────────┐ ┌───────────────────────────┐ │ │
│  │  │ UserRepo     │ │ DocumentRepository│ │DocumentChunkRepository    │ │ │
│  │  │              │ │                   │ │  (+ vector/text search)   │ │ │
│  │  └──────────────┘ └───────────────────┘ └───────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                            MODEL LAYER                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌──────────┐ ┌──────────────┐ ┌──────────────┐                      │ │
│  │  │   User   │ │   Document   │ │DocumentChunk │                      │ │
│  │  │  Model   │ │    Model     │ │    Model     │                      │ │
│  │  └──────────┘ └──────────────┘ └──────────────┘                      │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  PostgreSQL + pgvector (Vector(768) + TSVECTOR)                  │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Core Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CORE MODULES                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │   config.py │  │ security.py │  │   deps.py   │  │ logging.py│ │
│  │             │  │             │  │             │  │           │ │
│  │ Pydantic    │  │ JWT +       │  │ FastAPI     │  │ Structured│ │
│  │ Settings    │  │ bcrypt      │  │ Dependencies│  │ Logging   │ │
│  │ (.env)      │  │ utilities   │  │ (DI)        │  │ Setup     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  exceptions/                                                     │ │
│  │  ┌───────────────┐  ┌──────────────────────────────────────────┐│ │
│  │  │ exceptions.py │  │ handlers.py                              ││ │
│  │  │               │  │                                          ││ │
│  │  │ AppException  │  │ Global exception handlers                ││ │
│  │  │ NotFoundError │  │ → JSON error responses                   ││ │
│  │  │ ConflictError │  │ → RequestValidationError                 ││ │
│  │  │ ValidationError│ │ → IntegrityError                         ││ │
│  │  │ Unauthorized  │  │ → Catch-all Exception                    ││ │
│  │  │ Forbidden     │  │                                          ││ │
│  │  │ BadRequest    │  │                                          ││ │
│  │  │ ServiceUnavail│  │                                          ││ │
│  │  └───────────────┘  └──────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Provider Pattern Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROVIDER PATTERN                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    ABSTRACT BASE CLASS                           │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │    │
│  │  │EmbeddingProvider│  │  ChatProvider   │  │CrossEncoderProv │ │    │
│  │  │                 │  │                 │  │                 │ │    │
│  │  │ embed()         │  │ complete()      │  │ rerank()        │ │    │
│  │  │ embed_batch()   │  │ complete_json() │  │                 │ │    │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │    │
│  └───────────┼────────────────────┼────────────────────┼──────────┘    │
│              │                    │                    │                │
│  ┌───────────▼────────┐  ┌───────▼─────────┐  ┌──────▼──────────┐    │
│  │HuggingFaceEmbedding│  │ GroqChatProvider│  │SentenceTransformer│   │
│  │    Provider        │  │                 │  │CrossEncoder      │   │
│  │                    │  │                 │  │                  │   │
│  │ HuggingFace API    │  │ Groq API        │  │ Local model      │   │
│  │ snowflake-arctic   │  │ OpenAI-compat   │  │ MiniLM-L-6-v2    │   │
│  │ 768 dimensions     │  │ JSON completion  │  │ sigmoid scoring  │   │
│  └────────────────────┘  └─────────────────┘  └──────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  LAZY INITIALIZATION                                            │    │
│  │  • Providers instantiated on first use                          │    │
│  │  • Singleton per class (reranker)                               │    │
│  │  • Credentials required only at runtime                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Diagrams

### 3.1 Document Upload Flow

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│ Client │     │  API   │     │Service │     │Storage │     │   DB   │
└───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘
    │              │              │              │              │
    │ POST         │              │              │              │
    │ /documents   │              │              │              │
    │ /upload      │              │              │              │
    │─────────────▶│              │              │              │
    │              │              │              │              │
    │              │ upload_document()           │              │
    │              │─────────────▶│              │              │
    │              │              │              │              │
    │              │              │ validate()   │              │
    │              │              │ (MIME+size)  │              │
    │              │              │────┐         │              │
    │              │              │    │         │              │
    │              │              │◀───┘         │              │
    │              │              │              │              │
    │              │              │ upload_to_cloudinary()      │
    │              │              │─────────────▶│              │
    │              │              │              │              │
    │              │              │ create_document_record()    │
    │              │              │─────────────────────────────▶
    │              │              │              │              │
    │              │              │ parse_pdf()  │              │
    │              │              │ (pypdf)      │              │
    │              │              │────┐         │              │
    │              │              │    │         │              │
    │              │              │◀───┘         │              │
    │              │              │              │              │
    │              │              │ chunk_text() │              │
    │              │              │ (structure-  │              │
    │              │              │  aware)      │              │
    │              │              │────┐         │              │
    │              │              │    │         │              │
    │              │              │◀───┘         │              │
    │              │              │              │              │
    │              │              │ generate_embeddings()       │
    │              │              │ (HuggingFace API)           │
    │              │              │────┐         │              │
    │              │              │    │         │              │
    │              │              │◀───┘         │              │
    │              │              │              │              │
    │              │              │ persist_chunks()            │
    │              │              │─────────────────────────────▶
    │              │              │              │              │
    │              │              │ update_status(COMPLETED)    │
    │              │              │─────────────────────────────▶
    │              │              │              │              │
    │              │ 200 OK       │              │              │
    │◀─────────────│◀─────────────│              │              │
    │              │              │              │              │
```

### 3.2 Hybrid Search Flow

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│ Client │     │  API   │     │Retrieval│    │  RRF   │     │  Reranker│
└───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘
    │              │              │              │              │
    │ GET /search  │              │              │              │
    │ ?query=...   │              │              │              │
    │ &method=hybrid              │              │              │
    │─────────────▶│              │              │              │
    │              │              │              │              │
    │              │ hybrid_search()             │              │
    │              │─────────────▶│              │              │
    │              │              │              │              │
    │              │              │ embed_query()│              │
    │              │              │────┐         │              │
    │              │              │◀───┘         │              │
    │              │              │              │              │
    │              │              │ vector_search()             │
    │              │              │ (pgvector    │              │
    │              │              │  cosine)     │              │
    │              │              │────┐         │              │
    │              │              │◀───┘         │              │
    │              │              │              │              │
    │              │              │ lexical_search()            │
    │              │              │ (PostgreSQL  │              │
    │              │              │  FTS)        │              │
    │              │              │────┐         │              │
    │              │              │◀───┘         │              │
    │              │              │              │              │
    │              │              │ fuse(vector, lexical)       │
    │              │              │─────────────▶│              │
    │              │              │              │              │
    │              │              │              │ RRF scoring  │
    │              │              │              │ dedup + rank │
    │              │              │              │────┐         │
    │              │              │              │◀───┘         │
    │              │              │              │              │
    │              │              │              │ fused results│
    │              │              │◀─────────────│              │
    │              │              │              │              │
    │              │              │ rerank(fused_results)       │
    │              │              │─────────────────────────────▶
    │              │              │              │              │
    │              │              │              │  cross-encoder│
    │              │              │              │  scoring     │
    │              │              │              │────┐         │
    │              │              │              │◀───┘         │
    │              │              │              │              │
    │              │              │              │ ranked results│
    │              │              │◀─────────────────────────────
    │              │              │              │              │
    │              │ SearchResponse│             │              │
    │◀─────────────│◀─────────────│              │              │
```

### 3.3 Corrective Retrieval Loop

```
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ Client │  │  API   │  │Corrective│ │Retrieval│ │Evidence│  │  LLM   │
└───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
    │           │           │           │           │           │
    │ POST /chat│           │           │           │           │
    │ /stream   │           │           │           │           │
    │──────────▶│           │           │           │           │
    │           │           │           │           │           │
    │           │ correct() │           │           │           │
    │           │──────────▶│           │           │           │
    │           │           │           │           │           │
    │           │           │ retrieve_and_rerank() │           │
    │           │           │──────────▶│           │           │
    │           │           │           │           │           │
    │           │           │           │──┐ hybrid │           │
    │           │           │           │◀─┘ search │           │
    │           │           │           │           │           │
    │           │           │           │──┐ rerank │           │
    │           │           │           │◀─┘        │           │
    │           │           │           │           │           │
    │           │           │ results   │           │           │
    │           │           │◀──────────│           │           │
    │           │           │           │           │           │
    │           │           │ grade_evidence()      │           │
    │           │           │──────────────────────▶│           │
    │           │           │           │           │           │
    │           │           │           │           │ grade()   │
    │           │           │           │           │──────────▶│
    │           │           │           │           │           │
    │           │           │           │           │ verdict   │
    │           │           │           │           │◀──────────│
    │           │           │           │           │           │
    │           │           │ verdict   │           │           │
    │           │           │◀──────────│           │           │
    │           │           │           │           │           │
    │           │           │ sufficient?           │           │
    │           │           │────┐      │           │           │
    │           │           │◀───┘      │           │           │
    │           │           │           │           │           │
    │           │           │ [IF NO]   │           │           │
    │           │           │ refine_query()        │           │
    │           │           │──────────────────────▶│           │
    │           │           │           │           │ refine()  │
    │           │           │           │           │──────────▶│
    │           │           │           │           │           │
    │           │           │           │           │ new query │
    │           │           │           │           │◀──────────│
    │           │           │           │           │           │
    │           │           │ new_query │           │           │
    │           │           │◀──────────│           │           │
    │           │           │           │           │           │
    │           │           │ [LOOP: retrieve → grade again]    │
    │           │           │           │           │           │
    │           │           │ final_results         │           │
    │           │◀──────────│           │           │           │
    │           │           │           │           │           │
    │  SSE Stream           │           │           │           │
    │◀──────────│           │           │           │           │
```

---

## 4. Layered Architecture Details

### 4.1 Dependency Injection Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY INJECTION                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FastAPI Request                                                    │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Endpoint Function (e.g., upload_document)                   │    │
│  │  Parameters:                                                 │    │
│  │    - file: UploadFile                                        │    │
│  │    - current_user: User = Depends(get_current_user)          │    │
│  │    - db: Session = Depends(get_db)                           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                             │
│       │ Resolves dependencies:                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  get_current_user(request)                                   │    │
│  │    1. Extract Bearer token from Authorization header         │    │
│  │    2. decode_access_token(token)                             │    │
│  │    3. user_repo.get_by_id(user_id)                           │    │
│  │    4. Validate is_active                                     │    │
│  │    → Returns User                                            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  get_db()                                                    │    │
│  │    1. db = SessionLocal()                                    │    │
│  │    2. yield db                                               │    │
│  │    3. db.close()                                             │    │
│  │    → Returns Session                                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Exception Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EXCEPTION HIERARCHY                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AppException (500 Internal Server Error)                    │    │
│  │  └── Base exception for all application errors               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                             │
│       ├── NotFoundError (404)                                       │
│       │   └── Resource not found                                    │
│       │                                                             │
│       ├── ConflictError (409)                                       │
│       │   └── Resource already exists                               │
│       │                                                             │
│       ├── ValidationError (422)                                     │
│       │   └── Input validation failed                               │
│       │                                                             │
│       ├── UnauthorizedError (401)                                   │
│       │   └── Authentication required                               │
│       │                                                             │
│       ├── ForbiddenError (403)                                      │
│       │   └── Insufficient permissions                              │
│       │                                                             │
│       ├── BadRequestError (400)                                     │
│       │   └── Invalid request                                       │
│       │                                                             │
│       └── ServiceUnavailableError (503)                             │
│           └── External service unavailable                          │
│                                                                     │
│  Global Handlers:                                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AppException → JSON {status_code, message, errors}          │    │
│  │  RequestValidationError → 422 JSON                           │    │
│  │  IntegrityError → 409 Conflict                               │    │
│  │  Exception → 500 Internal Server Error                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Architecture

### 5.1 Authentication Flow

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│ Client │     │  API   │     │Security │     │   DB   │
└───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘
    │              │              │              │
    │ POST /auth/register        │              │
    │ {email, password}          │              │
    │─────────────▶│              │              │
    │              │              │              │
    │              │ register()   │              │
    │              │─────────────▶│              │
    │              │              │              │
    │              │              │ hash_password()
    │              │              │ (bcrypt)     │
    │              │              │────┐         │
    │              │              │◀───┘         │
    │              │              │              │
    │              │              │ create_user()│
    │              │              │─────────────▶│
    │              │              │              │
    │              │              │ create_access_token()
    │              │              │ (HS256 JWT)  │
    │              │              │────┐         │
    │              │              │◀───┘         │
    │              │              │              │
    │  200 OK      │              │              │
    │  {access_token, user}       │              │
    │◀─────────────│◀─────────────│              │
    │              │              │              │
    │              │              │              │
    │ GET /auth/me │              │              │
    │ Authorization: Bearer <jwt> │              │
    │─────────────▶│              │              │
    │              │              │              │
    │              │ get_current_user()          │
    │              │─────────────▶│              │
    │              │              │              │
    │              │              │ decode_token()│
    │              │              │────┐         │
    │              │              │◀───┘         │
    │              │              │              │
    │              │              │ get_user_by_id()
    │              │              │─────────────▶│
    │              │              │              │
    │  200 OK      │              │ user         │
    │  {user}      │              │◀─────────────│
    │◀─────────────│◀─────────────│              │
```

### 5.2 RBAC Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ROLE-BASED ACCESS CONTROL                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Request → get_current_user() → require_role("admin") → Endpoint   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  get_current_user(request)                                   │    │
│  │    │                                                         │    │
│  │    ▼                                                         │    │
│  │  ┌─────────────┐     ┌─────────────┐                        │    │
│  │  │ Extract JWT │────▶│ Decode JWT  │                        │    │
│  │  │ from header │     │ (HS256)     │                        │    │
│  │  └─────────────┘     └──────┬──────┘                        │    │
│  │                              │                               │    │
│  │                              ▼                               │    │
│  │                      ┌──────────────┐                       │    │
│  │                      │ Fetch User   │                       │    │
│  │                      │ from DB      │                       │    │
│  │                      └──────┬───────┘                       │    │
│  │                              │                               │    │
│  │                              ▼                               │    │
│  │                      ┌──────────────┐                       │    │
│  │                      │ Check        │                       │    │
│  │                      │ is_active    │                       │    │
│  │                      └──────┬───────┘                       │    │
│  │                              │                               │    │
│  │                              ▼                               │    │
│  │                      ┌──────────────┐                       │    │
│  │                      │ Return User  │                       │    │
│  │                      └──────────────┘                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  require_role("admin")                                       │    │
│  │    │                                                         │    │
│  │    ▼                                                         │    │
│  │  ┌─────────────┐     ┌─────────────┐                        │    │
│  │  │ Get user    │────▶│ Check role  │                        │    │
│  │  │ from DB     │     │ in allowed  │                        │    │
│  │  └─────────────┘     │ roles       │                        │    │
│  │                      └──────┬──────┘                        │    │
│  │                              │                               │    │
│  │                    ┌─────────┴─────────┐                     │    │
│  │                    │                   │                     │    │
│  │                    ▼                   ▼                     │    │
│  │              ┌──────────┐        ┌──────────┐               │    │
│  │              │  Allow   │        │  Deny    │               │    │
│  │              │  (200)   │        │  (403)   │               │    │
│  │              └──────────┘        └──────────┘               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. External Integrations

### 6.1 External Services Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Cloudinary  │    │  HuggingFace │    │    Groq      │              │
│  │              │    │    API       │    │    API       │              │
│  │  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │              │
│  │  │ Upload │  │    │  │Embed   │  │    │  │Chat    │  │              │
│  │  │ Delete │  │    │  │Generate│  │    │  │Complete│  │              │
│  │  └────────┘  │    │  └────────┘  │    │  └────────┘  │              │
│  │              │    │              │    │              │              │
│  │  Purpose:    │    │  Purpose:    │    │  Purpose:    │              │
│  │  PDF file    │    │  Vector      │    │  LLM text    │              │
│  │  storage     │    │  embeddings  │    │  generation  │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                         │
│  ┌──────────────┐                                                     │
│  │ DuckDuckGo   │                                                     │
│  │              │                                                     │
│  │  ┌────────┐  │                                                     │
│  │  │  HTML  │  │                                                     │
│  │  │Scraper │  │                                                     │
│  │  └────────┘  │                                                     │
│  │              │                                                     │
│  │  Purpose:    │                                                     │
│  │  Web search  │                                                     │
│  │  fallback    │                                                     │
│  └──────────────┘                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Service Communication Patterns

| Service | Protocol | Authentication | Timeout | Retry |
|---------|----------|----------------|---------|-------|
| Cloudinary | HTTPS REST | API Key + Secret | 30s | None |
| HuggingFace | HTTPS REST | Bearer Token | 60s | None |
| Groq | HTTPS REST | API Key | 120s | None |
| DuckDuckGo | HTTPS | None | 10s | None |
| PostgreSQL | TCP | Username + Password | 30s | Connection Pool |

---

## 7. Database Architecture

### 7.1 PostgreSQL Extensions

```
┌─────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL EXTENSIONS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  pgvector 0.3.6                                              │    │
│  │  ┌─────────────────────────────────────────────────────────┐ │    │
│  │  │  Vector(768) column type                                │ │    │
│  │  │  HNSW index for approximate nearest neighbor search     │ │    │
│  │  │  Cosine distance operator (<=>)                         │ │    │
│  │  └─────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Full-Text Search (built-in)                                 │    │
│  │  ┌─────────────────────────────────────────────────────────┐ │    │
│  │  │  TSVECTOR generated column (auto from content)          │ │    │
│  │  │  GIN index for fast text search                          │ │    │
│  │  │  websearch_to_tsquery for natural language queries       │ │    │
│  │  │  ts_rank for relevance scoring                           │ │    │
│  │  └─────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Index Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                       INDEX STRATEGY                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Table: document_chunks                                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ix_document_chunks_embedding_hnsw                           │    │
│  │  Type: HNSW (Hierarchical Navigable Small World)            │    │
│  │  Column: embedding (Vector(768))                             │    │
│  │  Operator Class: vector_cosine_ops                           │    │
│  │  Purpose: Fast approximate nearest neighbor search           │    │
│  │  Query Pattern: SELECT ... ORDER BY embedding <=> $1 LIMIT n │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ix_document_chunks_search_vector_gin                        │    │
│  │  Type: GIN (Generalized Inverted Index)                      │    │
│  │  Column: search_vector (TSVECTOR)                            │    │
│  │  Purpose: Fast full-text search with ranking                 │    │
│  │  Query Pattern: WHERE search_vector @@ websearch_to_tsquery()│    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Table: users                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ix_users_email (UNIQUE) — Login lookups                    │    │
│  │  ix_users_id — Primary key lookup                           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Table: documents                                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ix_documents_storage_key (UNIQUE) — File lookups           │    │
│  │  ix_documents_user_id — Ownership queries                   │    │
│  │  ix_documents_id — Primary key lookup                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Deployment Architecture

### 8.1 Docker Compose Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE TOPOLOGY                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  docker-compose.yml                                              │    │
│  │                                                                  │    │
│  │  ┌─────────────────────┐     ┌─────────────────────┐            │    │
│  │  │      api            │     │        db            │            │    │
│  │  │  ┌───────────────┐  │     │  ┌───────────────┐  │            │    │
│  │  │  │   FastAPI     │  │     │  │  PostgreSQL   │  │            │    │
│  │  │  │   Uvicorn     │──┼────▶│  │  + pgvector   │  │            │    │
│  │  │  │   Port 8000   │  │ TCP │  │  Port 5432    │  │            │    │
│  │  │  └───────────────┘  │     │  └───────────────┘  │            │    │
│  │  │                     │     │                     │            │    │
│  │  │  Build: Dockerfile  │     │  Image: pgvector/   │            │    │
│  │  │  Image: python:3.12 │     │  pgvector:pg16      │            │    │
│  │  │  -slim              │     │  User: docsense     │            │    │
│  │  │                     │     │  Pass: adminadmin   │            │    │
│  │  │  Depends on: db     │     │  Healthcheck: ✓     │            │    │
│  │  │  Healthcheck: ✓     │     │                     │            │    │
│  │  └─────────────────────┘     └─────────────────────┘            │    │
│  │                                                                  │    │
│  │  Network: default (bridge)                                       │    │
│  │  Volumes: db_data (persistent)                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Logging & Observability

### 9.1 Structured Logging

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LOGGING ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Structured Logging (app/core/logging.py)                    │    │
│  │                                                              │    │
│  │  Log Levels:                                                 │    │
│  │  ┌──────────┬──────────────────────────────────────────────┐ │    │
│  │  │  DEBUG   │  Detailed diagnostic information             │ │    │
│  │  │  INFO    │  General operational messages                │ │    │
│  │  │  WARNING │  Unexpected conditions                       │ │    │
│  │  │  ERROR   │  Error conditions                            │ │    │
│  │  │  CRITICAL│  System-level failures                       │ │    │
│  │  └──────────┴──────────────────────────────────────────────┘ │    │
│  │                                                              │    │
│  │  Format: Structured JSON                                     │    │
│  │  Fields: timestamp, level, module, message, extra            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Configuration Management

### 10.1 Environment Configuration

```
┌─────────────────────────────────────────────────────────────────────┐
│                 CONFIGURATION HIERARCHY                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  app/core/config.py (Pydantic Settings)                     │    │
│  │                                                              │    │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │    │
│  │  │ Environment  │    │  .env File   │    │  Code        │  │    │
│  │  │ Variables    │───▶│  (Optional)  │───▶│  Defaults    │  │    │
│  │  │ (Highest)    │    │  (Middle)    │    │  (Lowest)    │  │    │
│  │  └──────────────┘    └──────────────┘    └──────────────┘  │    │
│  │                                                              │    │
│  │  Priority: ENV > .env > Code Defaults                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Settings Categories:                                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  • Database: DATABASE_URL                                    │    │
│  │  • Security: JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRY      │    │
│  │  • CORS: CORS_ORIGINS                                       │    │
│  │  • Storage: CLOUDINARY_CLOUD_NAME/KEY/SECRET                 │    │
│  │  • AI: GROQ_API_KEY, GROQ_CHAT_MODEL, HUGGINGFACE_TOKEN     │    │
│  │  • Chunking: CHUNK_SIZE, CHUNK_OVERLAP                      │    │
│  │  • Retrieval: RETRIEVAL_DEFAULT_TOP_K, RETRIEVAL_MAX_TOP_K  │    │
│  │  • RRF: RRF_K                                               │    │
│  │  • Reranker: RERANKER_MODEL, RERANKER_MAX_RESULTS           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Next: [04-database-design.md](./04-database-design.md) — Database schema & ER diagrams*
