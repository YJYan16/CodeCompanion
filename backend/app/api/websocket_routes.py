from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth import decode_token
from app.core.utils.logging_config import get_logger
from app.core.websocket.manager import ws_manager

router = APIRouter(tags=["websocket"])
logger = get_logger("websocket")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    username = None
    if token:
        try:
            payload = decode_token(token)
            username = payload.get("sub")
        except Exception:
            await websocket.close(code=4001)
            return

    await ws_manager.connect(websocket, username)
    logger.info("WebSocket connected: %s", username or "anonymous")

    try:
        await websocket.send_json(
            {"event": "connected", "data": {"username": username}}
        )
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event":"pong","data":{}}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, username)
        logger.info("WebSocket disconnected: %s", username or "anonymous")
