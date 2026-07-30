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
)


async def _run_pipeline_async(job_id: int, initial_state: dict):
    """Async wrapper to run the LangGraph pipeline."""
    async with get_checkpointer() as checkpointer:
        # Compile graph with persistence
        graph = graph_builder.compile(checkpointer=checkpointer)

        from typing import Any, cast

        config = cast("Any", {"configurable": {"thread_id": str(job_id)}})

        # Run graph
        await graph.ainvoke(initial_state, config)


@celery_app.task(name="run_pipeline", bind=True, max_retries=3)
def run_pipeline(self, job_id: int, paper_url: str, arxiv_id: str):
    """
    Celery task that initializes and runs the LangGraph AI pipeline.
    """
    initial_state = {"job_id": job_id, "paper": {"source_url": paper_url, "arxiv_id": arxiv_id}}

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
