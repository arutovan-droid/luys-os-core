from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional


class EventLog:
    """Ring buffer of last N events (in-memory)."""

    def __init__(self, capacity: int = 200):
        self._buf: Deque[Dict[str, Any]] = deque(maxlen=capacity)

    def append(self, event: Dict[str, Any]) -> None:
        # ensure timestamp
        if "ts" not in event:
            event = {**event, "ts": datetime.now().isoformat()}
        self._buf.append(event)

    def tail(self, n: int = 40, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        items = list(self._buf)
        if operator_id:
            items = [e for e in items if e.get("operator_id") == operator_id]
        return items[-max(1, n):]


EVENT_LOG = EventLog(capacity=400)
