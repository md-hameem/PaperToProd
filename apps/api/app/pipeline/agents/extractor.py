"""
AI Pipeline — Extractor Agent (Doc 08 §3.1).
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

# Prompts
CLASSIFIER_PROMPT = """
You are an expert machine learning researcher. Analyze the following abstract and classify the paper into one of these domains:
- "CV" for Computer Vision (e.g., CNNs, ViTs, object detection, image synthesis)
- "NLP" for Natural Language Processing (e.g., Transformers, LLMs, tokenization, text generation)
- "RL" for Reinforcement Learning (e.g., policy gradients, Q-learning, environments, agents)
- "GENERAL" for anything else or interdisciplinary.

Respond with ONLY the exact classification string from the list above.
"""

EXTRACTOR_PROMPTS = {
    "CV": """You are an expert machine learning researcher. Extract the methodology from the provided Computer Vision arXiv paper.
Focus specifically on spatial resolutions, convolutions, vision transformers, image augmentations, datasets, and hyperparameters.
Return a structured JSON with 'components' (pieces of the methodology) and 'gaps' (missing or inferred details).""",
    "NLP": """You are an expert machine learning researcher. Extract the methodology from the provided Natural Language Processing arXiv paper.
Focus specifically on tokenizers, vocabulary sizes, attention masking, context windows, text corpora, and hyperparameters.
Return a structured JSON with 'components' (pieces of the methodology) and 'gaps' (missing or inferred details).""",
    "RL": """You are an expert machine learning researcher. Extract the methodology from the provided Reinforcement Learning arXiv paper.
Focus specifically on environment definitions, reward functions, action/observation spaces, discount factors, and hyperparameters.
Return a structured JSON with 'components' (pieces of the methodology) and 'gaps' (missing or inferred details).""",
    "GENERAL": """You are an expert machine learning researcher. Extract the methodology from the provided arXiv paper text.
Focus specifically on architecture, training procedure, datasets, and hyperparameters.
Return a structured JSON with 'components' (pieces of the methodology) and 'gaps' (missing or inferred details).""",
}


async def run_extractor(state: JobState, config: RunnableConfig) -> dict:
    """LangGraph node for the Extractor Agent."""
    job_id = state.get("job_id", 0)
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "extractor", "status": "started"}
    )

    import arxiv

    # Fetch text either from arXiv or mock PDF parse
    arxiv_id = state.get("paper", {}).get("arxiv_id")
    paper_url = state.get("paper", {}).get("source_url", "")

    raw_text = ""
    if arxiv_id:
        try:
            import arxiv

            search = arxiv.Search(id_list=[arxiv_id])
            paper_res = next(search.results())
            raw_text = paper_res.summary
        except Exception as e:
            raw_text = f"Error fetching from arxiv: {e}. Fallback abstract."
    elif paper_url.startswith("local:"):
        # Mocking PDF extraction for MVP
        raw_text = "This is a mocked abstract extracted from the uploaded PDF document. The paper proposes a novel framework for robust optimization using a Vision Transformer back-end."
    else:
        raw_text = "No valid paper source provided."

    byo_api_key = config.get("configurable", {}).get("byo_api_key")
    byo_provider = config.get("configurable", {}).get("byo_provider")
    llm = get_llm(temperature=0.1, byo_api_key=byo_api_key, byo_provider=byo_provider)

    # 1. Classify Domain
    classifier_chain = (
        ChatPromptTemplate.from_messages(
            [("system", CLASSIFIER_PROMPT), ("user", "Paper Abstract: {text}")]
        )
        | llm
    )

    classification_result = await classifier_chain.ainvoke({"text": raw_text})
    domain = classification_result.content.strip().upper()
    if domain not in EXTRACTOR_PROMPTS:
        domain = "GENERAL"

    await publish_job_event(
        job_id,
        {
            "event_type": "agent_logs",
            "agent_name": "extractor",
            "logs": [f"Classified paper domain as: {domain}"],
        },
    )

    # 2. Extract Methodology using domain-specific prompt
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
    extractor_prompt = EXTRACTOR_PROMPTS[domain]

    chain = (
        ChatPromptTemplate.from_messages(
            [("system", extractor_prompt), ("user", "Paper Text: {text}")]
        )
        | structured_llm
    )

    result = await chain.ainvoke({"text": raw_text})

    # Update state
    methodology = {
        "components": result.get("components", []),
        "gaps": result.get("gaps", []),
    }

    # We must construct a dict to update the PaperState reducer properly without losing fields
    # LangGraph replace_dict means we need to supply the full dict or merge carefully
    paper_state = state.get("paper", {})
    paper_state["domain_classification"] = domain
    paper_state["raw_text"] = raw_text

    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "extractor", "status": "completed"}
    )

    return {"paper": paper_state, "methodology": methodology}
