# DocSense — Deployment Guide

> **Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Classification:** Internal — Engineering

---

## 1. Deployment Overview

DocSense is containerized using **Docker** and orchestrated with **Docker Compose**. The deployment consists of two primary services: the FastAPI application (`api`) and the PostgreSQL database with pgvector (`db`).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DEPLOYMENT TOPOLOGY                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                      ┌─────────────────────┐                            │
│                      │    Client / User    │                            │
│                      │  (Web Browser)      │                            │
│                      └──────────┬──────────┘                            │
│                                 │                                       │
│                           HTTPS :443                     Production     │
│                                 │                                       │
│                      ┌──────────▼──────────┐                            │
│                      │   Reverse Proxy     │                            │
│                      │   (Nginx/Caddy)     │                            │
│                      └──────────┬──────────┘                            │
│                                 │                                       │
│                      ┌──────────▼──────────┐                            │
│                      │   FastAPI Backend   │                            │
│                      │   (Uvicorn :8000)   │                            │
│                      └──────────┬──────────┘                            │
│                                 │                                       │
│               ┌─────────────────┼─────────────────┐                     │
│               │                 │                 │                     │
│      ┌────────▼────────┐ ┌──────▼───────┐ ┌──────▼────────┐            │
│      │  PostgreSQL     │ │  Cloudinary  │ │ External APIs │            │
│      │  + pgvector     │ │  (Storage)   │ │ Groq / HF     │            │
│      │  (5432)         │ │              │ │ DDG           │            │
│      └─────────────────┘ └──────────────┘ └───────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### 2.1 Local Development

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Application runtime |
| PostgreSQL | 16 | Database (with pgvector) |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.x | Multi-container orchestration |
| Git | 2.x | Version control |

### 2.2 Cloud Services

| Service | Purpose | Requirement |
|---------|---------|-------------|
| Cloudinary | PDF file storage | Account + API credentials |
| HuggingFace | Vector embeddings | API token |
| Groq | LLM chat completion | API key |

---

## 3. Local Development Setup

### 3.1 Environment Configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ENVIRONMENT SETUP                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Clone the repository:                                               │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  git clone <repository-url>                                  │    │
│     │  cd docsense/backend                                         │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  2. Create .env file from template:                                    │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  cp .env.example .env                                        │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  3. Set required environment variables:                                │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  # Database                                                   │    │
│     │  DATABASE_URL=postgresql+psycopg://docsense:adminadmin@localhost:5432/docsense_db │
│     │                                                                 │    │
│     │  # JWT Security                                                │    │
│     │  JWT_SECRET_KEY=<generate-a-strong-secret>                     │    │
│     │  JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60                             │    │
│     │                                                                 │    │
│     │  # Cloudinary                                                  │    │
│     │  CLOUDINARY_CLOUD_NAME=<your-cloud-name>                        │    │
│     │  CLOUDINARY_API_KEY=<your-api-key>                              │    │
│     │  CLOUDINARY_API_SECRET=<your-api-secret>                        │    │
│     │                                                                 │    │
│     │  # AI Services                                                  │    │
│     │  HUGGINGFACE_TOKEN=<your-hf-token>                              │    │
│     │  GROQ_API_KEY=<your-groq-key>                                   │    │
│     │  GROQ_CHAT_MODEL=<your-model>                                   │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Virtual Environment Setup

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 VIRTUAL ENVIRONMENT SETUP                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Windows:                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  python -m venv venv                                           │    │
│  │  venv\Scripts\activate                                         │    │
│  │  pip install -r requirements.txt                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  macOS/Linux:                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  python3 -m venv venv                                          │    │
│  │  source venv/bin/activate                                      │    │
│  │  pip install -r requirements.txt                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Database Setup

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATABASE SETUP                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Option 1: Local PostgreSQL                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Install PostgreSQL 16 + pgvector extension                  │    │
│  │  2. Create database:                                            │    │
│  │     createdb docsense_db                                        │    │
│  │  3. Enable pgvector extension:                                  │    │
│  │     psql -d docsense_db -c "CREATE EXTENSION vector;"           │    │
│  │  4. Run migrations:                                             │    │
│  │     alembic upgrade head                                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Option 2: Docker PostgreSQL                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Start PostgreSQL container:                                 │    │
│  │     docker-compose up db                                        │    │
│  │  2. Run migrations:                                             │    │
│  │     alembic upgrade head                                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Run Application

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      RUN APPLICATION                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Development Server:                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  # With hot reload                                               │    │
│  │  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000        │    │
│  │                                                                  │    │
│  │  # Without hot reload                                            │    │
│  │  uvicorn app.main:app --host 0.0.0.0 --port 8000                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Verify:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Health Check:   http://localhost:8000/health                   │    │
│  │  API Docs:       http://localhost:8000/docs                     │    │
│  │  ReDoc:          http://localhost:8000/redoc                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Docker Deployment

