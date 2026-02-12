from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal


Scope = Literal["unverified_hyp", "emotional_buffer", "external_contamination"]


@dataclass
class RollbackItem:
    operator_id: str
    psl_id: str
    trigger: str
    scope: Scope
    created_at: str


class RollbackService:
    def __init__(self) -> None:
        self._queue: List[RollbackItem] = []

    def queue_rollback_check(
        self,
        operator_id: str,
        psl_id: str,
        trigger: str = "hrr_violation",
        scope: Scope = "unverified_hyp",
    ) -> None:
        self._queue.append(
            RollbackItem(
                operator_id=operator_id,
                psl_id=psl_id,
                trigger=trigger,
                scope=scope,
                created_at=datetime.now().isoformat(),
            )
        )

    def pending_count(self) -> int:
        return len(self._queue)

    def list_pending(self, operator_id: str) -> List[Dict]:
        items = [x for x in self._queue if x.operator_id == operator_id]
        return [
            {
                "psl_id": x.psl_id,
                "trigger": x.trigger,
                "scope": x.scope,
                "created_at": x.created_at,
            }
            for x in items
        ]

    async def execute_rollback(self, operator_id: str) -> int:
        before = len(self._queue)
        self._queue = [x for x in self._queue if x.operator_id != operator_id]
        after = len(self._queue)
        return before - after


ROLLBACK = RollbackService()
