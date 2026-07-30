"""
AI Pipeline — Finder Agent (Doc 08 §3.2).
"""

from github import Github
from github.GithubException import RateLimitExceededException

from app.config import settings
from app.pipeline.state import JobState
from app.websocket.manager import publish_job_event


async def run_finder(state: JobState) -> dict:
    """LangGraph node for the Finder Agent."""
    job_id = state["job_id"]
    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "finder", "status": "started"}
    )

    paper = state.get("paper", {})
    title = paper.get("title") or paper.get("arxiv_id", "")

    candidate_repos = []
    chosen_strategy = "generate_fresh"

    # 1. Search GitHub if we have a title/id and a token
    if title and settings.github_client_secret:
        try:
            # Note: For MVP, we use the client secret placeholder as a PAT if available,
            # or just unauthenticated search (which is heavily rate limited).
            # In a real app we'd use a Github App integration.
            gh = Github(
                settings.github_client_secret if len(settings.github_client_secret) > 20 else None
            )

            # Simple keyword search on the title
            query = f"{title} in:readme"
            repositories = gh.search_repositories(query=query, sort="stars", order="desc")

            for repo in repositories[:3]:
                candidate_repos.append(
                    {
                        "url": repo.html_url,
                        "stars": repo.stargazers_count,
                        "last_commit": repo.updated_at.isoformat() if repo.updated_at else "",
                        "similarity_score": 0.8,  # Mocked similarity for MVP
                        "license": repo.license.name if repo.license else None,
                    }
                )

            if candidate_repos:
                chosen_strategy = "adapt_existing"

        except RateLimitExceededException:
            # Fallback to generate fresh if rate limited
            pass
        except Exception as e:
            await publish_job_event(
                job_id,
                {
                    "event_type": "log_line",
                    "agent_name": "finder",
                    "payload": {"message": f"GitHub search error: {e}"},
                },
            )

    await publish_job_event(
        job_id, {"event_type": "agent_transition", "agent_name": "finder", "status": "completed"}
    )

    return {"candidate_repos": candidate_repos, "chosen_repo_strategy": chosen_strategy}