### 4.1 Dockerfile Analysis

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DOCKERFILE EXPLANATION                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  FROM python:3.12-slim                                                 │
│  │                                                                      │
│  │  • Base image: Debian-based Python 3.12                             │
│  │  • Minimal footprint (slim variant)                                 │
│  │  • Includes pip and system dependencies                             │
│  ▼                                                                      │
│  WORKDIR /app                                                          │
│  │                                                                      │
│  │  • Working directory for all subsequent commands                    │
│  ▼                                                                      │
│  COPY requirements.txt .                                               │
│  │                                                                      │
│  │  • Copy requirements first for layer caching                        │
│  ▼                                                                      │
│  RUN pip install --no-cache-dir -r requirements.txt                    │
│  │                                                                      │
│  │  • Install Python dependencies                                      │
│  │  • --no-cache-dir reduces image size                                │
│  ▼                                                                      │
│  COPY . .                                                              │
│  │                                                                      │
│  │  • Copy application code (after deps for build cache)               │
│  ▼                                                                      │
│  EXPOSE 8000                                                           │
│  │                                                                      │
│  │  • Document container port                                          │
│  ▼                                                                      │
│  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]│
│                                                                          │
│  • Run uvicorn server on container start                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Docker Compose Configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE CONFIGURATION                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  services:                                                              │
│    api:                                                                 │
│      build: .                                                          │
│      ports:                                                             │
│        - "8000:8000"                                                    │
│      environment:                                                       │
│        - DATABASE_URL=postgresql+psycopg://docsense:adminadmin@db:5432/docsense_db │
│        - CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME}                │
│        - CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY}                      │
│        - CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET}                │
│        - HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}                        │
│        - GROQ_API_KEY=${GROQ_API_KEY}                                  │
│        - JWT_SECRET_KEY=${JWT_SECRET_KEY}                              │
│      depends_on:                                                        │
│        - db                                                             │
│                                                                         │
│    db:                                                                  │
│      image: pgvector/pgvector:pg16                                     │
│      environment:                                                       │
│        POSTGRES_USER: docsense                                          │
│        POSTGRES_PASSWORD: adminadmin                                    │
│        POSTGRES_DB: docsense_db                                         │
│      ports:                                                             │
│        - "5432:5432"                                                    │
│      volumes:                                                           │
│        - db_data:/var/lib/postgresql/data                               │
│      healthcheck:                                                       │
│        test: ["CMD-SHELL", "pg_isready -U docsense"]                   │
│        interval: 10s                                                    │
│        timeout: 5s                                                      │
│        retries: 5                                                       │
│                                                                         │
│  volumes:                                                               │
│    db_data:                                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Docker Deployment Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DOCKER DEPLOYMENT                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Build and start all services:                                       │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  docker-compose build                                        │    │
│     │  docker-compose up -d                                        │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  2. Verify services are running:                                        │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  docker-compose ps                                           │    │
│     │                                                              │    │
│     │  NAME              STATUS          PORTS                     │    │
│     │  backend-api-1     Up 2 minutes    0.0.0.0:8000->8000/tcp   │    │
│     │  backend-db-1      Up 2 minutes    0.0.0.0:5432->5432/tcp   │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  3. Run database migrations:                                            │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  docker-compose exec api alembic upgrade head                │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  4. Verify health:                                                      │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  curl http://localhost:8000/health                           │    │
│     │  # Response: {"status":"ok"}                                 │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  5. View logs:                                                          │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  docker-compose logs -f api                                  │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  6. Stop services:                                                      │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  docker-compose down                                         │    │
│     │  # Include -v to remove volumes: docker-compose down -v      │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Database Migrations

