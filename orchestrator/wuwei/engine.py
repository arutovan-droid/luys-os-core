from __future__ import annotations

from typing import Optional

from services.event_bus import BUS
from services.rollback_service import ROLLBACK

from .models import Decision, DecisionType, ResonancePacket


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

        # [FACT] с HRR=1.0 -> прямой пропуск
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
            return Decision(type=DecisionType.DIRECT_PASS.value, payload=packet.payload)

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
            )

        return Decision(type=DecisionType.DROP.value, reason="noise_dropped")
