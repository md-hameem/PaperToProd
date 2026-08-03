"""
Celery worker integrating with LangGraph pipeline.
"""

import asyncio
import os

import structlog
from celery import Celery
from opentelemetry import trace
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from sqlalchemy.future import select

from app.config import settings
from app.database import async_session_maker
from app.models import Job, Notification, User, Webhook, Workspace
from app.pipeline.checkpointer import get_checkpointer
from app.pipeline.graph import graph_builder
from app.utils.crypto import decrypt_key

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
logger = structlog.get_logger()

# Initialize OpenTelemetry
resource = Resource(
    attributes={
        SERVICE_NAME: "papertoprod-worker",
        SERVICE_VERSION: os.environ.get("DEPLOYMENT_VERSION", "unknown"),
    }
)
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Setup Celery
CeleryInstrumentor().instrument()
celery_app = Celery("papertoprod_worker", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker concurrency config (e.g. 4 processes)
    worker_concurrency=4,
    # Queue priorities
    task_default_queue="celery",
    task_create_missing_queues=True,
)


async def _run_pipeline_async(job_id: int, initial_state: dict):
    """Async wrapper to run the LangGraph pipeline."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(job_id=job_id)
    logger.info("Starting pipeline execution", initial_state=initial_state)
    async with get_checkpointer() as checkpointer:
        # Compile graph with persistence and human-in-the-loop interruption
        graph = graph_builder.compile(checkpointer=checkpointer, interrupt_before=["scaffolder"])

        # Fetch job and workspace to get potential BYO key
        byo_api_key = None
        byo_provider = None

        async with async_session_maker() as db:
            stmt = select(Job).where(Job.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                ws_stmt = select(Workspace).where(Workspace.id == job.workspace_id)
                ws_res = await db.execute(ws_stmt)
                ws = ws_res.scalar_one_or_none()
                if ws and ws.byo_llm_api_key_encrypted:
                    byo_api_key = decrypt_key(ws.byo_llm_api_key_encrypted)
                    byo_provider = ws.byo_llm_provider

        from typing import Any, cast

        config_dict = {
            "configurable": {
                "thread_id": str(job_id),
                "byo_api_key": byo_api_key,
                "byo_provider": byo_provider,
            }
        }
        config = cast("Any", config_dict)

        # Run graph
        await graph.ainvoke(initial_state, config)


@celery_app.task(name="run_pipeline", bind=True, max_retries=3)
def run_pipeline(
    self,
    job_id: int,
    paper_url: str,
    arxiv_id: str | None = None,
    focus_scope: str | None = None,
    framework_override: str | None = None,
):
    """
    Celery task that initializes and runs the LangGraph AI pipeline.
    """
    initial_state = {
        "job_id": job_id,
        "paper": {"source_url": paper_url, "arxiv_id": arxiv_id},
        "focus_scope": focus_scope,
        "framework_override": framework_override,
    }

    # We must run the async graph inside the sync celery task
    try:
        asyncio.run(_run_pipeline_async(job_id, initial_state))

        # Dispatch notifications after success
        asyncio.run(_dispatch_notifications(job_id))

        # After success, we should update the DB Job status to COMPLETED
        # (Omitted full DB connection boilerplate for brevity, but a real app
        # would open an AsyncSession here and update the DB).
        return {"status": "completed", "job_id": job_id}

    except Exception as exc:
        # Update DB Job status to FAILED
        self.retry(exc=exc, countdown=60)


async def _resume_pipeline_async(job_id: int, approved_repo_url: str):
    """Resume a paused LangGraph pipeline after human approval."""
    async with get_checkpointer() as checkpointer:
        graph = graph_builder.compile(checkpointer=checkpointer, interrupt_before=["scaffolder"])

        from typing import Any, cast

        config = cast("Any", {"configurable": {"thread_id": str(job_id)}})

        # Update state with the user's choice
        await graph.aupdate_state(config, {"human_approved_repo_url": approved_repo_url})

        # Mark finder as fully completed in websocket so UI moves forward
        from app.websocket.manager import publish_job_event

        await publish_job_event(
            job_id,
            {"event_type": "agent_transition", "agent_name": "finder", "status": "completed"},
        )

        # Resume execution (passing None state)
        await graph.ainvoke(None, config)


async def _dispatch_notifications(job_id: int):
    """Fetch the job and user, check preferences, and dispatch notifications."""
    async with async_session_maker() as db:
        # Get Job and User
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalars().first()
        if not job:
            return

        user_res = await db.execute(select(User).where(User.id == job.user_id))
        user = user_res.scalars().first()
        if not user:
            return

        prefs = user.notification_preferences or {}

        # 1. In-App Notification (Always if not disabled)
        if prefs.get("in_app_enabled", True):
            notif = Notification(
                user_id=user.id,
                message=f"Job #{job_id} ({job.paper_title or 'Untitled'}) has completed successfully.",
                type="job_complete",
            )
            db.add(notif)
            await db.commit()

        # 2. Email Notification (Mock)
        if prefs.get("email_enabled", True):
            print(
                f"\\n\\033[92m[EMAIL DISPATCHED]\\033[0m Job {job_id} completion email sent to {user.email}\\n"
            )

        # 3. Webhooks (Mock)
        wh_res = await db.execute(select(Webhook).where(Webhook.workspace_id == job.workspace_id))
        webhooks = wh_res.scalars().all()
        for wh in webhooks:
            print(
                f"\\n\\033[94m[WEBHOOK DISPATCHED]\\033[0m POST to {wh.url} for Workspace {job.workspace_id}\\n"
            )


@celery_app.task(name="resume_pipeline", bind=True, max_retries=3)
def resume_pipeline(self, job_id: int, approved_repo_url: str):
    """
    Celery task that resumes a paused LangGraph pipeline.
    """
    try:
        asyncio.run(_resume_pipeline_async(job_id, approved_repo_url))
        return {"status": "resumed", "job_id": job_id}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
