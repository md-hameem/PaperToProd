"""
AI Pipeline — DevOps Agent (Doc 08 §3.4).
"""

from langchain_core.prompts import ChatPromptTemplate

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

DEVOPS_PROMPT = """
You are an expert DevOps and ML Infra engineer.
Given the following project file structure and dependency manifest, generate a Dockerfile and docker-compose.yml suitable for running this machine learning code.

Dependencies:
{dependencies}

File structure:
{file_tree}

Target framework: {target_framework}

Determine if a GPU (NVIDIA CUDA) is required based on the dependencies (e.g. torch, tensorflow).
Return a JSON object with 'dockerfile', 'compose_config' and 'gpu_required' (boolean).
"""


async def run_devops(state: JobState) -> dict:
    """LangGraph node for the DevOps Agent."""
    job_id = state["job_id"]
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "devops", "status": "started"}
    )

    scaffold = state.get("scaffold", {})
    deps = "\n".join([f"{k} {v}" for k, v in scaffold.get("dependency_manifest", {}).items()])
    files = "\n".join(scaffold.get("file_tree", {}).keys())
    framework = scaffold.get("target_framework", "pytorch")

    llm = get_llm(temperature=0.0)

    schema = {
        "title": "ContainerConfig",
        "type": "object",
        "properties": {
            "dockerfile": {"type": "string"},
            "compose_config": {"type": "string"},
            "gpu_required": {"type": "boolean"},
        },
        "required": ["dockerfile", "compose_config", "gpu_required"],
    }

    chain = ChatPromptTemplate.from_messages(
        [("user", DEVOPS_PROMPT)]
    ) | llm.with_structured_output(schema)

    result = await chain.ainvoke(
        {"dependencies": deps, "file_tree": files, "target_framework": framework}
    )

    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "devops", "status": "completed"}
    )

    return {
        "container": {
            "dockerfile": result.get("dockerfile", ""),
            "compose_config": result.get("compose_config", ""),
            "gpu_required": result.get("gpu_required", False),
        }
    }
