import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.router import get_current_user
from app.database import get_db
from app.models import Job, JobShare, User

router = APIRouter(tags=["Shared Jobs"])


# ── Schemas ───────────────────────────────────────────────────


class ShareLinkCreateRequest(BaseModel):
    expires_in_days: int | None = None
    allow_download: bool = False


class ShareLinkResponse(BaseModel):
    token: str
    expires_at: str | None
    allow_download: bool
    share_url: str


class SharedJobResponse(BaseModel):
    id: int
    paper_title: str | None
    domain_classification: str | None
    fidelity_score: float | None
    status: str
    paper_source_url: str
    allow_download: bool
    # We omit advanced_options, user data, and raw traces for security


# ── Routes ────────────────────────────────────────────────────


@router.post("/api/v1/jobs/{job_id}/share-link", response_model=ShareLinkResponse)
async def create_share_link(
    job_id: int,
    payload: ShareLinkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an expirable, read-only share link for a job."""
    # Verify ownership
    stmt = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    token = secrets.token_urlsafe(32)
    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=payload.expires_in_days)

    share = JobShare(
        job_id=job.id,
        token=token,
        expires_at=expires_at,
        allow_download=payload.allow_download,
    )
    db.add(share)
    await db.commit()

    # Note: frontend determines full base URL, we just return the token and relative path
    share_url = f"/shared/{token}"

    return ShareLinkResponse(
        token=token,
        expires_at=expires_at.isoformat() if expires_at else None,
        allow_download=payload.allow_download,
        share_url=share_url,
    )


@router.get("/api/v1/shared/{token}", response_model=SharedJobResponse)
async def get_shared_job(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve read-only job snapshot via share token (No Auth Required)."""
    stmt = select(JobShare).options(selectinload(JobShare.job)).where(JobShare.token == token)
    result = await db.execute(stmt)
    share = result.scalar_one_or_none()

    if not share:
        raise HTTPException(status_code=404, detail="Share link not found or invalid.")

    if share.expires_at and share.expires_at < datetime.now(UTC):
        # Auto-cleanup expired share (optional, but good practice)
        await db.delete(share)
        await db.commit()
        raise HTTPException(status_code=410, detail="This share link has expired.")

    job = share.job
    return SharedJobResponse(
        id=job.id,
        paper_title=job.paper_title,
        domain_classification=job.domain_classification,
        fidelity_score=job.fidelity_score,
        status=job.status,
        paper_source_url=job.paper_source_url,
        allow_download=share.allow_download,
    )
