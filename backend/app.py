"""
AI Resume Screening & Candidate Ranking System — FastAPI Application Entry Point
================================================================================
Creates and configures the FastAPI application with all middleware, routers,
exception handlers, and startup/shutdown lifecycle events.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database.base import engine, Base
from database.init_db import initialize_database
from middleware.error_handler import register_exception_handlers
from middleware.logging_middleware import LoggingMiddleware
from routes.auth_routes import router as auth_router
from routes.upload_routes import router as upload_router
from routes.candidate_routes import router as candidate_router
from routes.ranking_routes import router as ranking_router
from routes.analytics_routes import router as analytics_router
from routes.report_routes import router as report_router
from routes.feedback_routes import router as feedback_router
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle.
    Runs startup tasks before yield and shutdown tasks after.
    """
    # -------------------------------------------------------------------------
    # Startup
    # -------------------------------------------------------------------------
    logger.info("🚀 Starting AI Resume Screening System v%s", settings.APP_VERSION)

    # Ensure required directories exist
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.reports_path.mkdir(parents=True, exist_ok=True)
    settings.log_path.mkdir(parents=True, exist_ok=True)
    logger.info("✅ Directory structure verified")

    # Initialize database (create tables + seed admin user)
    await initialize_database()
    logger.info("✅ Database initialized")

    # Pre-load ML models to avoid cold-start on first request
    try:
        from ai.embedding_service import EmbeddingService
        EmbeddingService.get_instance()
        logger.info("✅ Sentence Transformer model loaded")
    except Exception as exc:
        logger.error("❌ Failed to load Sentence Transformer: %s", exc)

    try:
        import spacy
        spacy.load(settings.SPACY_MODEL)
        logger.info("✅ spaCy model '%s' loaded", settings.SPACY_MODEL)
    except Exception as exc:
        logger.error("❌ Failed to load spaCy model '%s': %s", settings.SPACY_MODEL, exc)

    logger.info("🎯 Application startup complete — listening on %s:%d",
                settings.BACKEND_HOST, settings.BACKEND_PORT)

    yield  # Application runs here

    # -------------------------------------------------------------------------
    # Shutdown
    # -------------------------------------------------------------------------
    logger.info("🛑 Shutting down AI Resume Screening System...")
    engine.dispose()
    logger.info("✅ Database connections closed")


def create_application() -> FastAPI:
    """
    Factory function that creates and fully configures the FastAPI application.

    Returns:
        FastAPI: The configured application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
## AI Resume Screening & Candidate Ranking System

An enterprise-grade AI-powered recruitment platform that:

- 📄 **Parses** PDF and DOCX resumes using NLP
- 🧠 **Matches** candidates to job descriptions via Sentence Transformers
- 📊 **Ranks** candidates with explainable AI scoring (100-point scale)
- 🔍 **Analyzes** skill gaps and ATS compatibility
- 📈 **Visualizes** analytics and generates downloadable reports

### Authentication
Use the `/auth/login` endpoint to obtain a JWT token, then include it in the
`Authorization: Bearer <token>` header for protected endpoints.

### Default Credentials (development)
- **Username**: admin
- **Password**: Admin@123
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    # -------------------------------------------------------------------------
    # Middleware (order matters — outermost runs first on request, last on response)
    # -------------------------------------------------------------------------

    # CORS — must be first
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip compression for responses > 1KB
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # Custom request/response logging
    app.add_middleware(LoggingMiddleware)

    # -------------------------------------------------------------------------
    # Exception handlers
    # -------------------------------------------------------------------------
    register_exception_handlers(app)

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    API_PREFIX = "/api/v1"

    app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])
    app.include_router(upload_router, prefix=f"{API_PREFIX}/upload", tags=["File Upload"])
    app.include_router(candidate_router, prefix=f"{API_PREFIX}/candidates", tags=["Candidates"])
    app.include_router(ranking_router, prefix=f"{API_PREFIX}/ranking", tags=["Ranking"])
    app.include_router(analytics_router, prefix=f"{API_PREFIX}/analytics", tags=["Analytics & Dashboard"])
    app.include_router(report_router, prefix=f"{API_PREFIX}/reports", tags=["Reports"])
    app.include_router(feedback_router, prefix=f"{API_PREFIX}/feedback", tags=["Feedback & ATS"])

    # -------------------------------------------------------------------------
    # Static files — serve uploaded files directly
    # -------------------------------------------------------------------------
    if settings.upload_path.exists():
        app.mount(
            "/uploads",
            StaticFiles(directory=str(settings.upload_path)),
            name="uploads",
        )

    # -------------------------------------------------------------------------
    # Health check endpoint
    # -------------------------------------------------------------------------
    @app.get("/health", tags=["Health"], summary="System health check")
    async def health_check(request: Request) -> dict:
        """
        Returns system health status including version, environment, and uptime.
        This endpoint is unauthenticated for use by load balancers and monitoring tools.
        """
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }

    @app.get("/", tags=["Root"], summary="API root")
    async def root() -> dict:
        """Redirect users to API documentation."""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
