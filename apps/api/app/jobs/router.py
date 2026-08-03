"""
Jobs module — API routes for job lifecycle (create, list, get, cancel, events, artifacts).
See Doc 14 for the full API specification.
"""

import asyncio
import os
import re
import shutil

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_workspace_role
from app.auth.router import get_current_user
from app.database import get_db
from app.jobs import service
from app.jobs.schemas import (
    ArtifactDownloadResponse,
    JobCreateResponse,
    JobDetailResponse,
    JobEventResponse,
    JobEventsListResponse,
    JobListResponse,
    JobSummaryResponse,
)
from app.models import User, WorkspaceMember, WorkspaceRole
from app.websocket.manager import redis_client

router = APIRouter()


async def fetch_arxiv_metadata(arxiv_id: str) -> dict:
    """Mock fetching metadata from arXiv API."""
    # Simulate network delay
    await asyncio.sleep(0.5)

    # Mock data for demonstration purposes
    if "9999.99999" in arxiv_id:
        return {"title": "WITHDRAWN: A Fake Paper", "summary": "This paper has been withdrawn."}
    if "survey" in arxiv_id.lower() or "review" in arxiv_id.lower():
        return {
            "title": "A Comprehensive Survey on LLMs",
            "summary": "We review recent advances...",
        }

    return {
        "title": "Attention Is All You Need",
        "summary": "We propose a new network architecture...",
    }


@router.post("", response_model=JobCreateResponse, status_code=201)
async def create_job(
    file: UploadFile | None = File(None),
    arxiv_url: str | None = Form(None),
    arxiv_id: str | None = Form(None),
    focus_scope: str | None = Form(None),
    framework_override: str | None = Form(None),
    github_auto_push: bool = Form(False),
    x_workspace_id: int = Header(...),
    current_user: User = Depends(get_current_user),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Create a new paper reproduction job."""
    if not file and not arxiv_url and not arxiv_id:
        raise HTTPException(
            status_code=422,
            detail="Must provide either a PDF file, an arxiv_url, or an arxiv_id.",
        )

    # Use arXiv URL or ID if provided
    paper_url = arxiv_url or arxiv_id or ""

    if arxiv_id or (arxiv_url and "arxiv.org" in arxiv_url):
        # Extract ID if URL is provided
        a_id = arxiv_id if arxiv_id else re.search(r"arxiv\.org/(?:abs|pdf)/(\d+\.\d+)", arxiv_url)
        if hasattr(a_id, "group"):
            a_id = a_id.group(1)

        if a_id:
            metadata = await fetch_arxiv_metadata(a_id)
            title = metadata["title"].upper()
            summary = metadata["summary"].upper()

            if "WITHDRAWN" in title or "WITHDRAWN" in summary:
                raise HTTPException(
                    status_code=422,
                    detail="Cannot process withdrawn papers.",
                )

            if "SURVEY" in title or "REVIEW" in title or "POSITION" in title:
                raise HTTPException(
                    status_code=422,
                    detail="PaperToProd does not support survey or position papers.",
                )

    if file and file.filename:
        paper_url = file.filename

        # Security Hardening (Phase 2.15): Malicious PDF detection
        content = await file.read()
        await file.seek(0)

        # Known adversarial payload signature mock
        if b"prompt_injection_payload" in content or b"MaliciousAction" in content:
            raise HTTPException(
                status_code=400,
                detail="Security Violation: Malicious payload detected in PDF file.",
            )

    job = await service.create_job(
        db=db,
        user_id=current_user.id,
        workspace_id=x_workspace_id,
        paper_url=paper_url,
        advanced_options={
            "focus_scope": focus_scope,
            "framework_override": framework_override,
            "github_auto_push": github_auto_push,
        },
    )

    if file:
        # Save file to local storage (stub for MinIO/S3)
        storage_dir = f"storage/jobs/{job.id}"
        os.makedirs(storage_dir, exist_ok=True)
        file_path = f"{storage_dir}/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update job paper source URL to the local path
        job.paper_source_url = f"local:{file_path}"
        await db.commit()

    return JobCreateResponse(id=job.id, status=job.status)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    cursor: str | None = Query(None, description="Pagination cursor (ISO datetime)"),
    limit: int = Query(20, ge=1, le=100),
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """List jobs for the current workspace with cursor-based pagination."""
    jobs, next_cursor = await service.list_jobs(
        db=db,
        workspace_id=x_workspace_id,
        cursor=cursor,
        limit=limit,
    )
    return JobListResponse(
        items=[JobSummaryResponse.model_validate(j) for j in jobs],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: int,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Get full job state snapshot."""
    job = await service.get_job(db=db, job_id=job_id, workspace_id=x_workspace_id)
    return JobDetailResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobDetailResponse)
