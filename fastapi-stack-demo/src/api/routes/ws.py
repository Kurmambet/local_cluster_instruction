import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.config import settings
from src.core.metrics import WS_ACTIVE

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)
        WS_ACTIVE.set(len(self.active))
        await self.broadcast_count()

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)
        WS_ACTIVE.set(len(self.active))

    async def broadcast_count(self) -> None:
        message = {"type": "active", "active": len(self.active)}
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                self.active.discard(ws)
        WS_ACTIVE.set(len(self.active))


manager = ConnectionManager()


@router.websocket("/ws/counter")
async def counter(ws: WebSocket) -> None:
    """Эхо + счётчик подключений. Раз в N секунд шлёт heartbeat, чтобы nginx не рвал
    «молчащее» соединение (proxy_read_timeout)."""
    await manager.connect(ws)
    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    ws.receive_text(), timeout=settings.ws_heartbeat_seconds
                )
            except TimeoutError:
                await ws.send_json({"type": "heartbeat"})
                continue
            await ws.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws)
        await manager.broadcast_count()
