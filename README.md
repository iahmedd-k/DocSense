# 📄 DocSense

<p align="center">
  <strong>Production-Grade Hybrid Search & Verified RAG Document Q&A Platform</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React%2019-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React 19" />
  <img src="https://img.shields.io/badge/PostgreSQL%2016-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="pgvector" />
  <img src="https://img.shields.io/badge/Clerk%20Auth-6C47FF?style=for-the-badge&logo=clerk&logoColor=white" alt="Clerk" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</p>

---

## 🌟 Overview

**DocSense** is an end-to-end, multi-tenant Retrieval-Augmented Generation (RAG) platform designed for accurate, document-grounded question answering with zero hallucinations. Built with an enterprise-grade architectural standard, it combines dense vector search, lexical full-text indexing, reciprocal rank fusion (RRF), cross-encoder reranking, and strict citation attribution.

---

## ⚡ Key Architectural Features

- **🚀 Hybrid Retrieval (Dense + Sparse)**: Combines semantic vector similarity search via `pgvector` with PostgreSQL full-text search (`tsvector` & `ts_rank`), fused using **Reciprocal Rank Fusion (RRF)** for optimal recall.
- **🎯 Cross-Encoder Reranking**: Fine-grained neural re-scoring of candidate chunks to prioritize the most relevant evidence spans.
- **🛡️ Strict Grounding & Guardrails**: Enforced LLM system boundary that abstains on out-of-scope questions and prevents fabricated citations.
- **⚡ Asynchronous Ingestion & OCR**: Non-blocking document processing using FastAPI background tasks with fallback OCR support (`pytesseract`, `pdf2image`, `pdfplumber`) for scanned PDFs.
- **🔐 Multi-Tenant Security & Clerk Auth**: Clerk JWT authentication with JWS key validation, automatic database user provisioning, and strict row-level tenant isolation.
- **📊 Real Usage Metering**: Dynamic database tracking of queries, chunks, storage, and showcase quotas.
- **🎨 Modern Interactive UI**: Built with React 19, Tailwind CSS, Lucide icons, dynamic streaming simulation, and collapsible source drawers with interactive citation links.

---

## 🏗️ Architecture & Pipeline Flow

```mermaid
flowchart TD
    subgraph Ingestion["📥 Document Ingestion Pipeline"]
        A["Document Upload (PDF/DOCX/TXT)"] --> B["FastAPI Background Task"]
        B --> C{"Native Text Extracted?"}
        C -->|"Yes"| D["Chunking & Tokenizer"]
        C -->|"No (Scanned)"| E["OCR Pipeline (Tesseract)"]
        E --> D
        D --> F["Dense Embeddings (768-dim)"]
        D --> G["Sparse Search Vector (tsvector)"]
        F --> H[("PostgreSQL + pgvector")]
        G --> H
    end

    subgraph RAG["🔍 Retrieval & Answering Pipeline"]
        Q["User Query"] --> RA["Query Analysis & Intent Expansion"]
        RA --> VR["Vector Retrieval (Cosine Distance)"]
        RA --> LR["Lexical Retrieval (FTS ts_rank)"]
        VR --> RRF["Reciprocal Rank Fusion (RRF)"]
        LR --> RRF
        RRF --> RERANK["Cross-Encoder Reranking"]
        RERANK --> PROMPT["Strict Grounding Prompt"]
        PROMPT --> LLM["LLM Generation (Gemini / Claude / OpenAI)"]
        LLM --> VERIFY{"Evidence Grounded?"}
        VERIFY -->|"Yes"| OUT["Grounded Answer + Collapsible Citations"]
        VERIFY -->|"No / Out of Scope"| ABSTAIN["Honest Abstention Notice"]
    end
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (ORM), Alembic, Pydantic v2 |
| **Database & Vector** | PostgreSQL 16, pgvector extension, Full-Text Search (GIN indexes) |
| **AI & NLP** | Google Gemini API / HuggingFace Transformers, sentence-transformers, PyTorch |
| **Ingestion & OCR** | PyPDF, pdfplumber, pdf2image, pytesseract, Cloudinary |
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS, Lucide React, React Markdown |
| **Auth & Identity** | Clerk Authentication (JWT verification via JWKS) |
| **DevOps & Containers** | Docker, Docker Compose, Uvicorn |

---

## 🚀 Quick Start

### 1. Prerequisites
- [Docker & Docker Compose](https://www.docker.com/) installed
- Node.js 18+ and Python 3.12 (for local native development)

### 2. Clone the Repository
```bash
git clone https://github.com/iahmedd-k/DocSense.git
cd DocSense
```

### 3. Environment Configuration

Create a `.env` file in `backend/`:
```env
# Database
DATABASE_URL=postgresql+psycopg://docsense:docsense_dev_password@localhost:5432/docsense

# LLM & Embeddings
GEMINI_API_KEY=your_gemini_api_key
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Authentication (Clerk)
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

Create a `.env.local` file in `Frontend/`:
```env
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

### 4. Run with Docker Compose
```bash
# Start PostgreSQL (pgvector) and FastAPI backend
docker compose up -d --build

# Run frontend
cd Frontend
npm install
npm run dev
```

The application will be accessible at:
- **Frontend App**: `http://localhost:3000`
- **FastAPI Documentation (Swagger)**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 📡 API Reference Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents` | Upload and asynchronously index a document |
| `GET` | `/api/v1/documents` | List user documents and indexing statuses |
| `GET` | `/api/v1/documents/{id}/status` | Check real-time indexing status |
| `DELETE`| `/api/v1/documents/{id}` | Delete document, chunks, and storage records |
| `POST` | `/api/v1/chat/rag` | Execute end-to-end grounded RAG answering |
| `GET` | `/api/v1/search` | Direct hybrid search across indexed chunks |
| `GET` | `/api/v1/usage` | Return live user metrics and showcase quota stats |

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
