"""
PaperToProd API — FastAPI Application Factory

Modular monolith serving REST + WebSocket endpoints.
Modules: auth, jobs, billing, integrations, gallery, notifications, websocket.
"""

import contextlib
import hashlib
import os
import uuid

import jwt
import structlog
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.config import settings

# Initialize OpenTelemetry
resource = Resource(
    attributes={
        SERVICE_NAME: "papertoprod-api",
        SERVICE_VERSION: os.environ.get("DEPLOYMENT_VERSION", "unknown"),
    }
)
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Configure Structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)


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

    @app.middleware("http")
    async def structlog_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Extract Actor for Audit Logging
        actor_id = "anonymous"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            if token.startswith("ptp_"):
                actor_id = f"apikey:{hashlib.sha256(token.encode()).hexdigest()[:8]}"
            else:
                try:
                    # Non-verifying decode just for audit trail attribution
                    payload = jwt.decode(token, options={"verify_signature": False})
                    actor_id = f"user:{payload.get('sub', 'unknown')}"
                except Exception:
                    actor_id = "invalid_token"

        structlog.contextvars.bind_contextvars(actor_id=actor_id)

        # Inject request_id into OpenTelemetry current span
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.set_attribute("request_id", request_id)
            current_span.set_attribute("actor_id", actor_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # Emit [AUDIT] log for mutative requests
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            logger = structlog.get_logger("audit")
            logger.info(
                "audit_event",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
            )

        return response

    # Instrument FastAPI with OpenTelemetry
    FastAPIInstrumentor.instrument_app(app)

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
    from app.auth.api_keys import router as api_keys_router
    from app.auth.router import router as auth_router
    from app.billing.router import router as billing_router
    from app.gallery.router import router as gallery_router
    from app.integrations.router import router as integrations_router
    from app.jobs.router import router as jobs_router
    from app.jobs.shared_router import router as shared_router
    from app.notifications.router import router as notifications_router
    from app.users.router import router as users_router
    from app.webhooks.router import router as webhooks_router
    from app.websocket.router import router as websocket_router
    from app.workspaces.router import router as workspaces_router

    api_v1 = APIRouter(prefix="/api/v1")

    api_v1.include_router(auth_router, prefix="/auth", tags=["Auth"])
    api_v1.include_router(api_keys_router, prefix="/auth", tags=["API Keys"])
    api_v1.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
    api_v1.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
    api_v1.include_router(billing_router, tags=["Billing"])
    api_v1.include_router(integrations_router, tags=["Integrations"])
    api_v1.include_router(users_router, tags=["Users"])
    api_v1.include_router(notifications_router, tags=["Notifications"])
    api_v1.include_router(webhooks_router, tags=["Webhooks"])
    api_v1.include_router(gallery_router, tags=["Gallery"])

    # We include shared_router on the main app directly since its prefix is already in the router
    app.include_router(shared_router)

    app.include_router(api_v1)
    app.include_router(websocket_router, tags=["WebSockets"])


app = create_app()
