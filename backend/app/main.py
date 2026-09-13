import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.v1.endpoints import health
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s v%s started", settings.project_name, settings.app_version)

    if settings.cloudinary_cloud_name:
        logger.info("Cloudinary configured (cloud: %s)", settings.cloudinary_cloud_name)
    else:
        logger.warning("Cloudinary is NOT configured — uploads will fail")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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