# DocSense — Database Design

> **Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Classification:** Internal — Engineering

---

## 1. Database Overview

DocSense uses **PostgreSQL 16** with the **pgvector** extension for relational data storage and semantic vector search. The database schema is managed via **Alembic** migrations and accessed through **SQLAlchemy 2.0** ORM.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATABASE TECHNOLOGY                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ PostgreSQL   │  │  pgvector    │  │  SQLAlchemy  │                  │
│  │ 16           │  │ 0.3.6        │  │ 2.0.36       │                  │
│  │              │  │              │  │              │                  │
│  │ Relational   │  │ Vector       │  │ ORM +        │                  │
│  │ + FTS        │  │ Search       │  │ Declarative  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐                                    │
│  │  Alembic     │  │  psycopg     │                                    │
│  │ 1.14.0       │  │ 3.2.3        │                                    │
│  │              │  │              │                                    │
│  │  Schema      │  │  PostgreSQL  │                                    │
│  │  Migrations  │  │  Driver      │                                    │
│  └──────────────┘  └──────────────┘                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENTITY-RELATIONSHIP DIAGRAM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐         ┌─────────────────────────────────┐   │
│  │        users             │         │         documents               │   │
│  ├─────────────────────────┤         ├─────────────────────────────────┤   │
│  │ PK  id           INT    │◀───┐    │ PK  id              INT        │   │
│  │     first_name   VARCHAR│    │    │ FK  user_id         INT        │   │──┐
│  │     last_name    VARCHAR│    │    │     original_filename VARCHAR  │   │  │
│  │     email        VARCHAR│    │    │     storage_key     VARCHAR    │   │  │
│  │     password_hash VARCHAR│    │    │     storage_url     VARCHAR   │   │  │
│  │     role         ENUM   │    │    │     mime_type       VARCHAR   │   │  │
│  │     is_active    BOOLEAN│    │    │     file_size       INT       │   │  │
│  │     is_verified  BOOLEAN│    │    │     status          ENUM      │   │  │
│  │     created_at   DATETIME│    │    │     created_at      DATETIME  │   │  │
│  │     updated_at   DATETIME│    │    │     updated_at      DATETIME  │   │  │
│  └─────────────────────────┘    │    └─────────────────────────────────┘   │
│           │                     │              │                            │
│           │                     │              │                            │
│           │                     │    ┌─────────▼─────────────────────────┐  │
│           │                     │    │      document_chunks              │  │
│           │                     │    ├─────────────────────────────────┤  │
│           │                     │    │ PK  id              INT        │  │
│           │                     └────│ FK  user_id         INT        │  │
│           │                          │ FK  document_id     INT        │  │
│           │                          │     page_number     INT        │  │
│           │                          │     page_numbers    JSONB      │  │
│           │                          │     content         TEXT       │  │
│           │                          │     content_type    VARCHAR    │  │
│           │                          │     metadata        JSONB      │  │
│           │                          │     embedding       VECTOR(768)│  │
│           │                          │     search_vector   TSVECTOR   │  │
│           │                          │     created_at      DATETIME   │  │
│           │                          └─────────────────────────────────┘  │
│           │                                                               │
│           └───────────────────────────────────────────────────────────────┘
│                                                                             │
│  Legend:                                                                    │
│  PK = Primary Key    FK = Foreign Key    INT = Integer    VARCHAR = String  │
│  ENUM = Enumeration  JSONB = JSON Binary VECTOR = pgvector TSVECTOR = FTS   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Table Definitions

### 3.1 `users` Table

