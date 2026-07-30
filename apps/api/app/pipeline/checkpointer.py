"""
AI Pipeline — LangGraph Checkpointer utilizing Postgres.
"""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import AsyncConnection

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.config import settings

# langgraph-checkpoint-postgres uses psycopg3, not asyncpg.
# We need to construct the standard postgresql URI from asyncpg URI if needed,
# but for local dev, settings.database_url usually has postgresql+asyncpg://
# We will replace +asyncpg with empty string for psycopg3.
psycopg_url = settings.database_url.replace("+asyncpg", "")


@asynccontextmanager
async def get_checkpointer():
    """Context manager yielding the LangGraph Postgres checkpointer."""
    async with AsyncConnectionPool(
        conninfo=psycopg_url,
        max_size=20,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
        },
    ) as pool:
        from typing import Any, cast

        pool_cast = cast("AsyncConnectionPool[AsyncConnection[dict[str, Any]]]", pool)
        checkpointer = AsyncPostgresSaver(pool_cast)

        # We need to ensure the checkpointer tables exist.
        # Calling setup() creates the required `checkpoints` and `checkpoint_writes` tables.
        # In production, this should be done via Alembic, but we rely on setup() here for MVP.
        await checkpointer.setup()

        yield checkpointer
