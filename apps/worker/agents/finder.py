"""
Finder Agent — Searches and ranks existing implementations.

Uses GitHub Search API (via platform GitHub App) and embedding-based
similarity ranking (Qdrant) to find the best existing implementation.

Outputs: candidate_repos[], chosen_repo_strategy
"""

# TODO: Implement GitHub search, ranking, cross-job cache, human approval checkpoint
