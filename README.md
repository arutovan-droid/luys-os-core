# LUYS.OS Core — WuWei Core (MVP)

Minimal orchestration core for LUYS.OS:
- **WuWei Engine** signal processing (`[FACT]/[HYP]`)
- **Rollback queue** (in-memory MVP)
- **Event Bus** + **WebSocket stream** (`/wuwei/stream`)
- **Operator Dashboard UI** served from the same origin (no CORS pain)

---

## Quickstart (Windows)

### 1) Go to project folder
```bat
cd /d C:\Users\H2H1\luys-os-core

2) Activate virtualenv

If .venv already exists:

.\.venv\Scripts\activate


If you need to create it:

python -m venv .venv
.\.venv\Scripts\activate

3) Install dependencies
pip install -r requirements.txt


If WebSocket shows warnings like:

Unsupported upgrade request

No supported WebSocket library detected

Install the standard extras:

pip install "uvicorn[standard]"

4) Run the server

Stable (no reload):

python -m uvicorn api.main:app --host 127.0.0.1 --port 7777


Dev mode (auto reload):

python -m uvicorn api.main:app --host 127.0.0.1 --port 7777 --reload

Open Operator UI

Open in browser:

http://127.0.0.1:7777/ui/operator_dashboard.html

Expected at the top:

API: OK

WS: CONNECTED

API (curl)
Health
curl -s http://127.0.0.1:7777/health

Send [FACT] (should return direct_pass)
curl -s http://127.0.0.1:7777/api/signal ^
  -H "Content-Type: application/json" ^
  -d "{\"operator_id\":\"OPERATOR_ID\",\"payload\":\"I keep the lens clean\",\"psl_id\":\"psl_fact_1\",\"psl_tag\":\"[FACT]\",\"source\":\"operator\",\"resonance_score\":1.0,\"meta\":{}}"

Send [HYP] with score < 1.0 (should queue rollback)
curl -s http://127.0.0.1:7777/api/signal ^
  -H "Content-Type: application/json" ^
  -d "{\"operator_id\":\"OPERATOR_ID\",\"payload\":\"HYP test\",\"psl_id\":\"psl_hyp_1\",\"psl_tag\":\"[HYP]\",\"source\":\"operator\",\"resonance_score\":0.7,\"meta\":{}}"

Rollback status
curl -s "http://127.0.0.1:7777/api/rollback/status?operator_id=OPERATOR_ID"

Execute rollback (manual)
curl -s http://127.0.0.1:7777/api/rollback/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"operator_id\":\"OPERATOR_ID\"}"

(Optional) Tail last events
curl -s "http://127.0.0.1:7777/api/events/tail?n=50&operator_id=OPERATOR_ID"

Behavior Contract (MVP)

[FACT] + resonance_score == 1.0
→ direct_pass

[HYP] + resonance_score < 1.0
→ queue_rollback + enqueue item + WS event

UI connects to:

REST: http://127.0.0.1:7777

WS: ws://127.0.0.1:7777/wuwei/stream

Troubleshooting
Port already in use (Windows 10048)

Find PID and kill:

netstat -ano | findstr :7777
taskkill /PID <PID> /F

WebSocket warnings / WS not connecting

Install:

pip install "uvicorn[standard]"


Then restart the server.

pydantic conflict with aiogram

If you installed aiogram into the same venv, it may require pydantic<2.6.
Best practice: keep aiogram and luys-os-core in separate virtualenvs.

Status

MVP is running: REST OK, WS events OK, rollback queue OK, UI OK.