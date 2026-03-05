from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from orchestrator.wuwei.engine import WuWeiEngine
from orchestrator.wuwei.models import ResonancePacket, Source
from services.event_bus import BUS
from services.event_log import EVENT_LOG
from services.rollback_service import ROLLBACK
from services.heartbeat import HEARTBEAT
from services.bytovaya_projection import project as _project


# --- Utilizer state store (MVP: in-memory) ---
_UTILIZER_STATE_STORE: Dict[str, Dict[str, Any]] = {}

def _utilizer_session_key(operator_id: str, meta: Dict[str, Any]) -> str:
    # Prefer explicit session_id if client provides it; fallback to operator_id
    sid = (meta or {}).get("session_id")
    return str(sid) if sid else str(operator_id)

app = FastAPI(title="LUYS.OS WuWei Core (MVP)")
@app.on_event("startup")
async def _startup() -> None:
    HEARTBEAT.start()


# Serve UI from the same origin to avoid CORS issues when opening via browser.
# UI will be available at: http://127.0.0.1:7777/ui/operator_dashboard.html
app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")


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


@app.get("/api/events/tail")
def events_tail(n: int = 40, operator_id: str | None = None) -> Dict[str, Any]:
    items = EVENT_LOG.tail(n=n, operator_id=operator_id)
    return {"count": len(items), "items": items}


@app.post("/api/signal")
async def signal(inp: SignalIn) -> Dict[str, Any]:
    engine = WuWeiEngine(operator_id=inp.operator_id)


    session_key = _utilizer_session_key(inp.operator_id, inp.meta)
    meta = dict(inp.meta or {})
    # Inject previous utilizer_state if not provided in request
    if "utilizer_state" not in meta and session_key in _UTILIZER_STATE_STORE:
        meta["utilizer_state"] = _UTILIZER_STATE_STORE[session_key]    

    packet = ResonancePacket(
        payload=inp.payload,
        psl_id=inp.psl_id,
        psl_tag=inp.psl_tag,
        timestamp=datetime.now(),
        source=Source(inp.source),
        resonance_score=inp.resonance_score,
        meta=meta,
    )

    decision = await engine.process(packet)

    # User-facing cleanup (бытовая проекция) — меняем только текст
    if decision is not None and decision.payload is not None:
        if isinstance(decision.payload, str):
            decision.payload = _project(decision.payload)
        elif isinstance(decision.payload, dict) and isinstance(decision.payload.get("text"), str):
            decision.payload["text"] = _project(decision.payload["text"])
    # Persist utilizer_state for the next request in this session
    if decision is not None and decision.meta and "utilizer_state" in decision.meta:
        _UTILIZER_STATE_STORE[session_key] = decision.meta["utilizer_state"]

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

    # Optional: also publish a WS event so UI shows it immediately
    await BUS.publish(
        {
            "type": "rollback_execute_response",
            "operator_id": inp.operator_id,
            "deleted": deleted,
            "rollback_queue": ROLLBACK.pending_count(),
        }
    )

    return {"deleted": deleted, "rollback_queue": ROLLBACK.pending_count()}


@app.get("/api/rollback/status")
def rollback_status(operator_id: str) -> Dict[str, Any]:
    items = ROLLBACK.list_pending(operator_id)
    return {"count": len(items), "items": items}


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




