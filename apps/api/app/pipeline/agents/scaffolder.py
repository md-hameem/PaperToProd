"""
AI Pipeline — Scaffolder Agent (Doc 08 §3.3).
"""

import asyncio

from langchain_core.prompts import ChatPromptTemplate

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

SCAFFOLD_PROMPT = """
You are an expert ML engineer. Based on the following methodology components extracted from a paper,
design a Python project file structure (PyTorch).
Methodology: {methodology}

CRITICAL: You MUST include a `tests/` directory with comprehensive `pytest` unit test files for each custom component or layer in the file tree.

Return a structured JSON with 'file_tree' (a flat dictionary of filepath -> description) and 'dependency_manifest' (a dictionary of package -> version constraint).
"""

FILE_GEN_PROMPT = """
You are an expert ML engineer implementing a research paper.
Write the complete, runnable Python code for the following file: {filepath}

File purpose: {file_purpose}
Overall Methodology Context: {methodology}

If this file is a unit test (e.g. inside `tests/`), ensure you write comprehensive `pytest` assertions.
Include shape checks for custom ML layers and forward-pass smoke tests for larger components to verify execution without CUDA dependencies if possible.

Return ONLY the raw python code. Do not include markdown code blocks (e.g. ```python) around the response. Start immediately with imports.
"""


async def _generate_file(
    llm, filepath: str, file_purpose: str, methodology: str
) -> tuple[str, str]:
    """Generate a single file's content using the LLM."""
    prompt = ChatPromptTemplate.from_messages([("user", FILE_GEN_PROMPT)])
    chain = prompt | llm

    # We use string output here, not structured.
    result = await chain.ainvoke(
        {"filepath": filepath, "file_purpose": file_purpose, "methodology": methodology}
    )

    # Clean up markdown code blocks if the model ignored instructions
    code = result.content.strip()
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    return filepath, code.strip()


async def run_scaffolder(state: JobState) -> dict:
    """LangGraph node for the Scaffolder Agent."""
    job_id = state["job_id"]
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "scaffolder", "status": "started"}
    )

    methodology = state.get("methodology", {})
    methodology_str = "\n".join(
        [f"- {c['id']}: {c['description']}" for c in methodology.get("components", [])]
    )

    llm = get_llm(temperature=0.1)

    # 1. Generate scaffold
    schema = {
        "title": "ProjectScaffold",
        "type": "object",
        "properties": {
            "file_tree": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "Dictionary mapping file path to its purpose",
            },
            "dependency_manifest": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "Dictionary mapping pip package name to version constraint",
            },
        },
        "required": ["file_tree", "dependency_manifest"],
    }

    scaffold_chain = ChatPromptTemplate.from_messages(
        [("user", SCAFFOLD_PROMPT)]
    ) | llm.with_structured_output(schema)
    scaffold_result = await scaffold_chain.ainvoke({"methodology": methodology_str})

    file_tree = scaffold_result.get("file_tree", {"main.py": "Main entry point"})
    dependency_manifest = scaffold_result.get("dependency_manifest", {"torch": ">=2.0.0"})

    # 2. Parallel Generation of files
    await publish_job_event(
        job_id,
        {
            "event_type": "log_line",
            "agent_name": "scaffolder",
            "payload": {"message": f"Generating {len(file_tree)} files in parallel..."},
        },
    )

    tasks = []
    # Use standard model for file gen
    file_gen_llm = get_llm(temperature=0.2)

    for filepath, purpose in file_tree.items():
        tasks.append(_generate_file(file_gen_llm, filepath, purpose, methodology_str))

    generated_files_list = await asyncio.gather(*tasks)

    generated_files = {filepath: content for filepath, content in generated_files_list}

    await publish_job_event(
        job_id,
        {"event_type": "agent_transition", "agent_name": "scaffolder", "status": "completed"},
    )

    return {
        "scaffold": {
            "file_tree": file_tree,
            "dependency_manifest": dependency_manifest,
            "target_framework": "pytorch",
        },
        "generated_files": generated_files,
    }
