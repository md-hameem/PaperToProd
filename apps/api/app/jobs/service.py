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
    paper_url: str,
) -> Job:
    """Create a new reproduction job after validation."""
    # Validate URL format
    arxiv_id = extract_arxiv_id(paper_url)
    if not arxiv_id:
        raise HTTPException(
            status_code=422,
            detail="Invalid paper URL. Please provide a valid arXiv URL "
            "(e.g. https://arxiv.org/abs/2301.12345).",
        )

    # Check for duplicate submissions
    existing = await db.execute(
        select(Job).where(
            Job.user_id == user_id,
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
                "message": "A job for this paper already exists.",
                "existing_job_id": existing_job.id,
                "existing_status": existing_job.status,
            },
        )

    # Create the job
    job = Job(
        user_id=user_id,
        paper_source_url=paper_url,
        paper_arxiv_id=arxiv_id,
        status=JobStatus.QUEUED.value,
    )
    db.add(job)
    await db.flush()

    # Create initial event
    event = JobEvent(
        job_id=job.id,
        sequence=1,
        agent_name=None,
        event_type="job_created",
        payload={"paper_url": paper_url, "arxiv_id": arxiv_id},
    )
    db.add(event)
    await db.commit()
    await db.refresh(job)

    # TODO: Dispatch Celery task here
    # from app.worker import run_pipeline
    # run_pipeline.delay(job.id)

    return job


async def get_job(db: AsyncSession, job_id: int, user_id: int) -> Job:
    """Get a single job by ID, scoped to the current user."""
    result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


async def list_jobs(
    db: AsyncSession,
    user_id: int,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Job], str | None]:
    """List jobs for a user with cursor-based pagination."""
    query = (
        select(Job)
        .where(Job.user_id == user_id)
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


async def cancel_job(db: AsyncSession, job_id: int, user_id: int) -> Job:
    """Cancel a running or queued job."""
    job = await get_job(db, job_id, user_id)

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
    user_id: int,
    since_sequence: int = 0,
) -> list[JobEvent]:
    """Get events for a job since a given sequence number (for reconnection replay)."""
    # Verify ownership
    await get_job(db, job_id, user_id)

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
