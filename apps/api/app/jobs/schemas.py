"""
API request/response schemas for the Jobs endpoints — Doc 14.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ── Requests ──────────────────────────────────────────────────


class JobCreateRequest(BaseModel):
    """POST /api/v1/jobs — Create a new reproduction job."""

    paper_url: str = Field(
        ...,
        description="arXiv URL (e.g. https://arxiv.org/abs/2301.12345)",
        examples=["https://arxiv.org/abs/2301.12345"],
    )
    advanced_options: dict | None = None


# ── Responses ─────────────────────────────────────────────────


class JobSummaryResponse(BaseModel):
    """Compact job representation for list views / dashboard."""

    id: int
    paper_title: str | None
    paper_arxiv_id: str | None
    status: str
    fidelity_score: float | None
    current_agent: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class JobDetailResponse(BaseModel):
    """Full job state snapshot for the job detail / progress page."""

    id: int
    paper_source_url: str
    paper_title: str | None
    paper_arxiv_id: str | None
    domain_classification: str | None
    advanced_options: dict | None
    status: str
    current_agent: str | None
    fidelity_score: float | None
    error_message: str | None
    retry_count: int
    compute_cost_cents: int
    token_cost_cents: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class JobCreateResponse(BaseModel):
    """Response from POST /api/v1/jobs."""

    id: int
    status: str
    message: str = "Job queued successfully"


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    items: list[JobSummaryResponse]
    next_cursor: str | None = None
    has_more: bool = False


# ── Events ────────────────────────────────────────────────────


class JobEventResponse(BaseModel):
    """A single pipeline event."""

    id: int
    sequence: int
    agent_name: str | None
    event_type: str
    payload: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobEventsListResponse(BaseModel):
    """List of events for reconnection replay."""

    events: list[JobEventResponse]
    latest_sequence: int = 0


# ── Artifacts ─────────────────────────────────────────────────


class ArtifactDownloadResponse(BaseModel):
    """Signed URL for artifact download."""

    download_url: str
    artifact_type: str
    size_bytes: int | None
    expires_in_seconds: int = 3600
