# DocSense — Project Overview

> **Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Classification:** Internal — Engineering

---

## 1. Executive Summary

**DocSense** is an enterprise-grade, AI-powered document question-answering platform that enables users to upload PDF documents and interact with them through natural language queries. The system implements a sophisticated Retrieval-Augmented Generation (RAG) pipeline combining vector search, lexical search, cross-encoder reranking, and LLM-powered answer generation with citations.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DocSense Platform                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│   │  Upload  │───▶│  Parse   │───▶│  Embed   │───▶│  Store   │    │
│   │   PDF    │    │  Extract │    │  Vectors │    │  pgvec   │    │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘    │
│                                                                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│   │  Query   │───▶│ Retrieve │───▶│  Rerank  │───▶│  Answer  │    │
│   │  Search  │    │  Hybrid  │    │  Cross-  │    │  LLM +   │    │
│   │          │    │  Vector  │    │  Encoder  │    │  Citations│   │
│   │          │    │  Lexical │    │          │    │          │    │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Problem Statement

Organizations accumulate vast volumes of PDF documents — technical manuals, legal contracts, research papers, compliance reports — yet lack efficient tools to extract precise answers from them. Manual document review is time-consuming, error-prone, and does not scale.

**DocSense** addresses this by providing:

- Automated PDF ingestion with structure-aware chunking
- Semantic vector embeddings for meaning-based search
- Full-text lexical search for keyword precision
- Hybrid retrieval combining both approaches
- LLM-generated answers grounded in source evidence with verifiable citations

---

## 3. Vision & Goals

| Goal | Description |
|------|-------------|
| **Accuracy** | Ground all answers in retrieved evidence with verifiable citations |
| **Scalability** | Handle growing document corpora via pgvector indexes and efficient chunking |
| **Usability** | Simple upload-and-query workflow with streaming responses |
| **Security** | Role-based access control, JWT authentication, ownership isolation |
| **Extensibility** | Provider pattern for LLMs, embedding models, and rerankers |

---

## 4. High-Level System Context

```
                         ┌─────────────────┐
                         │     User         │
                         │  (Web Browser)   │
                         └────────┬────────┘
                                  │
                           HTTPS / REST
                                  │
                         ┌────────▼────────┐
                         │   FastAPI        │
                         │   Backend        │
                         │   (Port 8000)    │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
     ┌────────▼────────┐ ┌───────▼───────┐ ┌────────▼────────┐
     │   PostgreSQL    │ │  Cloudinary   │ │  External APIs   │
     │   + pgvector    │ │  (File Store) │ │  Groq / HF API   │
     │   (Port 5432)   │ │               │ │  DuckDuckGo      │
     └─────────────────┘ └───────────────┘ └─────────────────┘
```

---

## 5. Core Capabilities

### 5.1 Document Ingestion Pipeline

```
PDF Upload ──▶ Validation ──▶ Cloudinary Storage ──▶ PDF Parsing ──▶ Chunking ──▶ Embedding ──▶ PGStorage
     │              │                │                   │             │            │              │
     │              │                │                   │             │            │              │
  Extension      MIME Type      Cloudinary API       pypdf lib    Structure-   HuggingFace    pgvector
  Size Limit     File Size        Upload              Page-by-     Aware        Snowflake     HNSW Index
```

### 5.2 Hybrid Retrieval Pipeline

```
User Query ──┬──▶ Vector Search ──┬──▶ RRF Fusion ──▶ Cross-Encoder ──▶ LLM Answer
             │   (pgvector        │   (Reciprocal     Reranking         + Citations
             │    cosine)         │    Rank Fusion)   (MiniLM)
             │                   │
             └──▶ Lexical Search ─┘
                  (PostgreSQL FTS
                   ts_rank)
```

### 5.3 Corrective Retrieval Loop

