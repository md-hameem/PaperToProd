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
    JSON,
    Boolean,
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


class WorkspaceRole(StrEnum):
    """RBAC roles within a workspace."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    BILLING = "billing"


class SubscriptionTier(StrEnum):
    """Billing and usage tiers for a workspace."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# ── Workspaces ────────────────────────────────────────────────


class Workspace(Base):
    """Organization/Workspace entity."""

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    subscription_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SubscriptionTier.FREE.value
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100))

    # GitHub Integration
    github_installation_id: Mapped[str | None] = mapped_column(String(100))
    github_account_name: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace", lazy="selectin", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(back_populates="workspace", lazy="selectin")


class WorkspaceMember(Base):
    """Join table mapping Users to Workspaces with roles."""

    __tablename__ = "workspace_members"
    __table_args__ = (Index("ix_workspace_members_user", "user_id"),)

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WorkspaceRole.MEMBER.value
    )

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="workspace_memberships")


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
    notification_preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    jobs: Mapped[list["Job"]] = relationship(back_populates="user", lazy="selectin")
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    """Developer API Keys for dual-auth access."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_keys")


# ── Jobs ──────────────────────────────────────────────────────


class Job(Base):
    """Paper reproduction job — the central entity."""

    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_workspace_created", "workspace_id", "created_at"),
        Index("ix_jobs_arxiv_id", "paper_arxiv_id"),
        Index(
            "ix_jobs_active_status",
            "status",
            postgresql_where="status IN ('queued', 'running')",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False)

    # Paper metadata
    paper_source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    paper_arxiv_id: Mapped[str | None] = mapped_column(String(30))
    paper_title: Mapped[str | None] = mapped_column(String(500))
    domain_classification: Mapped[str | None] = mapped_column(String(30))
    advanced_options: Mapped[dict | None] = mapped_column(JSON, nullable=True)

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
    workspace: Mapped["Workspace"] = relationship(back_populates="jobs")
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


# ── Notifications & Webhooks ──────────────────────────────────


class Notification(Base):
    """In-app notifications for users."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")


class Webhook(Base):
    """Programmatic webhooks for workspaces."""

    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    secret: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace: Mapped["Workspace"] = relationship()


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
    job: Mapped["Job"] = relationship(back_populates="job")


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
