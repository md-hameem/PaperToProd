"""
Celery worker integrating with LangGraph pipeline.
"""

import asyncio

from celery import Celery

from app.config import settings
from app.pipeline.checkpointer import get_checkpointer
from app.pipeline.graph import graph_builder

# Setup Celery
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
    async with get_checkpointer() as checkpointer:
        # Compile graph with persistence and human-in-the-loop interruption
        graph = graph_builder.compile(checkpointer=checkpointer, interrupt_before=["scaffolder"])

        from typing import Any, cast

        config = cast("Any", {"configurable": {"thread_id": str(job_id)}})

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
