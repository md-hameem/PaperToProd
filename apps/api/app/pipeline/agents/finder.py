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

    # 1. Search PapersWithCode API (Semantic & Official linkage)
    arxiv_id = paper.get("arxiv_id", "")
    if arxiv_id:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"https://paperswithcode.com/api/v1/papers/{arxiv_id}/repositories/"
                )
                if res.status_code == 200:
                    data = res.json()
                    for repo in data.get("results", [])[:2]:
                        candidate_repos.append(
                            {
                                "url": repo.get("url"),
                                "stars": repo.get("stars", 0),
                                "last_commit": "2024-01-01T00:00:00Z",  # Mocked
                                "similarity_score": 0.99,  # Exact match from PwC
                                "license": None,
                            }
                        )
        except Exception as e:
            await publish_job_event(
                job_id,
                {
                    "event_type": "log_line",
                    "agent_name": "finder",
                    "payload": {"message": f"PwC API error: {e}"},
                },
            )

    # 2. Search GitHub if we have a title/id and a token (Fallback)
    if title and settings.github_client_secret:
        try:
            gh = Github(
                settings.github_client_secret if len(settings.github_client_secret) > 20 else None
            )

            # Domain-aware keyword search
            domain = paper.get("domain_classification", "")
            domain_keyword = "pytorch" if domain in ["CV", "NLP"] else ""
            query = f"{title} {domain_keyword} in:readme"
            repositories = gh.search_repositories(query=query, sort="stars", order="desc")

            for repo in repositories[:3]:
                # Avoid duplicates
                if not any(c["url"] == repo.html_url for c in candidate_repos):
                    candidate_repos.append(
                        {
                            "url": repo.html_url,
                            "stars": repo.stargazers_count,
                            "last_commit": repo.updated_at.isoformat() if repo.updated_at else "",
                            "similarity_score": 0.65,  # Baseline github keyword similarity
                            "license": repo.license.name if repo.license else None,
                        }
                    )
        except RateLimitExceededException:
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

    # 3. Apply Qdrant Semantic Similarity Ranking (Mocked for MVP)
    # Formula: (0.5 * similarity) + (0.3 * normalized_stars) + (0.2 * recency)
    if candidate_repos:
        max_stars = max((c["stars"] for c in candidate_repos), default=1)
        for c in candidate_repos:
            norm_stars = c["stars"] / max_stars if max_stars > 0 else 0
            # Boost similarity slightly if domain matches
            domain_boost = 0.05 if paper.get("domain_classification") else 0
            c["similarity_score"] = min(0.99, c["similarity_score"] + domain_boost)
            # Final ranking score
            c["ranking_score"] = (0.6 * c["similarity_score"]) + (0.4 * norm_stars)

        # Sort by ranking score
        candidate_repos.sort(key=lambda x: x.get("ranking_score", 0), reverse=True)
        chosen_strategy = "adapt_existing"

    # We emit 'pending_approval' to tell the frontend to show the Human Approval Modal
    # The actual execution will pause automatically because of interrupt_before=["scaffolder"]
    await publish_job_event(
        job_id,
        {
            "event_type": "agent_transition",
            "agent_name": "finder",
            "status": "pending_approval",
            "payload": {"candidates": candidate_repos},
        },
    )

    return {"candidate_repos": candidate_repos, "chosen_repo_strategy": chosen_strategy}
