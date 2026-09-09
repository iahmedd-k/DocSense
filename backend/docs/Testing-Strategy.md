# DocSense — Testing Strategy

> **Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Classification:** Internal — Engineering

---

## 1. Testing Overview

DocSense employs a comprehensive testing strategy with **117+ test cases** across **14 test files**, covering unit tests, integration tests, and service-level tests. The test suite uses **pytest** with **httpx** for HTTP client testing and **SQLite in-memory** database for isolated test execution.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TESTING PYRAMID                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                              ▲                                           │
│                             ╱ ╲                                          │
│                            ╱   ╲         E2E Tests                      │
│                           ╱  0  ╲        (Not implemented)             │
│                          ╱───────╲                                      │
│                         ╱         ╲                                     │
│                        ╱   25+     ╲    Integration Tests               │
│                       ╱  Endpoint   ╲   (API + DB)                      │
│                      ╱───────────────╲                                  │
│                     ╱                 ╲                                 │
│                    ╱      90+          ╲  Unit Tests                    │
│                   ╱   Service/Repo      ╲ (Services, Repos, Models)    │
│                  ╱───────────────────────╲                              │
│                                                                         │
│  Total: 117+ test cases across 14 test files                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Test Architecture

### 2.1 Test Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TEST INFRASTRUCTURE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Test Framework: pytest 8.3.4                                    │    │
│  │  HTTP Client: httpx 0.28.1                                      │    │
│  │  Test Database: SQLite (in-memory / file-based)                 │    │
│  │  Mocking: unittest.mock (for external API calls)                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  conftest.py — Test Configuration                                │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  • SQLite test engine (replaces PostgreSQL)               │  │    │
│  │  │  • Session-scoped database setup/teardown                 │  │    │
│  │  │  • TestClient fixture (FastAPI TestClient)                │  │    │
│  │  │  • Database session override (get_db → test session)      │  │    │
│  │  │  • Table creation/drop per test (isolation)               │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Test Configuration Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TEST CONFIGURATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. conftest.py                                                 │    │
│  │     │                                                            │    │
│  │     ▼                                                            │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  Create SQLite test engine                                │  │    │
│  │  │  engine = create_engine("sqlite:///test.db")              │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │     │                                                            │    │
│  │     ▼                                                            │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  Create all tables (Base.metadata.create_all)             │  │    │
│  │  │  Override get_db dependency to use test session           │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │     │                                                            │    │
│  │     ▼                                                            │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  Create FastAPI TestClient with overridden dependencies   │  │    │
│  │  │  client = TestClient(app)                                 │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │     │                                                            │    │
│  │     ▼                                                            │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  Per-test: Insert test data, run assertions, drop tables  │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Test File Inventory

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TEST FILE INVENTORY                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  tests/                                                         │    │
│  │  ├── conftest.py           │ Test configuration & fixtures      │    │
│  │  │                                                         │    │
│  │  ├── Unit Tests (Service Layer)                                │    │
│  │  │   ├── test_chunking.py              │ 17 tests              │    │
│  │  │   ├── test_embedding.py             │ 11 tests              │    │
│  │  │   ├── test_pdf_parser.py            │ 5 tests               │    │
│  │  │   ├── test_retrieval_service.py     │ 12 tests              │    │
│  │  │   ├── test_rrf_service.py           │ 11 tests              │    │
│  │  │   ├── test_reranking_service.py     │ 10 tests              │    │
│  │  │   ├── test_evidence_grader_service.py │ 6 tests             │    │
│  │  │   ├── test_query_refinement_service.py │ 5 tests            │    │
│  │  │   └── test_corrective_retrieval_service.py │ 6 tests        │    │
│  │  │                                                         │    │
│  │  ├── Repository Tests                                           │    │
│  │  │   ├── test_retrieval_repository.py  │ 6 tests               │    │
│  │  │   └── test_document_chunk_repository.py │ 7 tests           │    │
│  │  │                                                         │    │
│  │  └── Integration Tests (Endpoint Layer)                         │    │
│  │      ├── test_auth.py                   │ 7 tests               │    │
│  │      ├── test_documents.py              │ 18 tests              │    │
│  │      └── test_retrieval_endpoint.py     │ 7 tests               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Total: 14 test files, 117+ test cases                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Unit Tests — Service Layer

