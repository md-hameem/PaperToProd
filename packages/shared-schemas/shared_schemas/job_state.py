"""
JobState — The single shared state object threaded through the LangGraph graph.

This is the contract between all agents. Each agent reads from and writes to
defined slices of this state. LangGraph persists it at each node transition.

See Doc 08 §2 for the full specification.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DomainClassification(str, Enum):
    CV = "cv"
    NLP = "nlp"
    RL = "rl"
    OTHER = "other"


class ConfidenceLevel(str, Enum):
    HIGH = "high"        # Explicitly stated in paper
    MEDIUM = "medium"    # Inferred from citation/prior work
    LOW = "low"          # Defaulted from general convention


class MethodologyComponent(BaseModel):
    """A single extracted methodology component with traceability."""
    name: str
    description: str
    source_ref: str  # Section/page/equation number in the paper
    confidence: ConfidenceLevel
    category: str  # e.g., "architecture", "loss_function", "training_procedure"


class MethodologyGap(BaseModel):
    """A flagged ambiguity or missing detail from the paper."""
    description: str
    proposed_default: Optional[str] = None
    rationale: Optional[str] = None
    source_ref: str


class CandidateRepo(BaseModel):
    """A candidate existing implementation found by the Finder agent."""
    url: str
    stars: int = 0
    last_commit: Optional[str] = None
    similarity_score: float = 0.0
    license: Optional[str] = None


class RepoStrategy(str, Enum):
    GENERATE_FRESH = "generate_fresh"
    ADAPT_EXISTING = "adapt_existing"


class ComponentValidationStatus(BaseModel):
    """Per-component validation result."""
    component_name: str
    status: str  # "validated", "failed", "skipped"
    details: Optional[str] = None


class AuditEntry(BaseModel):
    """A single audit log entry for observability."""
    agent: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tokens_used: int = 0
    model_used: str = ""


class JobState(BaseModel):
    """
    The full shared state for a single reproduction job.
    Threaded through the LangGraph pipeline and checkpointed at every transition.
    """

    # Identity
    job_id: str
    user_id: str
    workspace_id: Optional[str] = None

    # Paper
    paper_source_url: str = ""
    paper_arxiv_id: Optional[str] = None
    paper_title: str = ""
    paper_raw_text: str = ""
    paper_sections: list[str] = Field(default_factory=list)
    paper_equations: list[str] = Field(default_factory=list)
    paper_figures: list[str] = Field(default_factory=list)
    paper_tables: list[str] = Field(default_factory=list)
    domain_classification: Optional[DomainClassification] = None

    # Methodology (Extractor output)
    methodology_components: list[MethodologyComponent] = Field(default_factory=list)
    methodology_gaps: list[MethodologyGap] = Field(default_factory=list)

    # Discovery (Finder output)
    candidate_repos: list[CandidateRepo] = Field(default_factory=list)
    chosen_repo_strategy: Optional[RepoStrategy] = None

    # Generation (Scaffolder output)
    scaffold_file_tree: list[str] = Field(default_factory=list)
    scaffold_dependency_manifest: str = ""
    scaffold_target_framework: str = "pytorch"
    generated_files: dict[str, str] = Field(default_factory=dict)  # path -> content

    # Containerization (DevOps output)
    dockerfile: str = ""
    compose_config: Optional[str] = None
    gpu_required: bool = False

    # Validation (Reviewer output)
    validation_attempt_count: int = 0
    validation_last_error: Optional[str] = None
    fidelity_score: Optional[float] = None
    per_component_status: list[ComponentValidationStatus] = Field(default_factory=list)

    # Documentation (DocGenerator output)
    readme: str = ""
    fidelity_report: str = ""

    # Human approval
    approvals: dict[str, dict] = Field(default_factory=dict)

    # Audit
    audit_log: list[AuditEntry] = Field(default_factory=list)