async def cancel_job(
    job_id: int,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running or queued job."""
    job = await service.cancel_job(db=db, job_id=job_id, workspace_id=x_workspace_id)
    return JobDetailResponse.model_validate(job)


@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: int,
    request: Request,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Stream full job execution logs via SSE or return JSON."""
    # Verify job exists
    await service.get_job(db=db, job_id=job_id, workspace_id=x_workspace_id)

    accept_header = request.headers.get("accept", "")

    if "text/event-stream" in accept_header:

        async def event_generator():
            # 1. Fetch historical events
            events = await service.get_job_events(
                db=db,
                job_id=job_id,
                workspace_id=x_workspace_id,
                since_sequence=0,
            )
            for event in events:
                # Convert ORM model to dictionary then JSON string
                payload = JobEventResponse.model_validate(event).model_dump_json()
                yield f"data: {payload}\n\n"

            # 2. Subscribe to Redis for live events
            channel_name = f"job_events:{job_id}"
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(channel_name)

            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield f"data: {message['data']}\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Mock log retrieval from storage for standard JSON request
    log_path = f"storage/jobs/{job_id}/logs/full.log"
    if os.path.exists(log_path):
        with open(log_path) as f:
            return {"logs": f.read()}

    return {"logs": "[System] Logs are pending or do not exist yet."}


class ApproveRequest(BaseModel):
    repo_url: str


@router.post("/{job_id}/approve")
async def approve_job(
    job_id: int,
    payload: ApproveRequest,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Approve a candidate repository and resume LangGraph."""
    # Verify job exists
    await service.get_job(db=db, job_id=job_id, workspace_id=x_workspace_id)

    # Trigger Celery task to resume
    from app.worker import resume_pipeline

    resume_pipeline.delay(job_id, payload.repo_url)

    return {"status": "resumed", "job_id": job_id, "approved_repo": payload.repo_url}


@router.get("/{job_id}/events", response_model=JobEventsListResponse)
async def get_job_events(
    job_id: int,
    since_sequence: int = Query(0, ge=0, description="Return events after this sequence number"),
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Get job events for reconnection replay."""
    events = await service.get_job_events(
        db=db,
        job_id=job_id,
        workspace_id=x_workspace_id,
        since_sequence=since_sequence,
    )
    return JobEventsListResponse(
        events=[JobEventResponse.model_validate(e) for e in events],
        latest_sequence=events[-1].sequence if events else since_sequence,
    )


class PushToGithubRequest(BaseModel):
    repository_name: str


@router.post("/{job_id}/artifacts/push-to-github")
async def push_to_github(
    job_id: int,
    payload: PushToGithubRequest,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER])
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Mock endpoint to push artifacts to GitHub.
    Verifies workspace integration and simulates a push.
    """
    # 1. Verify job belongs to workspace
    job = await service.get_job(db, job_id, x_workspace_id)
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Can only push completed jobs")

    # 2. Verify workspace has GitHub integrated
    from app.models import Workspace

    ws_result = await db.execute(select(Workspace).where(Workspace.id == x_workspace_id))
    ws = ws_result.scalar_one_or_none()

    if not ws or not ws.github_installation_id:
        raise HTTPException(status_code=400, detail="GitHub is not integrated for this workspace")

    # 3. Simulate Push
    import asyncio

    await asyncio.sleep(2)  # Simulate work

    return {
        "status": "success",
        "repository_url": f"https://github.com/{ws.github_account_name}/{payload.repository_name}",
        "message": f"Successfully pushed to {ws.github_account_name}/{payload.repository_name}",
    }


@router.get("/{job_id}/artifacts/repository", response_model=ArtifactDownloadResponse)
async def get_repository_download(
    job_id: int,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Get a signed download URL for the generated repository archive."""
    # Verify job exists and is owned by workspace
    job = await service.get_job(db=db, job_id=job_id, workspace_id=x_workspace_id)

    # TODO: Generate signed MinIO URL
    return ArtifactDownloadResponse(
        download_url=f"/storage/jobs/{job.id}/repository.zip",
        artifact_type="repository_zip",
        size_bytes=None,
        expires_in_seconds=3600,
    )


@router.get("/health")
async def jobs_health():
    return {"status": "ok", "module": "jobs"}


@router.get("/{job_id}/artifacts/tree")
async def get_artifact_tree(
    job_id: int,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Return a mock file tree of the generated repository."""
    await service.get_job(db=db, job_id=job_id, workspace_id=x_workspace_id)

    return {
        "name": "repository",
        "type": "directory",
        "children": [
            {
                "name": "src",
                "type": "directory",
                "children": [
                    {
                        "name": "model.py",
                        "type": "file",
                        "path": "src/model.py",
                        "has_annotations": True,
                    },
                    {
                        "name": "train.py",
                        "type": "file",
                        "path": "src/train.py",
                        "has_annotations": False,
                    },
                    {
                        "name": "utils.py",
                        "type": "file",
                        "path": "src/utils.py",
                        "has_annotations": False,
                    },
                ],
            },
            {
                "name": "tests",
                "type": "directory",
                "children": [
                    {
                        "name": "test_model.py",
                        "type": "file",
                        "path": "tests/test_model.py",
                        "has_annotations": True,
                    },
                ],
            },
            {
                "name": "requirements.txt",
                "type": "file",
                "path": "requirements.txt",
                "has_annotations": False,
            },
            {"name": "README.md", "type": "file", "path": "README.md", "has_annotations": False},
        ],
    }


@router.get("/{job_id}/artifacts/file")
async def get_artifact_file(
    job_id: int,
    path: str,
    x_workspace_id: int = Header(...),
    membership: WorkspaceMember = Depends(require_workspace_role()),
    db: AsyncSession = Depends(get_db),
):
    """Return mock content and annotations for a specific file."""
    await service.get_job(db=db, job_id=job_id, workspace_id=x_workspace_id)

    if path == "src/model.py":
        content = (
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class VisionTransformer(nn.Module):\n"
            "    def __init__(self, embed_dim=768, num_heads=12):\n"
            "        super().__init__()\n"
            "        # Layer normalization before the self-attention block\n"
            "        self.norm1 = nn.LayerNorm(embed_dim)\n"
            "        self.attn = nn.MultiheadAttention(embed_dim, num_heads)\n"
            "        self.norm2 = nn.LayerNorm(embed_dim)\n"
            "        self.mlp = nn.Sequential(\n"
            "            nn.Linear(embed_dim, embed_dim * 4),\n"
            "            nn.GELU(),\n"
            "            nn.Linear(embed_dim * 4, embed_dim)\n"
            "        )\n\n"
            "    def forward(self, x):\n"
            "        x = x + self.attn(self.norm1(x))[0]\n"
            "        x = x + self.mlp(self.norm2(x))\n"
            "        return x\n"
        )
        annotations = [
            {
                "line": 6,
                "paper_text": "We apply Layer Normalization (LN) before every block, and residual connections after every block (Wang et al., 2019; Ba et al., 2016).",
                "section": "3.1 Vision Transformer (ViT)",
            },
            {
                "line": 15,
                "paper_text": "The MLP contains two layers with a GELU non-linearity.",
                "section": "3.1 Vision Transformer (ViT)",
            },
        ]
    elif path == "src/train.py":
        content = "print('Training script coming soon...')\n"
        annotations = []
    elif path == "src/utils.py":
        content = "def set_seed(seed=42):\n    pass\n"
        annotations = []
    elif path == "tests/test_model.py":
        content = (
            "import torch\n"
            "import pytest\n"
            "from src.model import VisionTransformer\n\n"
            "def test_vit_shape():\n"
            "    model = VisionTransformer(embed_dim=768, num_heads=12)\n"
            "    x = torch.randn(2, 197, 768)\n"
            "    out = model(x)\n"
            "    assert out.shape == (2, 197, 768), f'Expected shape (2, 197, 768), got {out.shape}'\n\n"
            "def test_vit_smoke():\n"
            "    model = VisionTransformer()\n"
            "    # Basic forward pass to ensure no runtime errors\n"
            "    x = torch.randn(1, 197, 768)\n"
            "    try:\n"
            "        model(x)\n"
            "    except Exception as e:\n"
            "        pytest.fail(f'Forward pass failed with exception: {e}')\n"
        )
        annotations = [
            {
                "line": 8,
                "paper_text": "The standard sequence length is 196 patches plus 1 class token (197), and the embedding dimension is 768 for ViT-Base.",
                "section": "3.1 Vision Transformer (ViT)",
            },
        ]
    elif path == "requirements.txt":
        content = "torch>=2.0.0\nnumpy>=1.24.0\n"
        annotations = []
    elif path == "README.md":
        content = "# Generated Project\n\nThis project was generated by PaperToProd.\n"
        annotations = []
    else:
        raise HTTPException(status_code=404, detail="File not found")

    return {"content": content, "annotations": annotations}
