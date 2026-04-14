import json
from collections import defaultdict
from typing import Any, DefaultDict, Set

from starlette.websockets import WebSocket, WebSocketState


class NotificationHub:
    """In-memory подписчики по user_id (один процесс)."""

    def __init__(self) -> None:
        self._by_user: DefaultDict[int, Set[WebSocket]] = defaultdict(set)

    def register(self, user_id: int, ws: WebSocket) -> None:
        self._by_user[user_id].add(ws)

    def unregister(self, user_id: int, ws: WebSocket) -> None:
        conns = self._by_user.get(user_id)
        if not conns:
            return
        conns.discard(ws)
        if not conns:
            del self._by_user[user_id]

    async def send_json_to_user(self, user_id: int, message: dict[str, Any]) -> None:
        conns = list(self._by_user.get(user_id, ()))
        raw = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(raw)
                else:
                    dead.append(ws)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister(user_id, ws)


hub = NotificationHub()
