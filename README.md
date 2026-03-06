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
## 🔄 Utilizer — двигатель структурного мышления (v0.2.0)

**Utilizer** — пятифазный FSM-движок, встроенный в LUYS.OS. Он переводит любой вход (включая «мусорные» запросы) из режима пассивного ответа в структурный цикл: **суть → вопросы → контракт → действие → кристалл**.

### 🧠 5 фаз

| Фаза | Назначение |
|------|------------|
| **DISTILL** | Извлечение сути из сырого запроса |
| **RESONANCE** | Уточняющие/расщепляющие вопросы |
| **PSL** | Формализация как мини-контракт |
| **EXECUTION** | 1–3 шага действия |
| **LIBRARIUM** | Фиксация результата как «кристалла» |

### 🎮 Режимы работы

Режим задаётся через `meta.utilizer_mode`:
- **AUTO** — роутер выбирает режим автоматически
- **MINI** — короткие вопросы и шаги
- **FULL** — полный цикл
- **DIRECT** — прямой ответ + один шаг

### 🧪 Тест (PowerShell)

```powershell
@'
{"operator_id":"op1","payload":"Мне скучно","psl_id":"p1","psl_tag":"[FACT]","source":"operator","resonance_score":1.0,"meta":{"session_id":"test_1","utilizer_mode":"FULL"}}
'@ | Set-Content -Encoding UTF8 req.json

curl.exe -s -X POST "http://127.0.0.1:7777/api/signal" -H "Content-Type: application/json; charset=utf-8" --data-binary "@req.json"
Ожидаемый ответ: decision.meta.utilizer_state.phase начинается с RESONANCE


