from __future__ import annotations

from datetime import datetime
from typing import Optional

from orchestrator.wuwei.models import ResonancePacket, Decision, DecisionType
from orchestrator.wuwei.policy import WuWeiPolicy
from services.rollback_service import ROLLBACK, RollbackItem, RollbackScope
from services.event_bus import BUS


class WuWeiEngine:
    """
    MVP policy:
    - [FACT] + resonance_score==1.0 -> DIRECT_PASS
    - [HYP] + score<1.0 -> QUEUE_ROLLBACK + event
    - score>=threshold -> SUGGEST
    - else -> DROP
    """

    def __init__(self, operator_id: str, policy: WuWeiPolicy | None = None) -> None:
        self.operator_id = operator_id
        self.policy = policy or WuWeiPolicy()

    async def process(self, packet: ResonancePacket) -> Optional[Decision]:
        if packet.psl_tag == "[HYP]" and packet.resonance_score < 1.0:
            ROLLBACK.queue_rollback_check(
                RollbackItem(
                    operator_id=self.operator_id,
                    psl_id=packet.psl_id,
                    trigger="hrr_violation",
                    scope=RollbackScope.COGNITIVE_HALLUCINATION,
                    created_at=datetime.now(),
                    payload={"meta": packet.meta},
                )
            )
            await BUS.publish({
                "type": "hrr_update",
                "operator_id": self.operator_id,
                "score": packet.resonance_score,
                "psl_id": packet.psl_id,
                "tag": packet.psl_tag,
                "action": "queued_for_rollback"
            })
            return Decision(type=DecisionType.QUEUE_ROLLBACK, reason="HYP<1.0 queued")

        if packet.psl_tag == "[FACT]" and packet.resonance_score == 1.0:
            await BUS.publish({
                "type": "packet_passed",
                "operator_id": self.operator_id,
                "psl_id": packet.psl_id,
                "tag": packet.psl_tag
            })
            return Decision(type=DecisionType.DIRECT_PASS, payload=packet.payload)

        if packet.resonance_score >= self.policy.resonance_threshold:
            return Decision(type=DecisionType.SUGGEST, payload=packet.payload, meta={"psl_id": packet.psl_id})

        return None
