from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from orchestrator.wuwei.engine import WuWeiEngine
from orchestrator.wuwei.models import ResonancePacket, Source
from services.event_bus import BUS
from services.rollback_service import ROLLBACK

app = FastAPI(title="LUYS.OS WuWei Core (MVP)")


class SignalIn(BaseModel):
    operator_id: str
    payload: Any
    psl_id: str
    psl_tag: str = Field(..., description="[FACT]/[HYP]/[ROLLBACK]")
    source: str = Field("operator", description="operator|latp|resonance|librarium")
    resonance_score: float = Field(..., ge=0.0, le=1.0)
    meta: Dict[str, Any] = Field(default_factory=dict)


class RollbackIn(BaseModel):
    operator_id: str


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "ts": datetime.now().isoformat()}


@app.post("/api/signal")
async def signal(inp: SignalIn) -> Dict[str, Any]:
    engine = WuWeiEngine(operator_id=inp.operator_id)

    packet = ResonancePacket(
        payload=inp.payload,
        psl_id=inp.psl_id,
        psl_tag=inp.psl_tag,
        timestamp=datetime.now(),
        source=Source(inp.source),
        resonance_score=inp.resonance_score,
        meta=inp.meta,
    )

    decision = await engine.process(packet)
    return {
        "decision": None
        if decision is None
        else {
            "type": decision.type,
            "payload": decision.payload,
            "reason": decision.reason,
            "meta": decision.meta,
        },
        "rollback_queue": ROLLBACK.pending_count(),
    }


@app.post("/api/rollback/execute")
async def rollback_execute(inp: RollbackIn) -> Dict[str, Any]:
    deleted = await ROLLBACK.execute_rollback(inp.operator_id)
    return {"deleted": deleted, "rollback_queue": ROLLBACK.pending_count()}


@app.websocket("/wuwei/stream")
async def wuwei_stream(ws: WebSocket):
    await ws.accept()
    q = BUS.subscribe()
    try:
        while True:
            event = await q.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        BUS.unsubscribe(q)
