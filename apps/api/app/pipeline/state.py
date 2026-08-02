"""
AI Pipeline — Shared State Schema (Doc 08 §2).
"""

# Using TypedDict to define the state for LangGraph
from typing import Annotated, Any, TypedDict


def replace_dict(old: dict, new: dict) -> dict:
    """Reducer that replaces the entire dict."""
    return new


def extend_list(old: list, new: list) -> list:
    """Reducer that appends to a list."""
    if old is None:
        return new
    return old + new


class PaperState(TypedDict, total=False):
    source_url: str
    arxiv_id: str
    title: str | None
    raw_text: str | None
    sections: list[str] | None
    equations: list[str] | None
    figures: list[str] | None
    tables: list[str] | None
    domain_classification: str | None


class ComponentState(TypedDict):
    id: str
    description: str
    source_ref: str | None
    confidence: str  # "high", "medium", "low"


class GapState(TypedDict):
    id: str
    description: str
    proposed_default: str


class MethodologyState(TypedDict, total=False):
    components: Annotated[list[ComponentState], extend_list]
    gaps: Annotated[list[GapState], extend_list]


class CandidateRepo(TypedDict):
    url: str
    stars: int
    last_commit: str
    similarity_score: float
    license: str | None


class ScaffoldState(TypedDict, total=False):
    file_tree: dict[str, Any]
    dependency_manifest: dict[str, str]
    target_framework: str


class ContainerState(TypedDict, total=False):
    dockerfile: str
    compose_config: str
    gpu_required: bool


class ValidationState(TypedDict, total=False):
    attempt_count: int
    last_error: dict[str, Any] | None
    fidelity_score: float | None
    per_component_status: list[dict[str, Any]]


class DocumentationState(TypedDict, total=False):
    readme: str | None
    fidelity_report: str | None


class JobState(TypedDict, total=False):
    """
    The central state object threaded through all LangGraph agents.
    Matches Doc 08 §2 exactly.
    """

    job_id: int
    user_id: int

    focus_scope: str | None
    framework_override: str | None

    paper: Annotated[PaperState, replace_dict]
    methodology: Annotated[MethodologyState, replace_dict]

    candidate_repos: Annotated[list[CandidateRepo], replace_dict]
    chosen_repo_strategy: str  # "generate_fresh" | "adapt_existing"
    human_approved_repo_url: str | None

    scaffold: Annotated[ScaffoldState, replace_dict]

    # Generated files: filename -> content
    generated_files: Annotated[dict[str, str], replace_dict]

    container: Annotated[ContainerState, replace_dict]
    validation: Annotated[ValidationState, replace_dict]
    documentation: Annotated[DocumentationState, replace_dict]

    # Checkpoint approvals tracking
    approvals: Annotated[dict[str, Any], replace_dict]

    # Audit trail
    audit_log: Annotated[list[dict[str, Any]], extend_list]