```
┌─────────────────────────────────────────────────────────────────────┐
│                           users                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┬─────────────┬───────────────────────────────┐  │
│  │ Column          │ Type        │ Constraints                   │  │
│  ├─────────────────┼─────────────┼───────────────────────────────┤  │
│  │ id              │ INTEGER     │ PK, AUTO INCREMENT, INDEXED  │  │
│  │ first_name      │ VARCHAR(50) │ NOT NULL                      │  │
│  │ last_name       │ VARCHAR(50) │ NOT NULL                      │  │
│  │ email           │ VARCHAR(255)│ UNIQUE, NOT NULL, INDEXED     │  │
│  │ password_hash   │ VARCHAR(255)│ NOT NULL                      │  │
│  │ role            │ ENUM        │ NOT NULL, DEFAULT 'user'      │  │
│  │                 │             │   Values: 'user', 'admin'     │  │
│  │ is_active       │ BOOLEAN     │ NOT NULL, DEFAULT TRUE        │  │
│  │ is_verified     │ BOOLEAN     │ NOT NULL, DEFAULT FALSE       │  │
│  │ created_at      │ DATETIME    │ NOT NULL, DEFAULT utcnow      │  │
│  │ updated_at      │ DATETIME    │ NOT NULL, DEFAULT utcnow      │  │
│  │                 │             │   ON UPDATE utcnow            │  │
│  └─────────────────┴─────────────┴───────────────────────────────┘  │
│                                                                     │
│  Indexes:                                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ix_users_id          — Primary key (B-tree)                │    │
│  │  ix_users_email       — UNIQUE (B-tree) for login lookups   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Role Enum:                                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  user   — Standard user (upload, search, chat)              │    │
│  │  admin  — Administrator (all user + user management)        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 `documents` Table

```
┌─────────────────────────────────────────────────────────────────────┐
│                          documents                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┬─────────────┬───────────────────────────────┐  │
│  │ Column          │ Type        │ Constraints                   │  │
│  ├─────────────────┼─────────────┼───────────────────────────────┤  │
│  │ id              │ INTEGER     │ PK, AUTO INCREMENT, INDEXED  │  │
│  │ user_id         │ INTEGER     │ FK → users.id                │  │
│  │                 │             │   ON DELETE CASCADE          │  │
│  │                 │             │   NOT NULL, INDEXED           │  │
│  │ original_filename│ VARCHAR(255)│ NOT NULL                     │  │
│  │ storage_key     │ VARCHAR(255)│ UNIQUE, NOT NULL, INDEXED    │  │
│  │ storage_url     │ VARCHAR(512)│ NOT NULL                      │  │
│  │ mime_type       │ VARCHAR(100)│ NOT NULL                      │  │
│  │ file_size       │ INTEGER     │ NOT NULL (bytes)              │  │
│  │ status          │ ENUM        │ NOT NULL, DEFAULT 'uploaded'  │  │
│  │                 │             │   Values: 'uploaded',         │  │
│  │                 │             │   'processing', 'completed',  │  │
│  │                 │             │   'failed'                    │  │
│  │ created_at      │ DATETIME    │ NOT NULL, DEFAULT utcnow      │  │
│  │ updated_at      │ DATETIME    │ NOT NULL, DEFAULT utcnow      │  │
│  │                 │             │   ON UPDATE utcnow            │  │
│  └─────────────────┴─────────────┴───────────────────────────────┘  │
│                                                                     │
│  Indexes:                                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ix_documents_id          — Primary key (B-tree)            │    │
│  │  ix_documents_storage_key — UNIQUE (B-tree) for file lookup │    │
│  │  ix_documents_user_id     — (B-tree) for ownership queries  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Status Lifecycle:                                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                                                              │    │
│  │  uploaded ──▶ processing ──▶ completed                       │    │
│  │                 │                                            │    │
│  │                 └──────▶ failed                              │    │
│  │                                                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 `document_chunks` Table

