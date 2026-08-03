"""
AI Pipeline — Documentation Generator Agent (Doc 08 §3.6).
"""

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

DOCGEN_PROMPT = """
You are an expert technical writer. Based on the following state of a machine learning reproduction job, write a comprehensive README.md and a structured Fidelity Report.

Paper Title: {paper_title}
Methodology Extracted:
{methodology}

Generated Files Overview:
{file_overview}

Validation Status (Fidelity Score: {fidelity_score}):
{validation_status}

For the fidelity report, provide structured JSON matching the requested schema exactly.
"""


async def run_docgen(state: JobState, config: RunnableConfig) -> dict:
    """LangGraph node for the DocGen Agent."""
    job_id = state.get("job_id", 0)
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
    byo_api_key = config.get("configurable", {}).get("byo_api_key")
    byo_provider = config.get("configurable", {}).get("byo_provider")

    # Generate README
    llm = get_llm(temperature=0.2, byo_api_key=byo_api_key, byo_provider=byo_provider)

    schema = {
        "title": "Documentation",
        "type": "object",
        "properties": {
            "readme": {"type": "string"},
            "fidelity_report": {
                "type": "object",
                "properties": {
                    "coverage": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "component_name": {"type": "string"},
                                "has_code": {"type": "boolean"},
                                "reason_if_missing": {"type": "string"},
                            },
                            "required": ["component_name", "has_code", "reason_if_missing"],
                        },
                    },
                    "structural_checks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "check_name": {"type": "string"},
                                "status": {"type": "string", "enum": ["pass", "fail", "warning"]},
                                "details": {"type": "string"},
                            },
                            "required": ["check_name", "status", "details"],
                        },
                    },
                    "execution": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "summary": {"type": "string"},
                        },
                        "required": ["success", "summary"],
                    },
                    "assumptions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "rationale": {"type": "string"},
                            },
                            "required": ["description", "rationale"],
                        },
                    },
                    "license": {
                        "type": "object",
                        "properties": {
                            "source_repo_url": {"type": "string"},
                            "license_type": {"type": "string"},
                            "disclosure_text": {"type": "string"},
                        },
                        "required": ["source_repo_url", "license_type", "disclosure_text"],
                    },
                },
                "required": [
                    "coverage",
                    "structural_checks",
                    "execution",
                    "assumptions",
                    "license",
                ],
            },
        },
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
            "fidelity_report": result.get("fidelity_report", {}),
        }
    }
