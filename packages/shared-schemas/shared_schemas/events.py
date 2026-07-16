"""
Event schemas — WebSocket and job_events table event types.
"""

from pydantic import BaseModel
from typing import Optional, Any


class JobEvent(BaseModel):
    """Event emitted by the worker, consumed by WebSocket handler and persisted."""
    type: str  # "agent_transition", "log_line", "approval_required", "job_complete", "job_failed"
    agent: Optional[str] = None
    status: Optional[str] = None
    line: Optional[str] = None
    sequence: int = 0
    data: Optional[dict[str, Any]] = None
