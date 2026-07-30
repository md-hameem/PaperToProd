"""
Core SQLAlchemy ORM models — Doc 10 (Database Architecture).

Tables:
  - users             — user accounts (OAuth providers)
  - jobs              — paper reproduction jobs
  - job_state_checkpoints — LangGraph state snapshots for crash recovery
  - job_events        — agent transition audit log
  - job_artifacts     — storage references for generated files
"""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ── Enums ─────────────────────────────────────────────────────


class JobStatus(StrEnum):
    """Pipeline lifecycle status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ArtifactType(StrEnum):
    """Types of files produced by the pipeline."""

    SOURCE_PDF = "source_pdf"
    REPOSITORY_ZIP = "repository_zip"
    FULL_LOG = "full_log"
    FIDELITY_REPORT = "fidelity_report"
    README = "readme"


class AuthProvider(StrEnum):
    """Supported OAuth providers."""

    GITHUB = "github"
    GOOGLE = "google"


# ── Users ─────────────────────────────────────────────────────


class User(Base):
    """User account — simplified for MVP (OAuth only, no workspaces)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False)
    auth_provider_id: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    jobs: Mapped[list["Job"]] = relationship(back_populates="user", lazy="selectin")


# ── Jobs ──────────────────────────────────────────────────────


class Job(Base):
    """Paper reproduction job — the central entity."""

    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_user_created", "user_id", "created_at"),
        Index("ix_jobs_arxiv_id", "paper_arxiv_id"),
        Index(
            "ix_jobs_active_status",
            "status",
            postgresql_where="status IN ('queued', 'running')",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Paper metadata
    paper_source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    paper_arxiv_id: Mapped[str | None] = mapped_column(String(30))
    paper_title: Mapped[str | None] = mapped_column(String(500))
    domain_classification: Mapped[str | None] = mapped_column(String(30))

    # Status & results
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.QUEUED.value)
    current_agent: Mapped[str | None] = mapped_column(String(30))
    fidelity_score: Mapped[float | None] = mapped_column()
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Cost tracking
    compute_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    token_cost_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="jobs")
    checkpoints: Mapped[list["JobStateCheckpoint"]] = relationship(
        back_populates="job", lazy="selectin"
    )
    events: Mapped[list["JobEvent"]] = relationship(back_populates="job", lazy="selectin")
    artifacts: Mapped[list["JobArtifact"]] = relationship(back_populates="job", lazy="selectin")


# ── Job State Checkpoints ─────────────────────────────────────


class JobStateCheckpoint(Base):
    """LangGraph state checkpoint — one per node transition for crash recovery."""

    __tablename__ = "job_state_checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    node_name: Mapped[str] = mapped_column(String(50), nullable=False)
    state_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="checkpoints")


# ── Job Events ────────────────────────────────────────────────


class JobEvent(Base):
    """Immutable audit log of agent transitions and pipeline events."""

    __tablename__ = "job_events"
    __table_args__ = (Index("ix_job_events_job_created", "job_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(50))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="events")


# ── Job Artifacts ─────────────────────────────────────────────


class JobArtifact(Base):
    """Reference to a file stored in object storage (MinIO/S3)."""

    __tablename__ = "job_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="artifacts")
