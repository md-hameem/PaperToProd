"""
PaperToProd API — FastAPI Application Factory

Modular monolith serving REST + WebSocket endpoints.
Modules: auth, jobs, billing, integrations, gallery, notifications, websocket.
"""

import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize storage buckets on startup
    from app.storage import init_buckets

    try:
        init_buckets()
    except Exception as e:
        print(f"Warning: Failed to initialize MinIO buckets: {e}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="PaperToProd API",
        description="Research reproduction engine — paper in, validated repository out.",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
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
    from app.billing.router import router as billing_router
    from app.integrations.router import router as integrations_router
    from app.jobs.router import router as jobs_router
    from app.users.router import router as users_router
    from app.websocket.router import router as websocket_router
    from app.workspaces.router import router as workspaces_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])
    app.include_router(workspaces_router, prefix="/api/v1/workspaces", tags=["Workspaces"])
    app.include_router(billing_router, prefix="/api/v1", tags=["Billing"])
    app.include_router(integrations_router, prefix="/api/v1", tags=["Integrations"])
    app.include_router(users_router, prefix="/api/v1", tags=["Users"])
    app.include_router(websocket_router, tags=["WebSockets"])

    # Future: integrations, gallery, notifications routers


app = create_app()
