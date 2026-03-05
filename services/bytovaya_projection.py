from __future__ import annotations

import re
from typing import Dict

# Minimal бытовой словарь. Расширишь позже.
_REPLACEMENTS: Dict[str, str] = {
    r"\bPSL-mini\b": "короткая договорённость",
    r"\bPSL\b": "договорённость",
    r"\bконтракт\b": "договорённость",
    r"\bconstraints\b": "ограничения",
    r"\bsuccess_signal\b": "как поймём, что стало лучше",
    r"\bROLLBACK\b": "если не сработает (откат)",
    r"\bHYP\b": "предположение",
    r"\bFACT\b": "факт",
    r"\bКристалл\b": "узелок на память",
    r"\bDistill\b": "суть",
    r"\bResonance\b": "вопросы на прояснение",
}

def project(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return text

    out = text
    for pat, rep in _REPLACEMENTS.items():
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)

    # чуть-чуть “человечнее” заголовки
    out = out.replace("Суть:", "По сути:")
    out = out.replace("Вопрос:", "Вопрос на уточнение:")
    out = out.replace("Вопросы:", "Вопросы на уточнение:")
    out = out.replace("Делаем сейчас:", "Что делаем сейчас:")
    out = out.replace("Фиксируем опыт:", "Запишем себе на будущее:")

    return out
