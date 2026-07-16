# Apps — Worker (Celery + LangGraph Orchestration)

The AI agent orchestration service that runs the LangGraph pipeline for each job.

## Agents

| Agent | Role |
|---|---|
| Extractor | Parse paper, extract structured methodology |
| Finder | Search & rank existing implementations |
| Scaffolder | Generate project scaffold & implementation code |
| DevOps | Containerization (Dockerfile, compose) |
| Reviewer | Validate, repair loop, compute Fidelity Score |
| Documentation Generator | Produce README & Fidelity Report |

## Structure

```
worker/
├── agents/
│   ├── __init__.py
│   ├── extractor.py        # Paper parsing & methodology extraction
│   ├── finder.py           # GitHub search & candidate ranking
│   ├── scaffolder.py       # Code generation
│   ├── devops.py           # Containerization
│   ├── reviewer.py         # Validation & repair loop
│   └── doc_generator.py    # README & Fidelity Report
│
├── graph/
│   ├── __init__.py
│   ├── pipeline.py         # LangGraph DAG definition
│   └── state.py            # JobState schema for the graph
│
├── prompts/
│   ├── extractor/
│   ├── finder/
│   ├── scaffolder/
│   ├── devops/
│   ├── reviewer/
│   └── doc_generator/
│
├── tools/
│   ├── __init__.py
│   ├── arxiv.py            # arXiv API client
│   ├── github_search.py    # GitHub search via App
│   ├── llm.py              # LLM provider wrapper with fallback
│   └── static_analysis.py  # Linter/import checker
│
├── tests/
│   └── __init__.py
│
├── celery_app.py            # Celery application config
├── tasks.py                 # Celery task definitions
├── Dockerfile
└── requirements.txt
```
