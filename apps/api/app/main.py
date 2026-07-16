"""
PaperToProd API — FastAPI Application Factory

Modular monolith serving REST + WebSocket endpoints.
Modules: auth, jobs, billing, integrations, gallery, notifications, websocket.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="PaperToProd API",
        description="Research reproduction engine — paper in, validated repository out.",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Register all module routers under /api/v1."""
    from app.auth.router import router as auth_router
    from app.jobs.router import router as jobs_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])

    # Future: billing, integrations, gallery, notifications routers


app = create_app()
