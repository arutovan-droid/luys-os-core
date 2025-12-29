from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Dict


class Source(str, Enum):
    OPERATOR = "operator"
    LATP = "latp"
    RESONANCE = "resonance"
    LIBRARIUM = "librarium"


@dataclass(frozen=True)
class ResonancePacket:
    payload: Any
    psl_id: str
    psl_tag: str            # "[FACT]" | "[HYP]" | "[ROLLBACK]"
    timestamp: datetime
    source: Source
    resonance_score: float  # 0.0..1.0
    meta: Dict[str, Any]


class DecisionType(str, Enum):
    DIRECT_PASS = "direct_pass"
    SUGGEST = "suggest"
    HOLD = "hold"
    QUEUE_ROLLBACK = "queue_rollback"
    DROP = "drop"


@dataclass(frozen=True)
class Decision:
    type: DecisionType
    payload: Optional[Any] = None
    reason: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
