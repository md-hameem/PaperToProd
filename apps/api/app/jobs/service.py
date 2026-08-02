"""
Jobs module — Business logic for job lifecycle.
Handles creation, queries, cancellation, and arXiv validation.
"""

import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, JobEvent, JobStatus

# Regex patterns for arXiv URL validation
ARXIV_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)"
)
ARXIV_ID_PATTERN = re.compile(r"(\d{4}\.\d{4,5}(?:v\d+)?)")


def extract_arxiv_id(url: str) -> str | None:
    """Extract arXiv ID from a URL like https://arxiv.org/abs/2301.12345."""
    match = ARXIV_URL_PATTERN.search(url)
    if match:
        return match.group(1)
    # Also accept raw arXiv IDs
    match = ARXIV_ID_PATTERN.match(url.strip())
    return match.group(1) if match else None


async def create_job(
    db: AsyncSession,
    user_id: int,
    workspace_id: int,
    paper_url: str,
    advanced_options: dict | None = None,
) -> Job:
    """Create a new reproduction job after validation."""
    # Extract arXiv ID if possible (for duplicates and metadata)
    arxiv_id = extract_arxiv_id(paper_url)

    # Check for duplicate submissions if we have an arXiv ID
    if arxiv_id:
        existing = await db.execute(
            select(Job).where(
                Job.workspace_id == workspace_id,
                Job.paper_arxiv_id == arxiv_id,
                Job.status.in_(
                    [JobStatus.QUEUED.value, JobStatus.RUNNING.value, JobStatus.COMPLETED.value]
                ),
            )
        )
        existing_job = existing.scalars().first()
        if existing_job:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "A job for this paper already exists in this workspace.",
                    "existing_job_id": existing_job.id,
                    "existing_status": existing_job.status,
                },
            )

    # Fetch workspace to check tier and quota
    from sqlalchemy import func

    from app.models import SubscriptionTier, Workspace

    ws_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws_result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if workspace.subscription_tier == SubscriptionTier.FREE.value:
        # Check quota (e.g. limit to 3 jobs for FREE tier)
        count_stmt = select(func.count(Job.id)).where(Job.workspace_id == workspace_id)
        count_result = await db.execute(count_stmt)
        total_jobs = count_result.scalar() or 0

        if total_jobs >= 3:
            raise HTTPException(
                status_code=403,
                detail="Free tier limit reached (3 jobs max). Please upgrade to Pro to continue.",
            )

    # Create the job
    job = Job(
        user_id=user_id,
        workspace_id=workspace_id,
        paper_source_url=paper_url,
        paper_arxiv_id=arxiv_id,
        status=JobStatus.QUEUED.value,
        advanced_options=advanced_options,
    )
    db.add(job)
    await db.flush()

    payload = {
        "paper_url": paper_url,
        "arxiv_id": arxiv_id,
    }
    if advanced_options:
        if advanced_options.get("focus_scope"):
            payload["focus_scope"] = advanced_options["focus_scope"]
        if advanced_options.get("framework_override"):
            payload["framework_override"] = advanced_options["framework_override"]

    # Create initial event
    event = JobEvent(
        job_id=job.id,
        sequence=1,
        agent_name=None,
        event_type="job_created",
        payload=payload,
    )
    db.add(event)
    await db.commit()
    await db.refresh(job)

    from app.worker import run_pipeline

    # Route PRO/ENTERPRISE to high_priority queue
    queue_name = "celery"
    if workspace.subscription_tier in (
        SubscriptionTier.PRO.value,
        SubscriptionTier.ENTERPRISE.value,
    ):
        queue_name = "high_priority"

    # Pass the payload directly to the pipeline worker
    f_scope = advanced_options.get("focus_scope") if advanced_options else None
    f_override = advanced_options.get("framework_override") if advanced_options else None
    run_pipeline.apply_async(
        args=[job.id, paper_url, arxiv_id, f_scope, f_override], queue=queue_name
    )

    return job


async def get_job(db: AsyncSession, job_id: int, workspace_id: int) -> Job:
    """Get a single job by ID, scoped to the workspace."""
    result = await db.execute(select(Job).where(Job.id == job_id, Job.workspace_id == workspace_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


async def list_jobs(
    db: AsyncSession,
    workspace_id: int,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Job], str | None]:
    """List jobs for a workspace with cursor-based pagination."""
    query = (
        select(Job)
        .where(Job.workspace_id == workspace_id)
        .order_by(Job.created_at.desc())
        .limit(limit + 1)  # fetch one extra to detect has_more
    )

    if cursor:
        # Cursor is a datetime ISO string
        cursor_dt = datetime.fromisoformat(cursor)
        query = query.where(Job.created_at < cursor_dt)

    result = await db.execute(query)
    jobs = list(result.scalars().all())

    next_cursor = None
    has_more = len(jobs) > limit
    if has_more:
        jobs = jobs[:limit]
        next_cursor = jobs[-1].created_at.isoformat()

    return jobs, next_cursor


async def cancel_job(db: AsyncSession, job_id: int, workspace_id: int) -> Job:
    """Cancel a running or queued job."""
    job = await get_job(db, job_id, workspace_id)

    if job.status not in (JobStatus.QUEUED.value, JobStatus.RUNNING.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in '{job.status}' state.",
        )

    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.utcnow()

    # Record cancellation event
    event = JobEvent(
        job_id=job.id,
        sequence=await _next_sequence(db, job.id),
        agent_name=None,
        event_type="job_cancelled",
        payload={"cancelled_by": "user"},
    )
    db.add(event)
    await db.commit()
    await db.refresh(job)

    # TODO: Send Celery revoke signal

    return job


async def get_job_events(
    db: AsyncSession,
    job_id: int,
    workspace_id: int,
    since_sequence: int = 0,
) -> list[JobEvent]:
    """Get events for a job since a given sequence number (for reconnection replay)."""
    # Verify ownership
    await get_job(db, job_id, workspace_id)

    result = await db.execute(
        select(JobEvent)
        .where(JobEvent.job_id == job_id, JobEvent.sequence > since_sequence)
        .order_by(JobEvent.sequence)
    )
    return list(result.scalars().all())


async def _next_sequence(db: AsyncSession, job_id: int) -> int:
    """Get the next monotonic sequence number for a job's events."""
    from sqlalchemy import func

    result = await db.execute(
        select(func.coalesce(func.max(JobEvent.sequence), 0)).where(JobEvent.job_id == job_id)
    )
    return (result.scalar() or 0) + 1
