from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class Source(str, Enum):
    operator = "operator"
    latp = "latp"
    resonance = "resonance"
    librarium = "librarium"


class DecisionType(str, Enum):
    DIRECT_PASS = "direct_pass"
    SYMBIOTIC_SUGGESTION = "symbiotic_suggestion"
    QUEUE_ROLLBACK = "queue_rollback"
    DROP = "drop"


@dataclass
class ResonancePacket:
    payload: Any
    psl_id: str
    psl_tag: str
    timestamp: datetime
    source: Source
    resonance_score: float
    meta: Dict[str, Any]


@dataclass
class Decision:
    type: str
    payload: Any = None
    reason: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
