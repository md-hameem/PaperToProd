import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_job_missing_args():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post(
            "/jobs", headers={"x-workspace-id": "1", "Authorization": "Bearer mock"}
        )
        # We expect a 422 because neither file nor arxiv_url was provided
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_job_success():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/jobs",
            data={"arxiv_id": "2103.00020"},
            headers={"x-workspace-id": "1", "Authorization": "Bearer mock"},
        )
        # Note: In a real test we would mock the DB and Auth dependencies
        # This is a structural representation for Phase 2.17
        pass
