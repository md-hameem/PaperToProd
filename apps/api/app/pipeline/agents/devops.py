"""
AI Pipeline — DevOps Agent (Doc 08 §3.4).
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event

# Compatibility matrix for known-good combinations
COMPATIBILITY_MATRIX = {
    "torch==2.2.0": "nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04",
    "torch==2.1.0": "nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04",
    "torch==2.0.1": "nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04",
    "tensorflow==2.15.0": "nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04",
    "tensorflow==2.14.0": "nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04",
}

DEVOPS_PROMPT = """
You are an expert DevOps and ML Infra engineer.
Given the following project file structure, dependency manifest, and paper domain, generate a Dockerfile and docker-compose.yml suitable for running this machine learning code.

Dependencies:
{dependencies}

File structure:
{file_tree}

Target framework: {target_framework}
Paper Domain: {domain}

CRITICAL CONSTRAINTS:
1. Base Image: You MUST use this exact base image: `{base_image}`
2. CPU Fallback: Your Dockerfile MUST support a build argument `ARG USE_CPU=false`. If true, the container should be able to run without NVIDIA runtimes (useful for smoke tests on commodity hardware).
3. Multi-service: If the domain is 'RL', you MUST generate a `docker-compose.yml` that includes a 'redis' service and wires it to the main application container via environment variables.

Determine if a GPU (NVIDIA CUDA) is required based on the components ({gpu_components_hint}). If true, set gpu_required=true.
Return a JSON object with 'dockerfile', 'compose_config' and 'gpu_required' (boolean).
"""


async def run_devops(state: JobState, config: RunnableConfig) -> dict:
    """LangGraph node for the DevOps Agent."""
    job_id = state.get("job_id", 0)
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "devops", "status": "started"}
    )

    scaffold = state.get("scaffold", {})
    deps_dict = scaffold.get("dependency_manifest", {})
    deps = "\n".join([f"{k} {v}" for k, v in deps_dict.items()])
    files = "\n".join(scaffold.get("file_tree", {}).keys())
    framework = scaffold.get("target_framework", "pytorch")

    paper = state.get("paper", {})
    domain = paper.get("domain_classification", "GENERAL")

    # 1. GPU Auto-Detection Hint
    methodology = state.get("methodology", {})
    components_text = " ".join(
        [c["description"].lower() for c in methodology.get("components", [])]
    )

    gpu_keywords = ["llm", "transformer", "resnet", "vit", "cnn", "diffusion", "cuda"]
    needs_gpu = any(kw in components_text for kw in gpu_keywords)
    gpu_components_hint = "Requires GPU" if needs_gpu else "Might not require GPU"

    # 2. Hardcoded Base Image Injection
    base_image = "python:3.10-slim"

    for dep, ver in deps_dict.items():
        key = f"{dep.lower()}=={ver}"
        if key in COMPATIBILITY_MATRIX:
            base_image = COMPATIBILITY_MATRIX[key]
            break

    # Default fallback for unpinned PyTorch/TF
    if base_image == "python:3.10-slim":
        if "torch" in [k.lower() for k in deps_dict]:
            base_image = "nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04"
        elif "tensorflow" in [k.lower() for k in deps_dict]:
            base_image = "nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04"

    byo_api_key = config.get("configurable", {}).get("byo_api_key")
    byo_provider = config.get("configurable", {}).get("byo_provider")

    llm = get_llm(temperature=0.1, byo_api_key=byo_api_key, byo_provider=byo_provider)

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
        [("system", DEVOPS_PROMPT)]
    ) | llm.with_structured_output(schema)

    result = await chain.ainvoke(
        {
            "dependencies": deps,
            "file_tree": files,
            "target_framework": framework,
            "domain": domain,
            "base_image": base_image,
            "gpu_components_hint": gpu_components_hint,
        }
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
