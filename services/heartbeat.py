from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from services.event_bus import BUS
from services.rollback_service import ROLLBACK


class HeartbeatService:
    def __init__(self, interval_sec: float = 5.0):
        self.interval_sec = interval_sec
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        # Start once (idempotent)
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            # We publish minimal "system_status"
            await BUS.publish(
                {
                    "type": "system_status",
                    "ts": datetime.now().isoformat(),
                    "rollback_queue": ROLLBACK.pending_count(),
                    "ws_subscribers": getattr(BUS, "_subs", None) and len(BUS._subs) or 0,
                }
            )
            await asyncio.sleep(self.interval_sec)


HEARTBEAT = HeartbeatService(interval_sec=5.0)
