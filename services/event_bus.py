from __future__ import annotations

import asyncio
from typing import Any, Dict, Set

from services.event_log import EVENT_LOG


class EventBus:
    """Fan-out bus: each subscriber gets every event (async queues)."""

    def __init__(self):
        self._subs: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    async def publish(self, event: Dict[str, Any]) -> None:
        # Always store in event tail
        EVENT_LOG.append(event)

        # Non-blocking fan-out (drop if subscriber queue is full)
        dead = []
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # drop for this subscriber
                pass
            except Exception:
                dead.append(q)

        for q in dead:
            self.unsubscribe(q)


BUS = EventBus()
