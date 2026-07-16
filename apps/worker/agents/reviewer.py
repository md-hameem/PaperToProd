"""
Reviewer Agent — Validation, repair loop, and Fidelity Score computation.

State machine: build → run_smoke_test → (pass → fidelity_score → done) |
               (fail → diagnose_error → route_to_responsible_agent → rebuild)
Bounded at max_retries (default 5).

Outputs: validation.attempt_count, .last_error, .fidelity_score, .per_component_status[]
"""

# TODO: Implement sandboxed execution, error classification, repair routing, fidelity scoring
