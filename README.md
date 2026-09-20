# 📄 DocSense

<p align="center">
  <strong>Enterprise Hybrid Search & Verified Document Q&A Platform</strong><br>
  <em>Powered by pgvector dense retrieval, full-text search, and cross-encoder reranking.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React%2019-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React 19" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="pgvector" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/Clerk%20Auth-6C47FF?style=for-the-badge&logo=clerk&logoColor=white" alt="Clerk" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</p>

---

## 🌟 Overview

**DocSense** is a production-grade, multi-tenant enterprise search and verified document Q&A platform designed for strictly source-grounded answers with zero hallucinations. Built to enterprise engineering standards, it pairs dense vector similarity search with lexical full-text indexing, reciprocal rank fusion (RRF), cross-encoder neural reranking, and citation attribution down to exact document passages.

---

## ⚡ Key Architectural Features

- **🚀 Hybrid Retrieval (Dense + Sparse)**: Combines semantic vector similarity search via `pgvector` (HNSW cosine indexing) with PostgreSQL full-text search (`tsvector` & `ts_rank` via GIN indexes), fused using **Reciprocal Rank Fusion (RRF, k=60)**.
- **🎯 Cross-Encoder Reranking**: High-precision neural re-scoring of candidate passages using `ms-marco-MiniLM-L-6-v2` to prioritize the most relevant evidence chunks.
- **🛡️ Strict Grounding & Guardrails**: Enforced LLM system boundary that abstains with an honest explanation when documents lack sufficient evidence, preventing hallucinated citations.
- **⚡ Asynchronous Ingestion & OCR**: Non-blocking document pipeline using FastAPI background tasks with automatic OCR fallback (`pytesseract`, `pdf2image`, `pdfplumber`) for scanned PDFs and tabular files (`.pdf`, `.docx`, `.xlsx`, `.csv`, `.json`).
- **📦 Unified Supabase & Object Storage**: Native integration with Supabase PostgreSQL (pgvector) and Supabase Storage (`documents` bucket) for scalable, secure document persistence.
- **🔐 Multi-Tenant Security & Clerk Auth**: Clerk JWT authentication with JWS key validation, automatic database user provisioning, and row-level tenant data isolation.
- **📊 Real Usage Metering**: Dynamic database tracking of queries, chunks, storage, and demo quotas with real-time UI synchronization.
- **🎨 Modern Interactive UI**: Built with React 19, Tailwind CSS, Lucide icons, collapsible source drawers with interactive citation links, and streaming responses.

---

## 🏗️ Architecture & Pipeline Flow

```mermaid
flowchart TD
    subgraph Ingestion["📥 Document Ingestion Pipeline"]
        A["Document Upload (PDF/DOCX/CSV/XLSX/JSON)"] --> B["Supabase Storage Bucket"]
        B --> C["FastAPI Background Task"]
        C --> D{"Native Text Extracted?"}
        D -->|"Yes"| E["Token Chunking & Metadata Extraction"]
        D -->|"No (Scanned)"| F["OCR Pipeline (Tesseract)"]
        F --> E
        E --> G["Dense Embeddings (768-dim)"]
        E --> H["Sparse Search Vector (tsvector)"]
        G --> I[("Supabase PostgreSQL + pgvector (HNSW)")]
        H --> I
    end

    subgraph RAG["🔍 Retrieval & Verified Answering"]
        Q["User Query"] --> QA["Query Analysis & Intent Expansion"]
        QA --> VR["Dense Vector Retrieval (Cosine Distance <=>)"]
        QA --> LR["Sparse Lexical Retrieval (FTS ts_rank)"]
        VR --> RRF["Reciprocal Rank Fusion (RRF)"]
        LR --> RRF
        RRF --> RERANK["Cross-Encoder Neural Reranking"]
        RERANK --> PROMPT["Strict Grounding Prompt + Evidence Assembly"]
        PROMPT --> LLM["LLM Generation (Groq / Gemini)"]
        LLM --> VERIFY{"Evidence Grounded?"}
        VERIFY -->|"Yes"| OUT["Grounded Answer + Collapsible Citations"]
        VERIFY -->|"No / Insufficient"| ABSTAIN["Honest Abstention Notice"]
    end
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (ORM), Alembic, Pydantic v2, Psycopg 3 |
| **Database & Vector** | Supabase PostgreSQL 17 / Local PostgreSQL, `pgvector` (HNSW Cosine index), FTS (`tsvector` + GIN index) |
| **Object Storage** | Supabase Storage (`documents` bucket) / Cloudinary fallback |
| **AI & NLP** | Groq (`gpt-oss-120b` / `llama-3.3-70b`), Hugging Face Inference API / `sentence-transformers` (768-dim) |
| **Ingestion & OCR** | PyPDF, pdfplumber, pdf2image, pytesseract, python-docx, openpyxl |
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS, Lucide React, React Markdown |
| **Auth & Identity** | Clerk Authentication (JWT verification via JWKS) |
| **DevOps & Hosting** | Docker, Docker Compose, Render, Supabase Cloud |

---

## 🚀 Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone https://github.com/iahmedd-k/DocSense.git
cd DocSense
```