```
┌─────────────────────────────────────────────────────────────────────┐
│                       document_chunks                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┬─────────────┬───────────────────────────────┐  │
│  │ Column          │ Type        │ Constraints                   │  │
│  ├─────────────────┼─────────────┼───────────────────────────────┤  │
│  │ id              │ INTEGER     │ PK, AUTO INCREMENT, INDEXED  │  │
│  │ document_id     │ INTEGER     │ FK → documents.id            │  │
│  │                 │             │   ON DELETE CASCADE          │  │
│  │                 │             │   NOT NULL, INDEXED           │  │
│  │ user_id         │ INTEGER     │ FK → users.id                │  │
│  │                 │             │   ON DELETE CASCADE          │  │
│  │                 │             │   NOT NULL, INDEXED           │  │
│  │ page_number     │ INTEGER     │ NOT NULL                      │  │
│  │ page_numbers    │ JSONB       │ NOT NULL, DEFAULT '[]'        │  │
│  │ content         │ TEXT        │ NOT NULL                      │  │
│  │ content_type    │ VARCHAR(20) │ NOT NULL                      │  │
│  │                 │             │   Values: 'text', 'heading',  │  │
│  │                 │             │   'list', 'table'             │  │
│  │ metadata        │ JSONB       │ NOT NULL, DEFAULT '{}'        │  │
│  │ embedding       │ VECTOR(768) │ NOT NULL                      │  │
│  │ search_vector   │ TSVECTOR    │ GENERATED (auto from content) │  │
│  │                 │             │   Nullable for SQLite         │  │
│  │ created_at      │ DATETIME    │ NOT NULL, DEFAULT utcnow      │  │
│  └─────────────────┴─────────────┴───────────────────────────────┘  │
│                                                                     │
│  Indexes:                                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ix_document_chunks_id              — Primary key (B-tree)  │    │
│  │  ix_document_chunks_document_id     — (B-tree) for doc queries│   │
│  │  ix_document_chunks_user_id         — (B-tree) for user scope│   │
│  │  ix_document_chunks_embedding_hnsw  — HNSW (vector_cosine)  │    │
│  │  ix_document_chunks_search_vector_gin — GIN (full-text)     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Content Type Enum:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  text    — Normal paragraph text                            │    │
│  │  heading — Section title / header                           │    │
│  │  list    — Bullet / numbered list items                     │    │
│  │  table   — Pipe-delimited or wide-space table rows          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Vector Index (HNSW):                                               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Type: HNSW (Hierarchical Navigable Small World)            │    │
│  │  Column: embedding (Vector(768))                             │    │
│  │  Operator Class: vector_cosine_ops                           │    │
│  │  Purpose: Fast approximate nearest neighbor search           │    │
│  │  Query: ORDER BY embedding <=> $1 LIMIT n                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Full-Text Search Index (GIN):                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Type: GIN (Generalized Inverted Index)                      │    │
│  │  Column: search_vector (TSVECTOR, generated)                 │    │
│  │  Purpose: Fast full-text search with ranking                 │    │
│  │  Query: WHERE search_vector @@ websearch_to_tsquery()       │    │
│  │  Ranking: ts_rank(search_vector, query)                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Types Reference

### 4.1 PostgreSQL Types

| Type | Description | Usage |
|------|-------------|-------|
| `INTEGER` | 4-byte signed integer | Primary keys, foreign keys, page numbers |
| `VARCHAR(n)` | Variable-length string with limit | Names, emails, filenames, keys |
| `TEXT` | Variable-length string (unlimited) | Document content |
| `BOOLEAN` | True/false | is_active, is_verified |
| `DATETIME` | Timestamp with timezone | created_at, updated_at |
| `JSONB` | Binary JSON | Metadata, page_numbers |
| `VECTOR(768)` | pgvector 768-dimensional vector | Chunk embeddings |
| `TSVECTOR` | Full-text search vector | Auto-generated from content |
| `ENUM` | Enumeration type | role, status, content_type |

### 4.2 Application-Level Types

```python
# Role Enum (users.role)
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# Status Enum (documents.status)
class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Content Type (document_chunks.content_type)
# Stored as VARCHAR(20) with values:
# "text", "heading", "list", "table"
```

---

## 5. Relationships

### 5.1 Foreign Key Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FOREIGN KEY RELATIONSHIPS                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  users.id ◄──────────── documents.user_id                          │
│    │                      │                                         │
│    │                      │ ON DELETE CASCADE                       │
│    │                      │ (Deleting user removes all documents)   │
│    │                      │                                         │
│    │                      ▼                                         │
│    │               documents.id ◄──── document_chunks.document_id   │
│    │                                    │                           │
│    │                                    │ ON DELETE CASCADE         │
│    │                                    │ (Deleting doc removes     │
│    │                                    │  all chunks)              │
│    │                                    │                           │
│    └────────────────────────────────────┘                           │
│         document_chunks.user_id                                     │
│         ON DELETE CASCADE                                           │
│         (Deleting user removes all their chunks)                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Cascade Rules

| Parent | Child | Cascade | Effect |
|--------|-------|---------|--------|
| `users` | `documents` | `CASCADE` | Delete user → delete all their documents |
| `users` | `document_chunks` | `CASCADE` | Delete user → delete all their chunks |
| `documents` | `document_chunks` | `CASCADE` | Delete document → delete all its chunks |

---

## 6. Indexes

### 6.1 Complete Index Catalog

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          INDEX CATALOG                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Table: users                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Index Name                    │ Type    │ Column │ Purpose     │    │
│  ├────────────────────────────────┼─────────┼────────┼─────────────┤    │
│  │  ix_users_id                   │ B-tree  │ id     │ PK lookup   │    │
│  │  ix_users_email                │ B-tree  │ email  │ Login/unique│    │
│  └────────────────────────────────┴─────────┴────────┴─────────────┘    │
│                                                                         │
│  Table: documents                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Index Name                    │ Type    │ Column │ Purpose     │    │
│  ├────────────────────────────────┼─────────┼────────┼─────────────┤    │
│  │  ix_documents_id               │ B-tree  │ id     │ PK lookup   │    │
│  │  ix_documents_storage_key      │ B-tree  │storage_│ File lookup │    │
│  │                                │  UNIQUE │  key   │             │    │
│  │  ix_documents_user_id          │ B-tree  │user_id │ User scope  │    │
│  └────────────────────────────────┴─────────┴────────┴─────────────┘    │
│                                                                         │
│  Table: document_chunks                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Index Name                    │ Type    │ Column │ Purpose     │    │
│  ├────────────────────────────────┼─────────┼────────┼─────────────┤    │
│  │  ix_document_chunks_id         │ B-tree  │ id     │ PK lookup   │    │
│  │  ix_document_chunks_document_id│ B-tree  │doc_id  │ Doc queries │    │
│  │  ix_document_chunks_user_id    │ B-tree  │user_id │ User scope  │    │
│  │  ix_document_chunks_embedding  │ HNSW    │embed.  │ Vector ANN  │    │
│  │    _hnsw                       │         │        │ (cosine)    │    │
│  │  ix_document_chunks_search_    │ GIN     │search_ │ Full-text   │    │
│  │    vector_gin                  │         │vector  │ search      │    │
│  └────────────────────────────────┴─────────┴────────┴─────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 HNSW Index Configuration

```sql
-- HNSW index for vector similarity search
CREATE INDEX ix_document_chunks_embedding_hnsw
ON document_chunks
USING hnsw (embedding vector_cosine_ops);

