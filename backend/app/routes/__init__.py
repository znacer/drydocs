"""API route modules for the DryDocs backend."""

from app.routes.documents import router as documents_router
from app.routes.references import router as references_router
from app.routes.search import router as search_router

# Export all routers for inclusion in the main app
__all__ = ["documents_router", "references_router", "search_router"]