### 2. Environment Configuration

Create `backend/.env`:
```env
# Database (Local Postgres via docker-compose or Supabase Pooler)
DATABASE_URL=postgresql+psycopg://postgres.rtobhqokqxjxuwscoley:j25X93hc7ZXJKkOh@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require

# Supabase Storage & Database
SUPABASE_URL=https://rtobhqokqxjxuwscoley.supabase.co
SUPABASE_SECRET_KEY=your_supabase_secret_key
SUPABASE_BUCKET=documents

# LLM & Embeddings
GROQ_API_KEY=your_groq_api_key
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
EMBEDDING_DIMENSION=768

# Auth
JWT_SECRET_KEY=change-me-in-production
```

Create `Frontend/.env.local`:
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### 3. Run Locally
```bash
# Run backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Run frontend (in separate terminal)
cd ../Frontend
npm install
npm run dev
```

Application URLs:
- **Frontend**: `http://localhost:3000`
- **FastAPI Documentation (Swagger)**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 🌐 Deploying to Render & Cloud

### Backend on Render (Web Service)
1. Create a new **Web Service** on [Render](https://render.com) connected to your GitHub repository.
2. Set **Root Directory**: `backend`
3. Set **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
4. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configure Environment Variables:
   - `DATABASE_URL`: Supabase Session Pooler URL (`postgresql+psycopg://...:5432/postgres?sslmode=require`)
   - `SUPABASE_URL`: Your Supabase Project URL
   - `SUPABASE_SECRET_KEY`: Your Supabase Service Role / Secret Key
   - `SUPABASE_BUCKET`: `documents`
   - `GROQ_API_KEY`: Your Groq API key
   - `HF_TOKEN`: Your Hugging Face token

### Frontend on Render / Vercel (Static Site)
1. Deploy `Frontend` directory as a Static Site.
2. Set **Build Command**: `npm run build`
3. Set **Publish Directory**: `dist`
4. Set Environment Variables:
   - `VITE_CLERK_PUBLISHABLE_KEY`: `pk_test_...`

---

## 📡 API Reference Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents` | Upload and asynchronously chunk, OCR, embed, and index a document |
| `GET` | `/api/v1/documents` | List user documents with real-time indexing status |
| `GET` | `/api/v1/documents/{id}/status` | Poll document processing progress |
| `DELETE`| `/api/v1/documents/{id}` | Remove document, chunks, and storage records |
| `POST` | `/api/v1/chat` | Execute hybrid search, cross-encoder reranking, and verified answer generation |
| `GET` | `/api/v1/conversations` | List conversation threads |
| `GET` | `/api/v1/usage` | Return live user metrics (queries used, chunks, storage, quota) |

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
