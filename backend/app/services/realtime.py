import asyncio
from collections import defaultdict

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)
        self.loop = None

    def set_loop(self, loop):
        self.loop = loop

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        self.connections[user_id].discard(websocket)
        if not self.connections[user_id]:
            self.connections.pop(user_id, None)

    async def publish(self, user_ids: set[int], event: dict):
        stale = []
        for user_id in user_ids:
            for websocket in self.connections.get(user_id, set()).copy():
                try:
                    await websocket.send_json(event)
                except Exception:
                    stale.append((user_id, websocket))
        for user_id, websocket in stale:
            self.disconnect(user_id, websocket)

    def publish_nowait(self, user_ids: set[int], event: dict):
        if self.loop is None:
            return
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None
        if running_loop is self.loop:
            running_loop.create_task(self.publish(user_ids, event))
        else:
            asyncio.run_coroutine_threadsafe(self.publish(user_ids, event), self.loop)


hub = RealtimeHub()