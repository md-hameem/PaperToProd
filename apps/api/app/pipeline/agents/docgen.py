"""
AI Pipeline — Documentation Generator Agent (Doc 08 §3.6).
"""

import json

from langchain_core.prompts import ChatPromptTemplate

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

DOCGEN_PROMPT = """
You are an expert technical writer. Based on the following state of a machine learning reproduction job, write a comprehensive README.md and a Fidelity Report.

Paper Title: {paper_title}
Methodology Extracted:
{methodology}

Generated Files Overview:
{file_overview}

Validation Status (Fidelity Score: {fidelity_score}):
{validation_status}

Return a structured JSON with 'readme' (markdown string) and 'fidelity_report' (markdown string).
"""


async def run_docgen(state: JobState) -> dict:
    """LangGraph node for the DocGen Agent."""
    job_id = state["job_id"]
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "docgen", "status": "started"}
    )

    paper = state.get("paper", {})
    methodology = state.get("methodology", {})
    generated_files = state.get("generated_files", {})
    validation = state.get("validation", {})

    methodology_str = json.dumps(methodology.get("components", []), indent=2)
    files_str = "\n".join(generated_files.keys())
    val_status_str = json.dumps(validation.get("per_component_status", []), indent=2)
    fidelity_score = validation.get("fidelity_score", "N/A")

    llm = get_llm(temperature=0.2)

    schema = {
        "title": "Documentation",
        "type": "object",
        "properties": {"readme": {"type": "string"}, "fidelity_report": {"type": "string"}},
        "required": ["readme", "fidelity_report"],
    }

    chain = ChatPromptTemplate.from_messages(
        [("user", DOCGEN_PROMPT)]
    ) | llm.with_structured_output(schema)

    result = await chain.ainvoke(
        {
            "paper_title": paper.get("title", "Unknown Title"),
            "methodology": methodology_str,
            "file_overview": files_str,
            "fidelity_score": fidelity_score,
            "validation_status": val_status_str,
        }
    )

    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "docgen", "status": "completed"}
    )

    return {
        "documentation": {
            "readme": result.get("readme", ""),
            "fidelity_report": result.get("fidelity_report", ""),
        }
    }