### 5.1 Migration Commands

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MIGRATION COMMANDS                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  # Apply all pending migrations                                 │    │
│  │  alembic upgrade head                                           │    │
│  │                                                                  │    │
│  │  # Apply one version                                            │    │
│  │  alembic upgrade +1                                             │    │
│  │                                                                  │    │
│  │  # Rollback one version                                         │    │
│  │  alembic downgrade -1                                           │    │
│  │                                                                  │    │
│  │  # Rollback to a specific version                               │    │
│  │  alembic downgrade 0005                                         │    │
│  │                                                                  │    │
│  │  # Show current version                                         │    │
│  │  alembic current                                                │    │
│  │                                                                  │    │
│  │  # Show migration history                                       │    │
│  │  alembic history                                                │    │
│  │                                                                  │    │
│  │  # Create a new migration (autogenerate)                        │    │
│  │  alembic revision --autogenerate -m "Description"               │    │
│  │                                                                  │    │
│  │  # Create an empty migration                                    │    │
│  │  alembic revision -m "Description"                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Migration Chain:                                                       │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐ │
│  │  0001   │──▶│  0002   │──▶│  0003   │──▶│  0004   │──▶│  0005   │ │
│  │  users  │   │documents│   │ status  │   │ filename│   │ chunks  │ │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └────┬────┘ │
│                                                                │       │
│                                                           ┌────▼────┐  │
│                                                           │  0006   │  │
│                                                           │ indexes │  │
│                                                           └─────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Production Deployment

### 6.1 Production Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  PRODUCTION ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Client Traffic                                                  │    │
│  │       │                                                          │    │
│  │       ▼                                                          │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │  Load Balancer (optional for HA)                         │    │    │
│  │  └─────────────────────────┬───────────────────────────────┘    │    │
│  │                            │                                     │    │
│  │  ┌─────────────────────────▼───────────────────────────────┐    │    │
│  │  │  Reverse Proxy (Nginx/Caddy)                             │    │    │
│  │  │  • TLS/SSL termination                                   │    │    │
│  │  │  • Rate limiting                                         │    │    │
│  │  │  • Request routing                                       │    │    │
│  │  └─────────────────────────┬───────────────────────────────┘    │    │
│  │                            │                                     │    │
│  │  ┌─────────────────────────▼───────────────────────────────┐    │    │
│  │  │  FastAPI Application (Docker)                            │    │    │
│  │  │  • Uvicorn workers (multiple)                            │    │    │
│  │  └─────────────────────────┬───────────────────────────────┘    │    │
│  │                            │                                     │    │
│  │  ┌─────────────────────────▼───────────────────────────────┐    │    │
│  │  │  PostgreSQL 16 + pgvector (Docker)                       │    │    │
│  │  │  • Persistent volume                                     │    │    │
│  │  │  • Daily backups                                         │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Production Checklist

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  PRODUCTION DEPLOYMENT CHECKLIST                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Security                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  [ ] Set ENVIRONMENT=production                                │    │
│  │  [ ] Use strong JWT_SECRET_KEY (256+ bit random)               │    │
│  │  [ ] Configure strict CORS_ORIGINS                             │    │
│  │  [ ] Rotate all API keys (Cloudinary, HF, Groq)                │    │
│  │  [ ] Never commit .env to version control                      │    │
│  │  [ ] Enable HTTPS/TLS (via reverse proxy)                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Performance                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  [ ] Run multiple uvicorn workers (4-8)                        │    │
│  │  [ ] Configure database connection pooling                     │    │
│  │  [ ] Tune pgvector HNSW parameters                             │    │
│  │  [ ] Add CDN caching for static assets                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Reliability                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  [ ] Configure database backups (daily)                         │    │
│  │  [ ] Set up health check monitoring                             │    │
│  │  [ ] Configure log aggregation                                 │    │
│  │  [ ] Set up alerting on errors                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Scaling                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  [ ] Add load balancer for horizontal scaling                  │    │
│  │  [ ] Use managed PostgreSQL for HA                             │    │
│  │  [ ] Implement background task queue for PDF processing        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Reverse Proxy Configuration (Nginx Example)

