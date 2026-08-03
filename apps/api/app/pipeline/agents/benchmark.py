"""
AI Pipeline — Benchmark Agent (Doc 08 §3.7).
"""

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.pipeline.llm import get_llm
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event


class BenchmarkMetric(BaseModel):
    metric_name: str = Field(description="Name of the metric, e.g., 'Accuracy', 'F1 Score', 'BLEU'")
    paper_baseline: float = Field(description="The numeric value reported in the original paper")
    reproduced_value: float = Field(
        description="The numeric value achieved by the reproduced codebase"
    )
    delta: float = Field(description="The difference between reproduced and baseline")
    status: str = Field(
        description="'pass', 'warning', or 'fail' based on acceptable margin of error"
    )


class BenchmarkResult(BaseModel):
    dataset_name: str = Field(description="The benchmark dataset used")
    metrics: list[BenchmarkMetric]
    summary: str = Field(description="Brief qualitative summary of benchmark performance")


BENCHMARK_PROMPT = """
You are an expert machine learning evaluator.
Your job is to compare the metrics reported in the original paper with the metrics achieved by our reproduced codebase.

Paper Abstract: {abstract}
Methodology Extracted: {methodology}

The reproduced code was executed and achieved the following logs/metrics:
{mocked_execution_logs}

Analyze this and return a structured JSON conforming to the requested schema. Ensure the 'delta' is correctly calculated (reproduced_value - paper_baseline) and status is 'pass' if the delta is within 5%, 'warning' if within 10%, else 'fail'.
"""


async def run_benchmark(state: JobState, config: RunnableConfig) -> dict:
    """LangGraph node for the Benchmark Agent."""
    job_id = state.get("job_id", 0)
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "benchmark", "status": "started"}
    )

    await publish_job_event(
        job_id,
        {
            "event_type": "agent_logs",
            "agent_name": "benchmark",
            "logs": ["Initiating quantitative fidelity benchmarking..."],
        },
    )

    abstract = state.get("paper", {}).get("raw_text", "")
    methodology = str(state.get("methodology", {}))

    # In MVP, we mock the actual codebase execution logs
    mocked_execution_logs = "Validation Accuracy: 84.2%, Inference Speed: 42ms/img on T4 GPU"

    byo_api_key = config.get("configurable", {}).get("byo_api_key")
    byo_provider = config.get("configurable", {}).get("byo_provider")

    parser = JsonOutputParser(pydantic_object=BenchmarkResult)
    llm = get_llm(temperature=0.1, byo_api_key=byo_api_key, byo_provider=byo_provider)

    chain = ChatPromptTemplate.from_messages([("system", BENCHMARK_PROMPT)]) | llm | parser

    try:
        result = await chain.ainvoke(
            {
                "abstract": abstract,
                "methodology": methodology,
                "mocked_execution_logs": mocked_execution_logs,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        await publish_job_event(
            job_id,
            {
                "event_type": "agent_logs",
                "agent_name": "benchmark",
                "logs": [f"Benchmarking complete. Dataset: {result.get('dataset_name')}."],
            },
        )

        # Log to audit trail
        audit_entry = {
            "agent": "benchmark",
            "action": "execute_benchmark",
            "details": result.get("summary"),
        }

        return {"benchmark_results": result, "audit_log": [audit_entry]}

    except Exception as e:
        await publish_job_event(
            job_id,
            {
                "event_type": "agent_logs",
                "agent_name": "benchmark",
                "logs": [f"Benchmarking failed: {e!s}"],
            },
        )
        return {
            "benchmark_results": {
                "dataset_name": "Unknown",
                "metrics": [],
                "summary": f"Failed to compute benchmarks: {e!s}",
            }
        }
