"""
WebSocket connection manager utilizing Redis Pub/Sub.
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis

from app.config import settings

# Global Redis client for pub/sub
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


class ConnectionManager:
    """Manages WebSocket connections and Redis Pub/Sub subscriptions per job."""

    def __init__(self):
        # job_id -> list of active websockets
        self.active_connections: dict[int, list[WebSocket]] = {}
        # job_id -> asyncio.Task running the redis listener
        self.listeners: dict[int, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, job_id: int):
        """Accept a WebSocket connection and start listening to its channel."""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
            # Start a background task to listen to Redis for this job_id
            self.listeners[job_id] = asyncio.create_task(self._listen_to_redis(job_id))

        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: int):
        """Remove a WebSocket connection, cleanup listener if empty."""
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)

            if not self.active_connections[job_id]:
                # No more clients listening to this job
                del self.active_connections[job_id]
                listener = self.listeners.pop(job_id, None)
                if listener:
                    listener.cancel()

    async def _listen_to_redis(self, job_id: int):
        """Subscribe to a Redis channel and broadcast messages to all connected websockets."""
        channel_name = f"job_events:{job_id}"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel_name)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = message["data"]
                    # Broadcast to all connected clients for this job
                    websockets = self.active_connections.get(job_id, [])

                    # Create tasks to send concurrently, ignore errors from disconnected clients
                    tasks = []
                    for ws in websockets:
                        tasks.append(ws.send_text(payload))

                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()


# Global manager instance
manager = ConnectionManager()


async def publish_job_event(job_id: int, event_data: dict[str, Any]):
    """Publish an event to Redis. This will be called by Celery workers."""
    channel_name = f"job_events:{job_id}"
    await redis_client.publish(channel_name, json.dumps(event_data))
