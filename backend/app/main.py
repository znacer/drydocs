"""FastAPI application with document management endpoints.

This module sets up the FastAPI application and includes all route modules.
The application is structured with domain-specific routers for better organization
and maintainability.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes.documents import router as documents_router
from app.routes.references import router as references_router
from app.routes.search import router as search_router
from app.storage import ensure_bucket

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Initializes database tables and ensures MinIO bucket exists on startup.
    """
    # Initialize database
    await init_db()
    # Ensure MinIO bucket exists
    await ensure_bucket()
    logger.info("Application started successfully")
    yield
    logger.info("Application shutdown")


# Initialize FastAPI app
app = FastAPI(
    title="Document Manager API",
    description="API for managing documents with versioning and Markdown conversion",
    version="1.0.0",
    lifespan=lifespan,
    # Enable OpenAPI docs
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for SvelteKit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(references_router)
app.include_router(search_router)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Global HTTP exception handler.

    Logs HTTP exceptions and returns consistent error responses.
    """
    logger.error(f"HTTP Error: {exc.status_code} - {exc.detail}")
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


# Root endpoint
@app.get(
    "/",
    summary="API Root",
    description="Root endpoint returning API information.",
    tags=["General"],
)
async def root():
    """Root endpoint for the Document Manager API."""
    return {
        "name": "Document Manager API",
        "version": "1.0.0",
        "description": "API for managing documents with versioning and Markdown conversion",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Health check endpoint
@app.get(
    "/health",
    summary="Health Check",
    description="Health check endpoint for monitoring.",
    tags=["General"],
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