-- Parameters (default):
--   m = 16 (number of connections per layer)
--   ef_construction = 64 (size of dynamic candidate list during build)
```

### 6.3 GIN Index Configuration

```sql
-- GIN index for full-text search
CREATE INDEX ix_document_chunks_search_vector_gin
ON document_chunks
USING gin (search_vector);

-- Generated column (auto-maintained by PostgreSQL):
-- search_vector TSVECTOR GENERATED ALWAYS AS (
--   to_tsvector('english', content)
-- ) STORED
```

---

## 7. Migration History

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MIGRATION HISTORY                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┬─────────────────────────────────────────────────────────┐  │
│  │ Version │ Description                                             │  │
│  ├─────────┼─────────────────────────────────────────────────────────┤  │
│  │  0001   │ Create users table                                      │  │
│  │         │ • id (PK), first_name, last_name, email (UNIQUE)       │  │
│  │         │ • password_hash, role (ENUM), is_active, is_verified    │  │
│  │         │ • created_at, updated_at                                │  │
│  │         │ • Indexes: ix_users_id, ix_users_email (UNIQUE)        │  │
│  ├─────────┼─────────────────────────────────────────────────────────┤  │
│  │  0002   │ Create documents table                                  │  │
│  │         │ • id (PK), user_id (FK → users.id CASCADE)             │  │
│  │         │ • filename, storage_key (UNIQUE), mime_type, file_size  │  │
│  │         │ • status (ENUM: uploaded/processing/completed/failed)   │  │
│  │         │ • Indexes: ix_documents_id, ix_documents_storage_key,   │  │
│  │         │   ix_documents_user_id                                  │  │
│  ├─────────┼─────────────────────────────────────────────────────────┤  │
│  │  0003   │ Extend document status lifecycle                        │  │
│  │         │ • No DDL change (VARCHAR status already supports values)│  │
│  ├─────────┼─────────────────────────────────────────────────────────┤  │
│  │  0004   │ Document filename and URL update                        │  │
│  │         │ • Rename: filename → original_filename                  │  │
│  │         │ • Add: storage_url (VARCHAR(512))                       │  │
│  ├─────────┼─────────────────────────────────────────────────────────┤  │
│  │  0005   │ Create document_chunks table with pgvector              │  │
│  │         │ • id (PK), document_id (FK), user_id (FK)              │  │
│  │         │ • page_number, page_numbers (JSONB), content (TEXT)     │  │
│  │         │ • content_type, metadata (JSONB)                        │  │
│  │         │ • embedding (VECTOR(768))                               │  │
│  │         │ • Indexes: ix_document_chunks_id, _document_id, _user_id│  │
│  ├─────────┼─────────────────────────────────────────────────────────┤  │
│  │  0006   │ Add retrieval indexes                                   │  │
│  │         │ • HNSW index on embedding (vector_cosine_ops)          │  │
│  │         │ • Generated TSVECTOR column on content                  │  │
│  │         │ • GIN index on search_vector                            │  │
│  └─────────┴─────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Migration Flow:                                                        │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐ │
│  │  0001   │──▶│  0002   │──▶│  0003   │──▶│  0004   │──▶│  0005   │ │
│  │  users  │   │documents│   │ status  │   │ filename│   │ chunks  │ │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └────┬────┘ │
│                                                                 │      │
│                                                            ┌────▼────┐ │
│                                                            │  0006   │ │
│                                                            │ indexes │ │
│                                                            └─────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Data Access Patterns

### 8.1 Common Query Patterns

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       QUERY PATTERNS                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Vector Similarity Search                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  SELECT *, embedding <=> $query_vector AS distance              │    │
│  │  FROM document_chunks                                           │    │
│  │  WHERE user_id = $user_id                                      │    │
│  │  ORDER BY embedding <=> $query_vector                          │    │
│  │  LIMIT $top_k;                                                  │    │
│  │                                                                 │    │
│  │  Index Used: ix_document_chunks_embedding_hnsw (HNSW)          │    │
│  │  Cost: O(log n) approximate                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  2. Full-Text Search                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  SELECT *, ts_rank(search_vector, query) AS rank                │    │
│  │  FROM document_chunks                                           │    │
│  │  WHERE user_id = $user_id                                      │    │
│  │    AND search_vector @@ websearch_to_tsquery('english', $query) │    │
│  │  ORDER BY ts_rank(search_vector, query) DESC                   │    │
│  │  LIMIT $top_k;                                                  │    │
│  │                                                                 │    │
│  │  Index Used: ix_document_chunks_search_vector_gin (GIN)        │    │
│  │  Cost: O(log n)                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  3. Ownership-Scoped Document Query                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  SELECT * FROM documents                                        │    │
│  │  WHERE user_id = $user_id                                      │    │
│  │  ORDER BY created_at DESC;                                      │    │
│  │                                                                 │    │
│  │  Index Used: ix_documents_user_id                               │    │
│  │  Cost: O(log n)                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  4. Chunk Count by Document                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  SELECT document_id, COUNT(*) AS chunk_count                    │    │
│  │  FROM document_chunks                                           │    │
│  │  WHERE user_id = $user_id                                      │    │
│  │  GROUP BY document_id;                                          │    │
│  │                                                                 │    │
│  │  Index Used: ix_document_chunks_user_id                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  5. Hybrid Search (Vector + Lexical)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  -- Step 1: Vector search                                       │    │
│  │  SELECT id, embedding <=> $vec AS vec_rank                     │    │
│  │  FROM document_chunks WHERE user_id = $uid                     │    │
│  │  ORDER BY vec_rank LIMIT $n;                                    │    │
│  │                                                                 │    │
│  │  -- Step 2: Lexical search                                      │    │
│  │  SELECT id, ts_rank(search_vector, $tsq) AS fts_rank           │    │
│  │  FROM document_chunks WHERE user_id = $uid                     │    │
│  │    AND search_vector @@ $tsq                                    │    │
│  │  ORDER BY fts_rank LIMIT $n;                                    │    │
│  │                                                                 │    │
│  │  -- Step 3: RRF Fusion                                          │    │
│  │  RRF(d) = SUM(1 / (k + rank(d)))  where k = 60                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Volume Estimates

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DATA VOLUME ESTIMATES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Per Document (typical 20-page PDF):                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  documents row          │  ~1 KB                                │    │
│  │  document_chunks rows   │  ~40-60 rows (500 chars each)        │    │
│  │  Embeddings per chunk   │  768 × 4 bytes = 3,072 bytes         │    │
│  │  Total embeddings       │  ~120-180 KB per document             │    │
│  │  Total content          │  ~20-30 KB per document               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  At Scale (10,000 documents):                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  documents rows        │  10,000                               │    │
│  │  document_chunks rows  │  400,000 - 600,000                    │    │
│  │  Total embeddings      │  ~1.2 - 1.8 GB                        │    │
│  │  Total content         │  ~200 - 300 MB                         │    │
│  │  HNSW index            │  ~2 - 3 GB                             │    │
│  │  GIN index             │  ~500 MB - 1 GB                        │    │
│  │  Total database size   │  ~4 - 6 GB                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Index Sizes (estimated):                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  HNSW (embedding)   │  ~1.5 - 2x embedding data size           │    │
│  │  GIN (search_vector)│  ~0.3 - 0.5x content data size           │    │
│  │  B-tree (various)   │  ~0.1 - 0.2x column data size            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Database Configuration

### 10.1 Connection Settings

```
┌─────────────────────────────────────────────────────────────────────┐
│                  DATABASE CONFIGURATION                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Environment Variable: DATABASE_URL                                 │
│  Format: postgresql+psycopg://user:password@host:port/database      │
│                                                                     │
│  Default (Development):                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  postgresql+psycopg://docsense:adminadmin@localhost:5432/   │    │
│  │  docsense_db                                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Docker Compose:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  postgresql+psycopg://docsense:adminadmin@db:5432/docsense_db│   │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Test (SQLite):                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  sqlite:///test.db (or :memory: for in-memory)               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Next: [05-api-specification.md](./05-api-specification.md) — REST API reference*
