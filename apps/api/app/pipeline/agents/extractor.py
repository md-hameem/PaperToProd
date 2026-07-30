"""
AI Pipeline — Extractor Agent (Doc 08 §3.1).
"""

from langchain_core.prompts import ChatPromptTemplate

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

# Prompts
EXTRACTOR_SYSTEM_PROMPT = """
You are an expert machine learning researcher. Your task is to extract the methodology from the provided arXiv paper text.
Focus specifically on architecture, training procedure, datasets, and hyperparameters.
Return a structured JSON with 'components' (pieces of the methodology) and 'gaps' (missing or inferred details).
"""


async def run_extractor(state: JobState) -> dict:
    """LangGraph node for the Extractor Agent."""
    job_id = state["job_id"]
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "extractor", "status": "started"}
    )

    # 1. Fetch paper (simulated text for now, but normally we'd use `arxiv` library)
    # import arxiv
    # search = arxiv.Search(id_list=[state["paper"]["arxiv_id"]])
    # paper = next(search.results())
    # raw_text = paper.summary # Fallback if pdf extraction is skipped for MVP speed

    raw_text = state.get("paper", {}).get(
        "raw_text", "Sample abstract describing a ResNet-like architecture with AdamW optimizer."
    )

    llm = get_llm(temperature=0.1)

    # Define JSON schema for structured output via tool calling (or use Pydantic)
    schema = {
        "title": "MethodologyExtraction",
        "type": "object",
        "properties": {
            "components": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": "string"},
                        "source_ref": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["id", "description", "confidence"],
                },
            },
            "gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": "string"},
                        "proposed_default": {"type": "string"},
                    },
                    "required": ["id", "description", "proposed_default"],
                },
            },
        },
        "required": ["components", "gaps"],
    }

    structured_llm = llm.with_structured_output(schema)
    prompt = ChatPromptTemplate.from_messages(
        [("system", EXTRACTOR_SYSTEM_PROMPT), ("user", "Paper Text: {text}")]
    )

    chain = prompt | structured_llm

    result = await chain.ainvoke({"text": raw_text})

    # Update state
    methodology = {
        "components": result.get("components", []),
        "gaps": result.get("gaps", []),
    }

    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "extractor", "status": "completed"}
    )

    # The returned dict is merged into the global JobState by LangGraph's reducers
    return {"methodology": methodology}
