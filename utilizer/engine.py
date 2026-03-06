from __future__ import annotations

import re
from dataclasses import replace
from typing import Optional

from .sources_loader import UtilizerSources, crystals_index
from .types import Mode, Phase, SessionState


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-zА-Яа-яЁё0-9\-]+", text.strip())


def _one_line(text: str, max_words: int = 22) -> str:
    w = _words(text)
    if not w:
        return ""
    return " ".join(w[:max_words]) + ("…" if len(w) > max_words else "")


def _distill(user_text: str) -> str:
    low = user_text.lower()
    if any(k in low for k in ["скучно", "апат", "пусто", "нет сил"]):
        return "Суть: это похоже на просадку вовлечённости (внимания или смысла), а не на запрос развлечений."
    return f"Суть: {_one_line(user_text, 18)}"


def _questions(distill: str) -> list[str]:
    low = distill.lower()
    if "вовлеч" in low or "скук" in low:
        return ["Скучно — это ум без дела или дело без смысла?"]
    return ["Что ты хочешь получить в результате одним предложением?"]


def _psl_mini(user_text: str, distill: str, user_answer: Optional[str]) -> str:
    facts = [f"- {_one_line(user_text, 18)}"]
    if user_answer:
        facts.append(f"- Ответ: {_one_line(user_answer, 18)}")
    return "\n".join([
        "[FACT]",
        *facts,
        "",
        "[HYP]",
        f"- {_one_line(distill.replace('Суть:', '').strip(), 18)}",
        "",
        "constraints",
        "- время: 5–10 минут",
        "- ресурсы: то, что рядом; без скролла",
        "",
        "[ROLLBACK]",
        "- если за 2 минуты нет прогресса → уменьшаем шаг в 10 раз или меняем ветку",
        "",
        "success_signal",
        "- появилось хоть немного любопытства/энергии и следующий шаг",
    ])


def _execution(distill: str, mode: Mode) -> list[str]:
    low = distill.lower()
    if "скук" in low or "вовлеч" in low:
        steps = [
            "Выбери предмет рядом и назови его.",
            "Найди одну странную деталь и опиши её.",
            "Сформулируй 3 вопроса к этой детали.",
        ]
    else:
        steps = ["Сформулируй цель одним предложением.", "Назови 1 ограничение.", "Сделай шаг на 5 минут."]
    return steps[:1] if mode == Mode.MINI else steps[:3]


def _pick_crystal(distill: str, crystals: dict[str, dict]) -> Optional[str]:
    low = distill.lower()
    if ("скук" in low or "вовлеч" in low) and "crystal.hunt_anomalies.v1" in crystals:
        return "crystal.hunt_anomalies.v1"
    return next(iter(crystals.keys()), None)


def _crystal_text(crystal: dict) -> str:
    name = crystal.get("name", "Кристалл")
    steps = crystal.get("steps", [])
    lines = [f"**Кристалл: {name}**", "3 шага:"]
    for i, s in enumerate(steps[:3], 1):
        lines.append(f"{i}) {s}")
    return "\n".join(lines)


class UtilizerEngine:
    def __init__(self, sources: UtilizerSources) -> None:
        self.sources = sources
        self.crystals = crystals_index(sources.crystals)

    def process(self, user_text: str, state: SessionState, mode: Mode) -> tuple[str, SessionState]:
        st = replace(state, last_user_answer=user_text)

        if st.phase == Phase.DISTILL:
            dist = _distill(user_text)
            q = _questions(dist)
            st2 = replace(st, phase=Phase.RESONANCE, distill=dist, resonance_questions=q)
            msg = "\n".join([dist, "", "Вопрос:", "1) " + q[0]])
            return msg, st2

        if st.phase == Phase.RESONANCE:
            dist = st.distill or _distill(user_text)
            st2 = replace(st, phase=Phase.PSL)
            msg = "\n".join([dist, "", "Ок. Ответь 1–2 фразами, и я оформлю контракт (PSL-mini)."])
            return msg, st2

        if st.phase == Phase.PSL:
            dist = st.distill or _distill(user_text)
            psl = _psl_mini(user_text=user_text, distill=dist, user_answer=user_text)
            st2 = replace(st, phase=Phase.EXECUTION, psl_contract=psl)
            msg = "\n".join(["PSL-mini:", "", psl])
            return msg, st2

        if st.phase == Phase.EXECUTION:
            dist = st.distill or _distill(user_text)
            steps = _execution(dist, mode)
            st2 = replace(st, phase=Phase.LIBRARIUM, execution_steps=steps)
            msg = "Делаем сейчас:\n" + "\n".join([f"{i}) {s}" for i, s in enumerate(steps, 1)])
            return msg, st2

        if st.phase == Phase.LIBRARIUM:
            dist = st.distill or _distill(user_text)
            cid = _pick_crystal(dist, self.crystals)
            crystal = self.crystals.get(cid or "", {})
            ctext = _crystal_text(crystal) if crystal else "**Кристалл:** зафиксируй паттерн и повтори завтра."
            st2 = replace(st, phase=Phase.DONE, crystal_id=cid, crystal_text=ctext)
            msg = "Фиксируем опыт:\n\n" + ctext
            return msg, st2

        return "Сеанс завершён.", replace(st, phase=Phase.DONE)
