import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.api.v1.endpoints import health
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.rate_limit import get_client_identifier, limiter

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s v%s started", settings.project_name, settings.app_version)

    if settings.supabase_url and settings.supabase_secret_key:
        logger.info("Supabase Storage configured (bucket: %s)", settings.supabase_bucket)
    elif settings.cloudinary_cloud_name:
        logger.info("Cloudinary configured (cloud: %s)", settings.cloudinary_cloud_name)
    else:
        logger.warning("No remote object storage configured — uploads will run in local fallback mode")

    yield
    logger.info("%s shutting down", settings.project_name)


app = FastAPI(
    title=settings.project_name,
    version=settings.app_version,
    description="Backend API for the DocSense project",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# ── Robust CORS Setup for Allowed Frontend Origins & Vercel Domains ────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app|.*\.onrender\.com)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Retry-After"],
)


# ── Global Rate Limiting Middleware (120 req/min per IP) ─────────────────
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in ("/health", "/docs", "/openapi.json"):
        return await call_next(request)

    client_id = get_client_identifier(request)
    allowed, retry_after = limiter.check_rate_limit(
        key=f"global:{client_id}",
        max_requests=120,
        window_seconds=60,
    )
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "status_code": 429,
                "message": f"Too many requests. Please wait {retry_after} seconds before retrying.",
            },
            headers={"Retry-After": str(retry_after)},
        )
    return await call_next(request)


# ── Request Timing Logger ────────────────────────────────────────────────
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - t0
    logger.info(
        "%s %s %d %.3fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


register_exception_handlers(app)

app.include_router(health.router)
app.include_router(api_router, prefix=settings.api_prefix)