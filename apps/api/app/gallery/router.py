from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.router import get_current_user
from app.database import get_db
from app.models import Job, User

router = APIRouter(prefix="/gallery", tags=["Gallery"])


# ── Schemas ───────────────────────────────────────────────────


class GalleryJobResponse(BaseModel):
    id: int
    paper_title: str | None
    domain_classification: str | None
    fidelity_score: float | None
    status: str
    submitter_username: str | None
    created_at: str
    completed_at: str | None
    paper_source_url: str


# ── Routes ────────────────────────────────────────────────────


@router.get("", response_model=list[GalleryJobResponse])
async def list_gallery_jobs(
    domain: str | None = Query(None, description="Filter by domain (e.g., CV, NLP)"),
    sort: str = Query("score", description="Sort by 'score' or 'recency'"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List public jobs in the gallery (No auth required)."""
    stmt = (
        select(Job)
        .options(selectinload(Job.user))
        .where(Job.is_public == True)
        .where(Job.status == "completed")
    )

    if domain:
        stmt = stmt.where(Job.domain_classification == domain)

    if sort == "recency":
        stmt = stmt.order_by(Job.completed_at.desc().nulls_last())
    else:  # default to score
        stmt = stmt.order_by(Job.fidelity_score.desc().nulls_last())

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return [
        GalleryJobResponse(
            id=j.id,
            paper_title=j.paper_title,
            domain_classification=j.domain_classification,
            fidelity_score=j.fidelity_score,
            status=j.status,
            submitter_username=j.user.email.split("@")[0] if j.user else "Anonymous",
            created_at=j.created_at.isoformat(),
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
            paper_source_url=j.paper_source_url,
        )
        for j in jobs
    ]


@router.post("/{job_id}")
async def publish_job_to_gallery(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a job to the public gallery."""
    stmt = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed jobs can be published")

    job.is_public = True
    await db.commit()
    return {"status": "published", "job_id": job.id}


@router.delete("/{job_id}")
async def remove_job_from_gallery(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a job from the public gallery."""
    stmt = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.is_public = False
    await db.commit()
    return {"status": "unpublished", "job_id": job.id}