### 4.1 Chunking Service Tests (`test_chunking.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CHUNKING SERVICE TESTS (17 tests)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Test Categories:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Text Chunking                                                  │    │
│  │  ├── test_chunk_text_normal_paragraphs                         │    │
│  │  ├── test_chunk_text_with_headings                             │    │
│  │  ├── test_chunk_text_with_lists                                │    │
│  │  └── test_chunk_text_with_tables                               │    │
│  │                                                                 │    │
│  │  Structure Detection                                            │    │
│  │  ├── test_detect_heading_type                                  │    │
│  │  ├── test_detect_list_type                                     │    │
│  │  ├── test_detect_table_type                                    │    │
│  │  └── test_detect_text_type                                     │    │
│  │                                                                 │    │
│  │  Chunk Splitting                                                │    │
│  │  ├── test_split_long_chunks                                    │    │
│  │  ├── test_chunk_overlap                                        │    │
│  │  ├── test_table_header_repetition                              │    │
│  │  └── test_list_grouping                                        │    │
│  │                                                                 │    │
│  │  Edge Cases                                                     │    │
│  │  ├── test_empty_content                                        │    │
│  │  ├── test_single_line_content                                  │    │
│  │  ├── test_large_document                                       │    │
│  │  ├── test_mixed_content_types                                  │    │
│  │  └── test_chunk_size_boundary                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Content type detection (heading, list, table, text)                 │
│  • Chunk size limits (500 chars default)                               │
│  • Chunk overlap (50 chars default)                                    │
│  • Table header repetition in sub-chunks                              │
│  • List item grouping                                                  │
│  • Edge cases (empty, large, mixed content)                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Embedding Service Tests (`test_embedding.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EMBEDDING SERVICE TESTS (11 tests)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Test Categories:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Provider Abstraction                                           │    │
│  │  ├── test_provider_initialization                              │    │
│  │  ├── test_provider_returns_embeddings                          │    │
│  │  └── test_provider_dimension_consistency                       │    │
│  │                                                                 │    │
│  │  HuggingFace Provider                                           │    │
│  │  ├── test_hf_provider_single_text                              │    │
│  │  ├── test_hf_provider_batch_texts                              │    │
│  │  ├── test_hf_provider_api_error_handling                       │    │
│  │  ├── test_hf_provider_response_format_openai                   │    │
│  │  └── test_hf_provider_response_format_bare                     │    │
│  │                                                                 │    │
│  │  Integration                                                    │    │
│  │  ├── test_embedding_service_integration                        │    │
│  │  ├── test_embedding_service_lazy_initialization                │    │
│  │  └── test_embedding_service_dimension_config                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Provider pattern (abstract base → concrete)                         │
│  • HuggingFace API response parsing                                    │
│  • 768-dimension vector output                                        │
│  • Error handling for API failures                                     │
│  • Lazy provider initialization                                        │
│  • Batch vs single text embedding                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 PDF Parser Tests (`test_pdf_parser.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PDF PARSER TESTS (5 tests)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_parse_single_page_pdf                                │    │
│  │  ├── test_parse_multi_page_pdf                                 │    │
│  │  ├── test_parse_pdf_page_numbers                               │    │
│  │  ├── test_parse_pdf_empty_pages                                │    │
│  │  └── test_parse_pdf_text_extraction                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Page-by-page text extraction                                        │
│  • Page number preservation                                            │
│  • Empty page handling                                                 │
│  • Text content accuracy                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Retrieval Service Tests (`test_retrieval_service.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  RETRIEVAL SERVICE TESTS (12 tests)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Test Categories:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Vector Retrieval                                               │    │
│  │  ├── test_vector_search_returns_results                        │    │
│  │  ├── test_vector_search_respects_top_k                         │    │
│  │  └── test_vector_search_scoped_by_user                         │    │
│  │                                                                 │    │
│  │  Lexical Retrieval                                              │    │
│  │  ├── test_lexical_search_returns_results                       │    │
│  │  ├── test_lexical_search_ranking                               │    │
│  │  └── test_lexical_search_empty_query                           │    │
│  │                                                                 │    │
│  │  Hybrid Retrieval                                               │    │
│  │  ├── test_hybrid_search_fusion                                 │    │
│  │  ├── test_hybrid_search_deduplication                          │    │
│  │  └── test_hybrid_search_respects_top_k                         │    │
│  │                                                                 │    │
│  │  Reranking                                                     │    │
│  │  ├── test_rerank_flag_enables_reranking                        │    │
│  │  ├── test_rerank_fetches_extra_candidates                      │    │
│  │  └── test_rerank_caps_max_results                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.5 RRF Service Tests (`test_rrf_service.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RRF SERVICE TESTS (11 tests)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_rrf_single_list                                     │    │
│  │  ├── test_rrf_fusion_two_lists                                 │    │
│  │  ├── test_rrf_deduplication                                    │    │
│  │  ├── test_rrf_ranking_order                                    │    │
│  │  ├── test_rrf_k_constant                                       │    │
│  │  ├── test_rrf_custom_k_value                                   │    │
│  │  ├── test_rrf_empty_lists                                      │    │
│  │  ├── test_rrf_one_empty_list                                   │    │
│  │  ├── test_rrf_overlapping_results                              │    │
│  │  ├── test_rrf_score_calculation                                │    │
│  │  └── test_rrf_preserves_chunk_ids                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • RRF formula: RRF(d) = Σ(1 / (k + rank(d)))                        │
│  • Deduplication by chunk_id                                           │
│  • Ranking order (descending RRF score)                                │
│  • Configurable k constant (default 60)                               │
│  • Edge cases (empty lists, single list, overlaps)                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.6 Reranking Service Tests (`test_reranking_service.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  RERANKING SERVICE TESTS (10 tests)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_cross_encoder_scoring                                │    │
│  │  ├── test_rerank_returns_top_n                                 │    │
│  │  ├── test_rerank_sorted_by_score                               │    │
│  │  ├── test_rerank_preserves_metadata                            │    │
│  │  ├── test_rerank_empty_input                                   │    │
│  │  ├── test_rerank_single_item                                   │    │
│  │  ├── test_rerank_batch_scoring                                 │    │
│  │  ├── test_cross_encoder_lazy_loading                           │    │
│  │  ├── test_cross_encoder_singleton                              │    │
│  │  └── test_rerank_max_results_cap                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Cross-encoder scoring (sigmoid of logits)                           │
│  • Top-N selection                                                      │
│  • Score-based sorting                                                 │
│  • Lazy model loading                                                  │
│  • Singleton pattern                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.7 Evidence Grader Tests (`test_evidence_grader_service.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                EVIDENCE GRADER SERVICE TESTS (6 tests)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_grade_sufficient_evidence                            │    │
│  │  ├── test_grade_insufficient_evidence                          │    │
│  │  ├── test_grade_returns_confidence_score                       │    │
│  │  ├── test_grade_returns_missing_information                    │    │
│  │  ├── test_grade_malformed_llm_output                           │    │
│  │  └── test_grade_empty_evidence                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Evidence sufficiency verdict                                        │
│  • Confidence score generation                                         │
│  • Missing information identification                                  │
│  • Malformed LLM response handling                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.8 Query Refinement Tests (`test_query_refinement_service.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│               QUERY REFINEMENT SERVICE TESTS (5 tests)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_refine_query_generates_new_query                     │    │
│  │  ├── test_refine_query_includes_missing_info                   │    │
│  │  ├── test_refine_query_skips_when_sufficient                   │    │
│  │  ├── test_refine_query_handles_llm_error                       │    │
│  │  └── test_refine_query_preserves_context                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Corrective query generation                                         │
│  • Missing information integration                                     │
│  • Skip when evidence is sufficient                                    │
│  • Error handling                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.9 Corrective Retrieval Tests (`test_corrective_retrieval_service.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│             CORRECTIVE RETRIEVAL SERVICE TESTS (6 tests)                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_corrective_loop_sufficient_first_try                 │    │
│  │  ├── test_corrective_loop_refines_query                        │    │
│  │  ├── test_corrective_loop_max_attempts                         │    │
│  │  ├── test_corrective_loop_stall_detection                      │    │
│  │  ├── test_corrective_loop_preserves_provenance                 │    │
│  │  └── test_corrective_loop_returns_final_results                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Bounded loop (max 2 attempts)                                      │
│  • Stall detection (same query twice)                                 │
│  • Provenance preservation                                            │
│  • Final result aggregation                                           │
│                                                                         │
│  Loop Flow Tested:                                                     │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │  Attempt 1: Retrieve → Grade → Sufficient? → Return          │      │
│  │  Attempt 1: Retrieve → Grade → Insufficient → Refine         │      │
│  │  Attempt 2: Retrieve → Grade → Sufficient? → Return          │      │
│  │  Attempt 2: Retrieve → Grade → Insufficient → Max Reached    │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Repository Tests

### 5.1 Retrieval Repository Tests (`test_retrieval_repository.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 RETRIEVAL REPOSITORY TESTS (6 tests)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_vector_search_sql_generation                         │    │
│  │  ├── test_lexical_search_sql_generation                        │    │
│  │  ├── test_hybrid_search_sql_generation                         │    │
│  │  ├── test_user_scope_sql_generation                            │    │
│  │  ├── test_top_k_limit_sql_generation                           │    │
│  │  └── test_order_by_clause_sql_generation                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • SQL query generation for vector search                             │
│  • SQL query generation for lexical search                            │
│  • User scope enforcement in queries                                   │
│  • top_k parameter handling                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Document Chunk Repository Tests (`test_document_chunk_repository.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│              DOCUMENT CHUNK REPOSITORY TESTS (7 tests)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_create_chunk                                         │    │
│  │  ├── test_get_chunks_by_document                               │    │
│  │  ├── test_get_chunks_by_user                                   │    │
│  │  ├── test_delete_chunks_by_document                            │    │
│  │  ├── test_chunk_embedding_storage                              │    │
│  │  ├── test_chunk_metadata_jsonb                                 │    │
│  │  └── test_chunk_content_type                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • CRUD operations for chunks                                          │
│  • Embedding vector storage (pgvector)                                 │
│  • JSONB metadata storage                                              │
│  • Content type enum handling                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Integration Tests — Endpoint Layer

### 6.1 Auth Endpoint Tests (`test_auth.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTH ENDPOINT TESTS (7 tests)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_register_success                                     │    │
│  │  ├── test_register_duplicate_email                             │    │
│  │  ├── test_login_success                                        │    │
│  │  ├── test_login_invalid_credentials                            │    │
│  │  ├── test_get_me_authenticated                                 │    │
│  │  ├── test_get_me_unauthenticated                               │    │
│  │  └── test_logout_returns_204                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Full registration flow (register → JWT returned)                    │
│  • Duplicate email detection                                          │
│  • Login flow (credentials → JWT)                                     │
│  • Invalid credentials handling                                        │
│  • Authenticated profile retrieval                                     │
│  • Unauthenticated access rejection                                    │
│  • Stateless logout behavior                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Document Endpoint Tests (`test_documents.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  DOCUMENT ENDPOINT TESTS (18 tests)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Test Categories:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Upload                                                         │    │
│  │  ├── test_upload_pdf_success                                   │    │
│  │  ├── test_upload_invalid_file_type                             │    │
│  │  ├── test_upload_file_too_large                                │    │
│  │  ├── test_upload_unauthenticated                               │    │
│  │  └── test_upload_creates_chunks                                │    │
│  │                                                                 │    │
│  │  Listing                                                        │    │
│  │  ├── test_list_documents_success                               │    │
│  │  ├── test_list_documents_empty                                 │    │
│  │  ├── test_list_documents_ownership_isolation                   │    │
│  │  └── test_list_documents_sorted_by_date                        │    │
│  │                                                                 │    │
│  │  Retrieval                                                      │    │
│  │  ├── test_get_document_success                                 │    │
│  │  ├── test_get_document_not_found                               │    │
│  │  └── test_get_document_ownership_isolation                     │    │
│  │                                                                 │    │
│  │  Status                                                         │    │
│  │  ├── test_get_document_status                                  │    │
│  │  └── test_get_document_status_transitions                      │    │
│  │                                                                 │    │
│  │  Deletion                                                       │    │
│  │  ├── test_delete_document_success                              │    │
│  │  ├── test_delete_document_not_found                            │    │
│  │  ├── test_delete_document_ownership_isolation                  │    │
│  │  └── test_delete_document_cascades_chunks                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • Full upload pipeline (PDF → chunks)                                 │
│  • File validation (type, size)                                        │
│  • Ownership isolation (users can't see others' docs)                 │
│  • Cascade deletion (doc + chunks)                                    │
│  • Status transitions                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Search Endpoint Tests (`test_retrieval_endpoint.py`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                SEARCH ENDPOINT TESTS (7 tests)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ├── test_search_vector_mode                                   │    │
│  │  ├── test_search_lexical_mode                                  │    │
│  │  ├── test_search_hybrid_mode                                   │    │
│  │  ├── test_search_default_top_k                                 │    │
│  │  ├── test_search_custom_top_k                                  │    │
│  │  ├── test_search_rerank_flag                                   │    │
│  │  └── test_search_ownership_isolation                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  What's Tested:                                                         │
│  • All three search modes (vector, lexical, hybrid)                    │
│  • top_k parameter behavior                                           │
│  • Reranking flag                                                      │
│  • Ownership isolation in search results                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Test Fixtures & Mocks

### 7.1 Fake Providers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FAKE PROVIDERS                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Purpose: Avoid external API calls during testing                      │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FakeEmbeddingProvider                                          │    │
│  │  • Returns deterministic 768-dimensional vectors                │    │
│  │  • No API calls                                                 │    │
│  │  • Configurable return values                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FakeChatProvider                                               │    │
│  │  • Returns mock LLM responses                                  │    │
│  │  • No API calls                                                 │    │
│  │  • Configurable JSON/text responses                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FakeCrossEncoderProvider                                       │    │
│  │  • Returns mock reranking scores                               │    │
│  │  • No model loading                                             │    │
│  │  • Configurable score outputs                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Test Database Setup

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TEST DATABASE SETUP                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  SQLite In-Memory Database                                      │    │
│  │                                                                 │    │
│  │  • Replaces PostgreSQL in tests                                │    │
│  │  • Fast setup/teardown                                         │    │
│  │  • Isolated per test session                                   │    │
│  │  • No pgvector extension (graceful degradation)                │    │
│  │  • No TSVECTOR generation (nullable column)                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Session Override:                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  # conftest.py                                                  │    │
│  │  def override_get_db():                                         │    │
│  │      try:                                                       │    │
│  │          yield db_session                                        │    │
│  │      finally:                                                   │    │
│  │          db_session.close()                                      │    │
│  │                                                                  │    │
│  │  app.dependency_overrides[get_db] = override_get_db             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Running Tests

### 8.1 Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_register_success

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests matching pattern
pytest -k "upload"

# Run tests with print output
pytest -s
```

### 8.2 Test Output Format

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TEST OUTPUT EXAMPLE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  tests/test_auth.py::test_register_success PASSED                      │
│  tests/test_auth.py::test_register_duplicate_email PASSED              │
│  tests/test_auth.py::test_login_success PASSED                         │
│  tests/test_auth.py::test_login_invalid_credentials PASSED             │
│  tests/test_auth.py::test_get_me_authenticated PASSED                  │
│  tests/test_auth.py::test_get_me_unauthenticated PASSED                │
│  tests/test_auth.py::test_logout_returns_204 PASSED                    │
│  tests/test_documents.py::test_upload_pdf_success PASSED               │
│  tests/test_documents.py::test_upload_invalid_file_type PASSED         │
│  ...                                                                   │
│                                                                         │
│  ========================= 117 passed in 12.34s ========================│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Test Coverage Goals

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TEST COVERAGE GOALS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Layer              │  Current Coverage  │  Target              │    │
│  ├─────────────────────┼────────────────────┼──────────────────────┤    │
│  │  Services           │  ~90%              │  95%                 │    │
│  │  Repositories       │  ~85%              │  90%                 │    │
│  │  API Endpoints      │  ~80%              │  85%                 │    │
│  │  Core (Config/Auth) │  ~75%              │  85%                 │    │
│  │  Overall            │  ~82%              │  90%                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Coverage Report Command:                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  pytest --cov=app --cov-report=html --cov-report=term-missing   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Testing Best Practices

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TESTING BEST PRACTICES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Test Isolation                                                      │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • Each test gets a clean database state                    │    │
│     │  • Tables created/dropped per test session                  │    │
│     │  • No shared state between tests                            │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  2. External Service Mocking                                           │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • All external APIs mocked in unit tests                   │    │
│     │  • Fake providers for embeddings, LLM, reranking           │    │
│     │  • No network calls in unit tests                           │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  3. Test Naming Convention                                             │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • test_<action>_<scenario>_<expected_result>               │    │
│     │  • Examples:                                                 │    │
│     │    - test_register_success                                  │    │
│     │    - test_register_duplicate_email                          │    │
│     │    - test_upload_invalid_file_type                          │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  4. Assertion Style                                                    │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • Use pytest assert statements                             │    │
│     │  • Check HTTP status codes                                  │    │
│     │  • Validate response body structure                         │    │
│     │  • Verify database state changes                            │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  5. Fixture Organization                                               │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • conftest.py for shared fixtures                          │    │
│     │  • Test-specific fixtures in test files                     │    │
│     │  • Clear fixture dependency chain                           │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Next: [07-deployment-guide.md](./07-deployment-guide.md) — Deployment procedures*
