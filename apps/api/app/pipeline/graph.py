"""
AI Pipeline — LangGraph Orchestration (Doc 08 §4).
"""

from langgraph.graph import END, START, StateGraph

from app.pipeline.agents.devops import run_devops
from app.pipeline.agents.docgen import run_docgen
from app.pipeline.agents.extractor import run_extractor
from app.pipeline.agents.finder import run_finder
from app.pipeline.agents.reviewer import route_repair, run_reviewer
from app.pipeline.agents.scaffolder import run_scaffolder
from app.pipeline.state import JobState


def create_pipeline_graph() -> StateGraph:
    """Build and return the LangGraph for the reproduction pipeline."""

    workflow = StateGraph(JobState)

    # Add nodes
    workflow.add_node("extractor", run_extractor)
    workflow.add_node("finder", run_finder)
    workflow.add_node("scaffolder", run_scaffolder)
    workflow.add_node("devops", run_devops)
    workflow.add_node("reviewer", run_reviewer)
    workflow.add_node("docgen", run_docgen)

    # Add edges
    # START -> Extractor and Finder run concurrently (Parallel Execution Doc 08 §5)
    workflow.add_edge(START, "extractor")
    workflow.add_edge(START, "finder")

    # Both must complete before Scaffolder starts
    workflow.add_edge(["extractor", "finder"], "scaffolder")

    # Scaffolder -> DevOps
    workflow.add_edge("scaffolder", "devops")

    # DevOps -> Reviewer (starts validation loop)
    workflow.add_edge("devops", "reviewer")

    # Reviewer -> conditional routing (repair loop)
    workflow.add_conditional_edges(
        "reviewer",
        route_repair,
        {"scaffolder": "scaffolder", "devops": "devops", "docgen": "docgen"},
    )

    # DocGen -> END
    workflow.add_edge("docgen", END)

    return workflow


# Global graph instance ready to be compiled
graph_builder = create_pipeline_graph()