```nginx
server {
    listen 80;
    server_name docsense.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name docsense.example.com;

    # SSL certificates
    ssl_certificate     /etc/nginx/ssl/docsense.crt;
    ssl_certificate_key /etc/nginx/ssl/docsense.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy to FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # Static files
    location /static/ {
        alias /path/to/static/;
        expires 30d;
    }
}
```

### 6.4 Uvicorn Multi-Worker Setup

```bash
# Run with 4 workers
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --proxy-headers \
    --forwarded-allow-ips="*"
```

---

## 7. Environment Configurations

### 7.1 Environment Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENVIRONMENT MATRIX                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┬─────────────┬──────────────┬──────────────────┐      │
│  │ Setting      │ Development │ Staging      │ Production       │      │
│  ├──────────────┼─────────────┼──────────────┼──────────────────┤      │
│  │ ENVIRONMENT  │ development │ staging      │ production       │      │
│  │ DEBUG        │ true        │ false        │ false            │      │
│  │ DATABASE_URL │ localhost   │ staging DB   │ managed DB       │      │
│  │ CORS_ORIGINS │ ["*"]       │ staging URL  │ prod URL         │      │
│  │ JWT_EXPIRY   │ 60 min      │ 60 min       │ 30 min           │      │
│  │ CHUNK_SIZE   │ 500         │ 500          │ 500              │      │
│  │ WORKERS      │ 1           │ 2            │ 4-8              │      │
│  └──────────────┴─────────────┴──────────────┴──────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Complete Environment Variables

