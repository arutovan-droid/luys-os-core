from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List

from services.event_bus import BUS


class RollbackScope(str, Enum):
    EMOTIONAL_NOISE = "emotional_buffer"
    COGNITIVE_HALLUCINATION = "unverified_hyp"
    EXTERNAL_CONTAMINATION = "unauthorized_authority_claims"


@dataclass(frozen=True)
class RollbackItem:
    operator_id: str
    psl_id: str
    trigger: str
    scope: RollbackScope
    created_at: datetime
    payload: Optional[Dict[str, Any]] = None


class RollbackService:
    def __init__(self) -> None:
        self._queue: List[RollbackItem] = []
        self._last_report: Dict[str, Any] | None = None

    def queue_rollback_check(self, item: RollbackItem) -> None:
        self._queue.append(item)

    def pending_count(self) -> int:
        return len(self._queue)

    async def execute_rollback(self, operator_id: str) -> int:
        before = len(self._queue)
        self._queue = [x for x in self._queue if x.operator_id != operator_id]
        deleted = before - len(self._queue)

        self._last_report = {
            "type": "rollback_report",
            "operator_id": operator_id,
            "deleted": deleted,
            "timestamp": datetime.now().isoformat()
        }
        await BUS.publish(self._last_report)
        return deleted

    async def schedule_daily(self, operator_id: str, hour: int = 4) -> None:
        while True:
            now = datetime.now()
            next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)

            await asyncio.sleep((next_run - now).total_seconds())
            await self.execute_rollback(operator_id)


ROLLBACK = RollbackService()
