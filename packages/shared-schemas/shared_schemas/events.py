"""
Event schemas — WebSocket and job_events table event types.
"""

from typing import Any

from pydantic import BaseModel


class JobEvent(BaseModel):
    """Event emitted by the worker, consumed by WebSocket handler and persisted."""

    type: str  # "agent_transition", "log_line", "approval_required", "job_complete", "job_failed"
    agent: str | None = None
    status: str | None = None
    line: str | None = None
    sequence: int = 0
    data: dict[str, Any] | None = None
