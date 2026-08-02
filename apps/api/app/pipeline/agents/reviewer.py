"""
AI Pipeline — Reviewer Agent (Validation & Repair Loop) (Doc 08 §3.5).
"""

import asyncio

from langchain_core.prompts import ChatPromptTemplate

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

MAX_RETRIES = 3

DIAGNOSE_PROMPT = """
You are diagnosing a failure in a machine learning codebase execution.
Error log:
{error_log}

Categorize this error. Is it a 'dependency' error (e.g. module not found, incompatible cuda version) or a 'logic' error (e.g. syntax error, tensor shape mismatch, unexpected kwarg)?
Return a JSON object with 'category' (either "dependency" or "logic") and 'explanation'.
"""


async def run_reviewer(state: JobState) -> dict:
    """LangGraph node for the Reviewer Agent."""
    job_id = state["job_id"]
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "reviewer", "status": "started"}
    )

    validation = state.get("validation", {})
    attempt_count = validation.get("attempt_count", 0) + 1

    # MVP: Mock the execution of the container.
    # In a real system, we would write generated_files and container configs to a temp dir,
    # invoke docker build & docker run, and capture the stdout/stderr.

    # We will simulate a failure on the first attempt and success on the second.
    mock_success = attempt_count > 1

    if mock_success:
        await publish_job_event(
            job_id,
            {
                "event_type": "log_line",
                "agent_name": "reviewer",
                "payload": {"message": "> pytest tests/"},
            },
        )
        await asyncio.sleep(1.0)
        await publish_job_event(
            job_id,
            {
                "event_type": "log_line",
                "agent_name": "reviewer",
                "payload": {
                    "message": "============================= test session starts ==============================\nCollected 24 items\ntests/test_model.py ........................ [100%]\n============================== 24 passed in 1.45s =============================="
                },
            },
        )
        await publish_job_event(
            job_id,
            {
                "event_type": "log_line",
                "agent_name": "reviewer",
                "payload": {
                    "message": "Unit tests and execution succeeded. Computing fidelity score..."
                },
            },
        )

        # Computing fidelity score based on methodology components
        methodology = state.get("methodology", {})
        components = methodology.get("components", [])

        per_component_status = [{"id": c["id"], "implemented": True} for c in components]

        return {
            "validation": {
                "attempt_count": attempt_count,
                "last_error": None,
                "fidelity_score": 0.92,  # Mock high score
                "per_component_status": per_component_status,
            }
        }
    else:
        await publish_job_event(
            job_id,
            {
                "event_type": "log_line",
                "agent_name": "reviewer",
                "payload": {"message": "> pytest tests/"},
            },
        )
        await asyncio.sleep(1.0)

        # Simulate a failure
        mock_error_log = (
            "============================= test session starts ==============================\n"
            "Collected 24 items\n"
            "tests/test_model.py F....................... [100%]\n"
            "=================================== FAILURES ===================================\n"
            "RuntimeError: mat1 and mat2 shapes cannot be multiplied (64x256 and 128x64)"
        )
        await publish_job_event(
            job_id,
            {
                "event_type": "log_line",
                "agent_name": "reviewer",
                "payload": {"message": f"Execution failed:\n{mock_error_log}"},
            },
        )

        # Diagnose the error using LLM
        llm = get_llm(temperature=0.0)
        schema = {
            "title": "ErrorDiagnosis",
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["dependency", "logic"]},
                "explanation": {"type": "string"},
            },
            "required": ["category", "explanation"],
        }

        chain = ChatPromptTemplate.from_messages(
            [("user", DIAGNOSE_PROMPT)]
        ) | llm.with_structured_output(schema)
        diagnosis = await chain.ainvoke({"error_log": mock_error_log})

        await publish_job_event(
            job_id,
            {"event_type": "agent_transition", "agent_name": "reviewer", "status": "completed"},
        )

        return {
            "validation": {
                "attempt_count": attempt_count,
                "last_error": {
                    "log": mock_error_log,
                    "category": diagnosis.get("category", "logic"),
                    "explanation": diagnosis.get("explanation", ""),
                },
                "fidelity_score": None,
                "per_component_status": [],
            }
        }


def route_repair(state: JobState) -> str:
    """
    Conditional edge function that determines the next node after Reviewer.
    Returns the name of the next agent (or "docgen" if done).
    """
    validation = state.get("validation", {})
    last_error = validation.get("last_error")

    # If no error, we succeeded -> move to docgen
    if not last_error:
        return "docgen"

    # Check max retries
    if validation.get("attempt_count", 0) >= MAX_RETRIES:
        return "docgen"  # Fail forward, partial success

    # Route based on diagnosis category
    category = last_error.get("category")
    if category == "dependency":
        return "devops"
    else:
        return "scaffolder"