```
┌──────────────────────────────────────────────────────────────────┐
│                    Corrective Retrieval Loop                      │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ Retrieve │───▶│  Grade   │───▶│ Refine   │──┐                │
│  │  Chunks  │    │ Evidence │    │  Query   │  │                │
│  └──────────┘    └────┬─────┘    └──────────┘  │                │
│                       │                         │                │
│                       ▼                         │                │
│               ┌──────────┐                      │                │
│               │Sufficient?│─── Yes ──▶ Return    │                │
│               └────┬─────┘                      │                │
│                    │ No                         │                │
│                    └──────── Retry ◀────────────┘                │
│                       (max 2 attempts)                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Runtime** | Python 3.12+ | Application runtime |
| **Framework** | FastAPI 0.115 | Async REST API framework |
| **Database** | PostgreSQL 16 | Primary data store |
| **Vector DB** | pgvector 0.3 | Semantic vector search |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Migrations** | Alembic 1.14 | Schema versioning |
| **Auth** | JWT + bcrypt | Stateless authentication |
| **File Storage** | Cloudinary | PDF file storage |
| **Embeddings** | HuggingFace API | snowflake-arctic-embed-m (768d) |
| **LLM** | Groq API | OpenAI-compatible completions |
| **Reranker** | Cross-Encoder | ms-marco-MiniLM-L-6-v2 |
| **PDF Parsing** | pypdf 6.16 | Text extraction |
| **Testing** | pytest + httpx | Unit & integration tests |
| **Containerization** | Docker + Compose | Deployment packaging |

---

## 7. Project Structure

```
backend/
├── alembic/                    # Database migrations
│   └── versions/               # Migration scripts (0001-0006)
├── app/
│   ├── core/                   # Configuration, security, dependencies
│   │   ├── config.py           # Pydantic Settings
│   │   ├── security.py         # JWT + bcrypt utilities
│   │   ├── deps.py             # FastAPI DI dependencies
│   │   └── exceptions/         # Custom exception hierarchy
│   ├── db/                     # Database engine & session
│   │   ├── base.py             # DeclarativeBase
│   │   └── session.py          # Engine, SessionLocal, get_db
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic layer
│   └── api/v1/endpoints/       # HTTP route handlers
├── tests/                      # pytest test suite
├── docs/                       # This documentation
├── Dockerfile                  # Container build
├── docker-compose.yml          # Multi-service orchestration
├── alembic.ini                 # Alembic configuration
└── requirements.txt            # Python dependencies
```

---

## 8. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **pgvector over dedicated vector DB** | Reduces infrastructure complexity; single database for relational + vector data |
| **Hybrid retrieval (vector + lexical)** | Combines semantic understanding with keyword precision |
| **Structure-aware chunking** | Preserves document structure (headings, lists, tables) for better retrieval |
| **Cross-encoder reranking** | Higher quality relevance scoring than bi-encoder alone |
| **Corrective retrieval loop** | Self-correcting pipeline that refines queries when evidence is insufficient |
| **Provider pattern for external services** | Enables swapping LLM/embedding/reranker providers without code changes |
| **Stateless JWT auth** | Scalable authentication without server-side session storage |
| **Ownership isolation** | All data queries scoped by user_id for security |

---

## 9. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **API Response Time** | < 200ms for CRUD operations |
| **Search Latency** | < 2s for hybrid retrieval with reranking |
| **Answer Generation** | < 10s for full RAG pipeline |
| **Concurrent Users** | 50+ simultaneous users |
| **Document Size** | Up to 10MB PDFs |
| **Embedding Dimension** | 768 dimensions (snowflake-arctic-embed-m) |
| **Test Coverage** | 117+ test cases across 14 test files |

---

## 10. Stakeholders

| Role | Responsibility |
|------|---------------|
| **End Users** | Upload documents, query knowledge base, receive answers |
| **Administrators** | Manage user roles, monitor system usage |
| **Engineering Team** | Develop, maintain, and operate the platform |

---

*This document provides a high-level overview. Detailed specifications are available in subsequent documents:*
- [02-requirements.md](./02-requirements.md) — Functional & non-functional requirements
- [03-system-architecture.md](./03-system-architecture.md) — Detailed system architecture
- [04-database-design.md](./04-database-design.md) — Database schema & ER diagrams
- [05-api-specification.md](./05-api-specification.md) — REST API reference
- [06-testing-strategy.md](./06-testing-strategy.md) — Testing approach & coverage
- [07-deployment-guide.md](./07-deployment-guide.md) — Deployment procedures
