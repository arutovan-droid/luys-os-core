from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Optional


class Phase(str, Enum):
    DISTILL = "DISTILL"
    RESONANCE = "RESONANCE"
    PSL = "PSL"
    EXECUTION = "EXECUTION"
    LIBRARIUM = "LIBRARIUM"
    DONE = "DONE"


class Mode(str, Enum):
    DIRECT = "DIRECT"
    MINI = "MINI_UTILIZER"
    FULL = "FULL_UTILIZER"


@dataclass
class SessionState:
    phase: Phase = Phase.DISTILL
    distill: Optional[str] = None
    resonance_questions: list[str] = field(default_factory=list)
    psl_contract: Optional[str] = None
    execution_steps: list[str] = field(default_factory=list)
    crystal_id: Optional[str] = None
    crystal_text: Optional[str] = None

    last_user_answer: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)