```
┌─────────────────────────────────────────────────────────────────────────┐
│                COMPLETE ENVIRONMENT VARIABLES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  # ─── Application ───────────────────────────────────────────────      │
│  ENVIRONMENT=development                                                │
│  API_PREFIX=/api/v1                                                     │
│                                                                          │
│  # ─── Database ───────────────────────────────────────────────────      │
│  DATABASE_URL=postgresql+psycopg://docsense:adminadmin@localhost:5432/docsense_db │
│                                                                          │
│  # ─── Security ──────────────────────────────────────────────────       │
│  JWT_SECRET_KEY=change-me-in-production                                 │
│  JWT_ALGORITHM=HS256                                                     │
│  JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60                                     │
│  CORS_ORIGINS=["*"]                                                      │
│                                                                          │
│  # ─── Cloudinary Storage ────────────────────────────────────────       │
│  CLOUDINARY_CLOUD_NAME=                                                 │
│  CLOUDINARY_API_KEY=                                                    │
│  CLOUDINARY_API_SECRET=                                                 │
│                                                                          │
│  # ─── File Upload ───────────────────────────────────────────────       │
│  MAX_FILE_SIZE_MB=10                                                     │
│                                                                          │
│  # ─── Chunking ──────────────────────────────────────────────────       │
│  CHUNK_SIZE=500                                                          │
│  CHUNK_OVERLAP=50                                                        │
│                                                                          │
│  # ─── Embedding ────────────────────────────────────────────────        │
│  EMBEDDING_PROVIDER=huggingface                                          │
│  EMBEDDING_MODEL=Snowflake/snowflake-arctic-embed-m                      │
│  EMBEDDING_DIMENSION=768                                                 │
│  HUGGINGFACE_TOKEN=                                                      │
│                                                                          │
│  # ─── LLM ───────────────────────────────────────────────────────       │
│  GROQ_API_KEY=                                                           │
│  GROQ_CHAT_MODEL=                                                        │
│                                                                          │
│  # ─── Retrieval ────────────────────────────────────────────────        │
│  RETRIEVAL_DEFAULT_TOP_K=10                                              │
│  RETRIEVAL_MAX_TOP_K=50                                                  │
│  RRF_K=60                                                                │
│  RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2                    │
│  RERANKER_MAX_RESULTS=20                                                 │
│  EVIDENCE_GRADING_TOP_K=4                                                │
│  CORRECTIVE_RETRIEVAL_MAX_ATTEMPTS=2                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Backup & Restore

### 8.1 Database Backup

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATABASE BACKUP                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Manual Backup:                                                       │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  pg_dump -U docsense -h localhost docsense_db > backup.sql │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  2. Docker Container Backup:                                            │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  docker exec backend-db-1 pg_dump -U docsense docsense_db  │    │
│     │    > backup_$(date +%Y%m%d).sql                            │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  3. Automated Daily Backup (cron):                                      │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  0 2 * * * docker exec backend-db-1 pg_dump -U docsense    │    │
│     │    docsense_db > /backups/docsense_$(date +\%Y\%m\%d).sql  │    │
│     │  # Retain 30 days                                          │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Database Restore

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATABASE RESTORE                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Restore from SQL dump:                                              │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  psql -U docsense -h localhost docsense_db < backup.sql    │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  2. Docker Container Restore:                                           │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  cat backup.sql | docker exec -i backend-db-1              │    │
│     │    psql -U docsense docsense_db                             │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  3. After restore, verify migrations:                                   │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  alembic current                                             │    │
│     │  # Should match expected migration head                     │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Health Checks & Monitoring

### 9.1 Health Check Endpoint

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      HEALTH CHECK PROCESS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Endpoint: GET /health                                                  │
│  Response: {"status": "ok"}                                             │
│                                                                         │
│  Docker Healthcheck:                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]   │    │
│  │  interval: 30s                                                  │    │
│  │  timeout: 10s                                                   │    │
│  │  retries: 3                                                     │    │
│  │  start_period: 10s                                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Monitoring Checks:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  • API availability: GET /health should return 200              │    │
│  │  • Database connectivity: health check queries DB               │    │
│  │  • External services: Cloudinary/HF/Groq reachable              │    │
│  │  • Disk space: < 80% utilization                                │    │
│  │  • Memory: < 80% utilization                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Monitoring Tools

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MONITORING TOOLS                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Application Metrics                                            │    │
│  │  • FastAPI built-in OpenAPI metrics                            │    │
│  │  • Structured logs (timestamp, level, module, message)        │    │
│  │  • Custom middleware for request timing                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Infrastructure (Recommended)                                   │    │
│  │  • Prometheus + Grafana for metrics                            │    │
│  │  • Sentry for error tracking                                   │    │
│  │  • ELK Stack for log aggregation                               │    │
│  │  • Uptime Kuma for availability pings                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Troubleshooting

### 10.1 Common Issues

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TROUBLESHOOTING                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: Connection refused to PostgreSQL                        │    │
│  │  Fix:                                                           │    │
│  │    • Check DATABASE_URL host/port                              │    │
│  │    • Verify PostgreSQL is running                              │    │
│  │    • Check firewall rules                                      │    │
│  │    • docker-compose ps                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: "relation does not exist"                               │    │
│  │  Fix:                                                           │    │
│  │    • Run migrations: alembic upgrade head                       │    │
│  │    • alembic current to verify state                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: pgvector extension not found                            │    │
│  │  Fix:                                                           │    │
│  │    • Run: CREATE EXTENSION vector;                              │    │
│  │    • Ensure using pgvector:pg16 image, not vanilla postgres     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: Cloudinary upload fails                                 │    │
│  │  Fix:                                                           │    │
│  │    • Check CLOUDINARY_* env variables                          │    │
│  │    • Verify account has storage quota                          │    │
│  │    • Check network connectivity                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: HuggingFace embedding fails                             │    │
│  │  Fix:                                                           │    │
│  │    • Check HUGGINGFACE_TOKEN validity                          │    │
│  │    • Verify model access permissions                            │    │
│  │    • Check rate limits                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: Groq LLM calls fail                                     │    │
│  │  Fix:                                                           │    │
│  │    • Check GROQ_API_KEY validity                                │    │
│  │    • Verify GROQ_CHAT_MODEL name matches available model         │    │
│  │    • Check quota / rate limits                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: Document processing fails                               │    │
│  │  Fix:                                                           │    │
│  │    • Check document status: failed                              │    │
│  │    • Check application logs for stack trace                    │    │
│  │    • Verify PDF is text-extractable (not scanned)               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Issue: Slow search performance                                 │    │
│  │  Fix:                                                           │    │
│  │    • Verify HNSW and GIN indexes exist                          │    │
│  │    • Check index usage: EXPLAIN ANALYZE                        │    │
│  │    • Reduce top_k / disable reranking                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Log File Locations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      LOG LOCATIONS                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Local Development:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  • Console output (stdout/stderr)                               │    │
│  │  • uvicorn default logger                                       │    │
│  │  • Application structured logs to console                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Docker:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  • docker-compose logs -f api                                   │    │
│  │  • docker-compose logs -f db                                    │    │
│  │  • docker logs backend-api-1                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Production:                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  • Aggregated to ELK/Splunk                                     │    │
│  │  • Application logs → stdout (docker)                           │    │
│  │  • Database logs → PostgreSQL log directory                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Rollback Procedures

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ROLLBACK PROCEDURES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Application Rollback:                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. docker-compose down -v                                     │    │
│  │  2. git checkout <previous-tag>                                │    │
│  │  3. docker-compose build                                        │    │
│  │  4. docker-compose up -d                                        │    │
│  │  5. Verify health: curl /health                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Database Migration Rollback:                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Identify current version: alembic current                    │    │
│  │  2. Rollback one version: alembic downgrade -1                  │    │
│  │  3. Verify application compatibility                           │    │
│  │  4. Test health checks                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Data Restore:                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Restore from latest backup                                 │    │
│  │  2. Verify data integrity                                      │    │
│  │  3. Verify migration alignment                                 │    │
│  │  4. Run smoke tests                                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Security Considerations

### 12.1 Security Checklist

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SECURITY CHECKLIST                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Passwords                                                     │    │
│  │  ✓ bcrypt hashing (12 rounds)                                  │    │
│  │  ✓ No plaintext storage                                        │    │
│  │  ✓ No password logging                                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Tokens                                                        │    │
│  │  ✓ HS256 JWT (configurable algorithm)                          │    │
│  │  ✓ Configurable expiry (default 60 min)                        │    │
│  │  ✓ Strong secret key required in production                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  API Keys                                                      │
│  │  ⚠️ ROTATE immediately: .env contains real keys                │    │
│  │  ⚠️ Ensure .env is gitignored                                 │    │
│  │  ✓ Use environment variables, never hardcode                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Data Isolation                                                 │
│  │  ✓ All queries scoped by user_id                               │    │
│  │  ✓ Ownership checks on every endpoint                          │    │
│  │  ✓ Cascade deletes preserve integrity                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  File Uploads                                                   │
│  │  ✓ MIME type validation                                        │    │
│  │  ✓ Extension validation                                        │    │
│  │  ✓ Size limits (10MB default)                                  │    │
│  │  ✓ Secure storage (Cloudinary)                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Secret Generation

```bash
# Generate a strong JWT secret (Linux/macOS)
openssl rand -base64 64

# Generate a strong JWT secret (Windows PowerShell)
[Convert]::ToBase64String((1..64 | ForEach-Object {Get-Random -Minimum 0 -Maximum 255}) -as [byte[]])
```

---

## 13. Future Deployment Considerations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  FUTURE IMPROVEMENTS                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CI/CD Pipeline                                                      │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • Lint, test, build on every PR                            │    │
│     │  • Automatic deployment to staging on merge                 │    │
│     │  • Blue-green / canary deployment for production            │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  2. Background Task Queue                                              │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • Move document processing to Celery/Redis                │    │
│     │  • Async processing for large documents                    │    │
│     │  • Progress tracking for long-running tasks                │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  3. Horizontal Scaling                                                  │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • Multiple API instances behind load balancer              │    │
│     │  • Managed PostgreSQL (Aurora/Cloud SQL) for HA            │    │
│     │  • Distributed session sharing (if needed)                 │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  4. Observability                                                       │
│     ┌─────────────────────────────────────────────────────────────┐    │
│     │  • Prometheus metrics endpoint                              │    │
│     │  • OpenTelemetry tracing                                    │    │
│     │  • Structured API request logging                            │    │
│     └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*This concludes the DocSense documentation set.*
