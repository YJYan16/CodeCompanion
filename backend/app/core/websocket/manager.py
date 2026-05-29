"""WebSocket 连接管理与事件广播。"""
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.user_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str | None = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if username:
            self.user_connections.setdefault(username, []).append(websocket)

    def disconnect(self, websocket: WebSocket, username: str | None = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if username and username in self.user_connections:
            conns = self.user_connections[username]
            if websocket in conns:
                conns.remove(websocket)
            if not conns:
                del self.user_connections[username]

    async def send_personal(self, username: str, event: str, data: Any):
        message = json.dumps({"event": event, "data": data}, ensure_ascii=False)
        for connection in self.user_connections.get(username, []):
            await connection.send_text(message)

    async def broadcast(self, event: str, data: Any):
        message = json.dumps({"event": event, "data": data}, ensure_ascii=False)
        stale: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


ws_manager = ConnectionManager()
