from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WuWeiPolicy:
    resonance_threshold: float = 0.95
    quiet_hours_start: int = 22
    quiet_hours_end: int = 6

    def is_quiet_hour(self, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        h = now.hour
        return h >= self.quiet_hours_start or h < self.quiet_hours_end
