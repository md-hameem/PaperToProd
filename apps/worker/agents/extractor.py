"""
Extractor Agent — Parses paper structure and produces structured methodology.

Multi-pass extraction:
  Pass 1: Structured outline (architecture, training procedure, evaluation)
  Pass 2: Hyperparameter/config value extraction
  Pass 3: Self-critique against abstract/conclusion for omissions

Outputs: methodology.components[] with confidence scores, methodology.gaps[]
"""

# TODO: Implement multi-pass extraction with domain-specific prompts
