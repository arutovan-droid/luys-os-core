from __future__ import annotations

from typing import Any, Optional

from services.event_bus import BUS
from services.rollback_service import ROLLBACK

from .models import Decision, DecisionType, ResonancePacket

# --- Utilizer hook (lightweight; does not change WuWei's gatekeeping role) ---
from pathlib import Path
from utilizer.router import decide_mode
from utilizer.types import SessionState, Phase
from utilizer.sources_loader import load_sources
from utilizer.engine import UtilizerEngine


def _extract_text(payload: Any) -> Optional[str]:
    """
    Best-effort extraction of user-facing text from payload.
    Supports:
      - str
      - dict with common keys: text/message/content/response
    """
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for k in ("text", "message", "content", "response", "answer", "output"):
            v = payload.get(k)
            if isinstance(v, str) and v.strip():
                return v
    return None


def _inject_text(payload: Any, new_text: str) -> Any:
    """
    Best-effort injection:
      - if payload is str -> return str
      - if dict -> put into 'text' (and preserve others)
      - else -> wrap into dict
    """
    if isinstance(payload, str) or payload is None:
        return new_text
    if isinstance(payload, dict):
        out = dict(payload)
        out["text"] = new_text
        return out
    return {"text": new_text, "original_payload": payload}


class WuWeiEngine:
    """
    MVP:
    - [FACT] + score==1.0 => direct_pass + event
    - [HYP] + score<1.0   => queue_rollback + event
    - score>=0.95         => symbiotic_suggestion (заглушка) + event
    - else                => drop
    """

    def __init__(self, operator_id: str, resonance_threshold: float = 0.95) -> None:
        self.operator_id = operator_id
        self.resonance_threshold = resonance_threshold

        # Utilizer initialized once
        repo_root = Path(__file__).resolve().parents[2]  # luys-os-core/
        sources = load_sources(repo_root)
        self.utilizer = UtilizerEngine(sources)

    async def process(self, packet: ResonancePacket) -> Optional[Decision]:
        tag = packet.psl_tag.strip()

        # [HYP] без идеального резонанса -> очередь отката
        if tag == "[HYP]" and packet.resonance_score < 1.0:
            ROLLBACK.queue_rollback_check(
                operator_id=self.operator_id,
                psl_id=packet.psl_id,
                trigger="hrr_violation",
                scope="unverified_hyp",
            )
            await BUS.publish(
                {
                    "type": "hrr_update",
                    "operator_id": self.operator_id,
                    "score": packet.resonance_score,
                    "psl_id": packet.psl_id,
                    "tag": tag,
                    "action": "queued_for_rollback",
                }
            )
            return Decision(type=DecisionType.QUEUE_ROLLBACK.value, reason="HYP<1.0 queued")

        # [FACT] + HRR=1.0 -> прямой пропуск
        if tag == "[FACT]" and packet.resonance_score == 1.0:
            await BUS.publish(
                {
                    "type": "hrr_update",
                    "operator_id": self.operator_id,
                    "score": 1.0,
                    "psl_id": packet.psl_id,
                    "tag": tag,
                    "action": "direct_pass",
                }
            )

            # --- Utilizer projection (non-breaking) ---
            txt = _extract_text(packet.payload)
            if txt:
                decision = decide_mode(txt)
                # store state per conversation if exists; fallback to fresh session
                st_dict = (packet.meta or {}).get("utilizer_state")
                if isinstance(st_dict, dict) and "phase" in st_dict:
                    try:
                        st = SessionState(phase=Phase(st_dict["phase"]))
                        st.distill = st_dict.get("distill")
                        st.resonance_questions = st_dict.get("resonance_questions", []) or []
                        st.psl_contract = st_dict.get("psl_contract")
                        st.execution_steps = st_dict.get("execution_steps", []) or []
                        st.crystal_id = st_dict.get("crystal_id")
                        st.crystal_text = st_dict.get("crystal_text")
                    except Exception:
                        st = SessionState(phase=Phase.DISTILL)
                else:
                    st = SessionState(phase=Phase.DISTILL)

                msg, st2 = self.utilizer.process(txt, st, decision.mode)

                new_payload = _inject_text(packet.payload, msg)
                new_meta = dict(packet.meta or {})
                new_meta["utilizer"] = {"mode": decision.mode.value, "reason": decision.reason}
                new_meta["utilizer_state"] = {
                    "phase": st2.phase.value,
                    "distill": st2.distill,
                    "resonance_questions": st2.resonance_questions,
                    "psl_contract": st2.psl_contract,
                    "execution_steps": st2.execution_steps,
                    "crystal_id": st2.crystal_id,
                    "crystal_text": st2.crystal_text,
                }

                return Decision(type=DecisionType.DIRECT_PASS.value, payload=new_payload, meta=new_meta)

            return Decision(type=DecisionType.DIRECT_PASS.value, payload=packet.payload, meta=packet.meta)

        # Резонанс >= порога -> suggestion (пока заглушка)
        if packet.resonance_score >= self.resonance_threshold:
            await BUS.publish(
                {
                    "type": "symbiotic_suggestion",
                    "operator_id": self.operator_id,
                    "score": packet.resonance_score,
                    "psl_id": packet.psl_id,
                }
            )
            return Decision(
                type=DecisionType.SYMBIOTIC_SUGGESTION.value,
                payload={"suggestion": "confirm_or_refine"},
                meta=packet.meta,
            )

        return Decision(type=DecisionType.DROP.value, reason="noise_dropped", meta=packet.meta)
