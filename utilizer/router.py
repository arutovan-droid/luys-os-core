from __future__ import annotations

import re
from dataclasses import dataclass

from .types import Mode

@dataclass(frozen=True)
class RouteDecision:
    mode: Mode
    reason: str

_DIRECT_TRIGGERS = [
    r"^\s*сколько\s",
    r"^\s*переведи\s",
    r"^\s*что\s+значит\s",
    r"^\s*как\s+перевести\s",
    r"^\s*\d+\s*[\+\-\*/]\s*\d+",
]

_FULL_TRIGGERS = [
    r"\b(контракт|psl)\b",
    r"\b(глубже|полный режим|full)\b",
    r"\b(утилизатор|utilizer)\b",
]

_MINI_TRIGGERS = [
    r"\b(скучно|апат|пусто|не хочу ничего|нет сил)\b",
    r"\b(тревог|паник|страх)\b",
    r"\b(обида|злость|конфликт)\b",
    r"\b(докажи|опровергни|бог|смысл)\b",
]

def decide_mode(user_text: str) -> RouteDecision:
    t = user_text.strip().lower()

    for p in _FULL_TRIGGERS:
        if re.search(p, t, flags=re.IGNORECASE):
            return RouteDecision(mode=Mode.FULL, reason="explicit_full_trigger")

    for p in _DIRECT_TRIGGERS:
        if re.search(p, t, flags=re.IGNORECASE):
            return RouteDecision(mode=Mode.DIRECT, reason="direct_trigger")

    for p in _MINI_TRIGGERS:
        if re.search(p, t, flags=re.IGNORECASE):
            return RouteDecision(mode=Mode.MINI, reason="mini_trigger")

    return RouteDecision(mode=Mode.MINI, reason="default_mini")
