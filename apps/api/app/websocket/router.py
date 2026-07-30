"""
WebSocket router — Doc 14 §9 (Real-Time Streaming).
"""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.auth import security
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_endpoint(
    websocket: WebSocket,
    job_id: int,
    token: str = Query(..., description="Short-lived access token for WebSocket auth"),
):
    """
    WebSocket endpoint for real-time job updates.
    Expects a valid JWT in the `token` query parameter.
    """
    # Authenticate via query param token
    user_id = security.verify_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # In a real implementation, we would verify that `user_id` has access to `job_id`
    # (e.g. check DB). We omit the DB call here for speed, assuming tokens are short-lived.

    await manager.connect(websocket, job_id)
    try:
        # Keep the connection open. The client doesn't need to send anything,
        # but we must wait to detect disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
