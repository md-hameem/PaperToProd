"""
LLM Provider Wrapper — Unified interface with automatic fallback chain.

Primary: Claude (Anthropic) for extraction & generation
Fallback: OpenAI on primary-provider outage/rate-limit
Cheap: GPT-4o-mini for low-stakes sub-tasks
"""

# TODO: Implement unified LLM call wrapper, model routing, fallback logic, token tracking
