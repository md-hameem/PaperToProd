"""
Sandbox Execution Service — accepts build/run requests from the Worker,
executes generated code in isolated containers, returns results.
"""

from fastapi import FastAPI

app = FastAPI(
    title="PaperToProd Sandbox Execution Service",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sandbox-svc"}


# TODO: POST /execute — build image, run smoke test, return stdout/stderr/exit code
