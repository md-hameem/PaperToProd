"""
Jobs module — API routes for job lifecycle (create, list, get, cancel, events, artifacts).
See Doc 14 for the full API specification.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.jobs import service
from app.jobs.schemas import (
    ArtifactDownloadResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobEventResponse,
    JobEventsListResponse,
    JobListResponse,
    JobSummaryResponse,
)

router = APIRouter()

# TODO: Replace with real auth dependency that extracts user_id from JWT
MOCK_USER_ID = 1


@router.post("", response_model=JobCreateResponse, status_code=201)
async def create_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new paper reproduction job."""
    job = await service.create_job(
        db=db,
        user_id=MOCK_USER_ID,
        paper_url=request.paper_url,
    )
    return JobCreateResponse(id=job.id, status=job.status)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    cursor: str | None = Query(None, description="Pagination cursor (ISO datetime)"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List jobs for the current user with cursor-based pagination."""
    jobs, next_cursor = await service.list_jobs(
        db=db,
        user_id=MOCK_USER_ID,
        cursor=cursor,
        limit=limit,
    )
    return JobListResponse(
        items=[JobSummaryResponse.model_validate(j) for j in jobs],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full job state snapshot."""
    job = await service.get_job(db=db, job_id=job_id, user_id=MOCK_USER_ID)
    return JobDetailResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobDetailResponse)
async def cancel_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running or queued job."""
    job = await service.cancel_job(db=db, job_id=job_id, user_id=MOCK_USER_ID)
    return JobDetailResponse.model_validate(job)


@router.get("/{job_id}/events", response_model=JobEventsListResponse)
async def get_job_events(
    job_id: int,
    since_sequence: int = Query(0, ge=0, description="Return events after this sequence number"),
    db: AsyncSession = Depends(get_db),
):
    """Get job events for reconnection replay."""
    events = await service.get_job_events(
        db=db,
        job_id=job_id,
        user_id=MOCK_USER_ID,
        since_sequence=since_sequence,
    )
    return JobEventsListResponse(
        events=[JobEventResponse.model_validate(e) for e in events],
        latest_sequence=events[-1].sequence if events else since_sequence,
    )


@router.get("/{job_id}/artifacts/repository", response_model=ArtifactDownloadResponse)
async def get_repository_download(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a signed download URL for the generated repository archive."""
    # Verify job exists and is owned by user
    job = await service.get_job(db=db, job_id=job_id, user_id=MOCK_USER_ID)

    # TODO: Generate signed MinIO URL
    return ArtifactDownloadResponse(
        download_url=f"/storage/jobs/{job.id}/repository.zip",
        artifact_type="repository_zip",
        size_bytes=None,
        expires_in_seconds=3600,
    )


@router.get("/health")
async def jobs_health():
    return {"status": "ok", "module": "jobs"}
