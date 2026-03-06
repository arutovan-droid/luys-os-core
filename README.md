# LUYS.OS Core — WuWei Core (MVP)

Minimal orchestration core for LUYS.OS:

- WuWei Engine signal processing ([FACT]/[HYP])
- Rollback queue (in-memory MVP)
- Event Bus + WebSocket stream (/wuwei/stream)
- Operator Dashboard UI served from the same origin (no CORS pain)

---

## 🚀 Quickstart (Windows)

### 1) Go to project folder
```powershell
cd /d C:\Users\H2H1\luys-os-core
2) Activate virtualenv
If .venv already exists:

powershell
.\.venv\Scripts\activate
If you need to create it:

powershell
python -m venv .venv
.\.venv\Scripts\activate
3) Install dependencies
powershell
pip install -r requirements.txt
If WebSocket shows warnings like:

Unsupported upgrade request

No supported WebSocket library detected

Install the standard extras:

powershell
pip install "uvicorn[standard]"
4) Run the server
Stable (no reload):

powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 7777
Dev mode (auto reload):

powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 7777 --reload
5) Open Operator UI
Open in browser:

text
http://127.0.0.1:7777/ui/operator_dashboard.html
Expected at the top:

API: OK

WS: CONNECTED

🌐 API (curl)
Health
powershell
curl -s http://127.0.0.1:7777/health
Send [FACT] (should return direct_pass)
powershell
curl -s http://127.0.0.1:7777/api/signal ^
  -H "Content-Type: application/json" ^
  -d "{\"operator_id\":\"OPERATOR_ID\",\"payload\":\"I keep the lens clean\",\"psl_id\":\"psl_fact_1\",\"psl_tag\":\"[FACT]\",\"source\":\"operator\",\"resonance_score\":1.0,\"meta\":{}}"
Send [HYP] with score < 1.0 (should queue rollback)
powershell
curl -s http://127.0.0.1:7777/api/signal ^
  -H "Content-Type: application/json" ^
  -d "{\"operator_id\":\"OPERATOR_ID\",\"payload\":\"HYP test\",\"psl_id\":\"psl_hyp_1\",\"psl_tag\":\"[HYP]\",\"source\":\"operator\",\"resonance_score\":0.7,\"meta\":{}}"
Rollback status
powershell
curl -s "http://127.0.0.1:7777/api/rollback/status?operator_id=OPERATOR_ID"
Execute rollback (manual)
powershell
curl -s http://127.0.0.1:7777/api/rollback/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"operator_id\":\"OPERATOR_ID\"}"
(Optional) Tail last events
powershell
curl -s "http://127.0.0.1:7777/api/events/tail?n=50&operator_id=OPERATOR_ID"
📜 Behavior Contract (MVP)
Условие	Результат
[FACT] + resonance_score == 1.0	direct_pass
[HYP] + resonance_score < 1.0	queue_rollback + enqueue item + WS event
UI connects to:

REST: http://127.0.0.1:7777

WS: ws://127.0.0.1:7777/wuwei/stream

🔧 Troubleshooting
Port already in use (Windows 10048)
Find PID and kill:

powershell
netstat -ano | findstr :7777
taskkill /PID <PID> /F
WebSocket warnings / WS not connecting
Install:

powershell
pip install "uvicorn[standard]"
Then restart the server.

pydantic conflict with aiogram
If you installed aiogram into the same venv, it may require pydantic<2.6.
Best practice: keep aiogram and luys-os-core in separate virtualenvs.

🔄 Utilizer — двигатель структурного мышления (v0.2.0)
Utilizer — это пятифазный FSM-движок, встроенный в LUYS.OS. Он превращает любой запрос (даже «мусорный») в структурированный диалог, ведущий пользователя от сырой мысли к кристаллу смысла.

🧠 5 фаз Utilizer
Фаза	Назначение
DISTILL	Извлечение сути из сырого запроса
RESONANCE	Расщепляющие вопросы для уточнения
PSL	Формализация задачи как контракта
EXECUTION	Конкретные шаги действия
LIBRARIUM	Сохранение результата как кристалла
🎮 Режимы работы
Режим	Описание
DIRECT	Прямой ответ + один шаг (для фактов)
MINI	Бытовой цикл (1–2 фазы) — по умолчанию
FULL	Полный 5-фазный цикл до кристалла
AUTO	Автоматический выбор роутером
🔄 Сброс фазы
Поддерживается принудительный сброс фазы в DISTILL через флаг reset_phase=True:

powershell
curl -s http://127.0.0.1:7777/api/signal ^
  -H "Content-Type: application/json" ^
  -d "{\"operator_id\":\"test\",\"payload\":\"любой ответ\",\"psl_id\":\"p2\",\"psl_tag\":\"[FACT]\",\"source\":\"operator\",\"resonance_score\":1.0,\"reset_phase\":true}"
📁 Структура модуля
text
luys-os-core/
  utilizer/
    engine.py          # 5-фазная FSM
    router.py          # выбор режима
    types.py           # Phase, Mode, SessionState
    sources_loader.py  # загрузка кристаллов
  sources/utilizer/
    CONSTITUTION_UTILIZER.md   # философия
    PSL_TEMPLATES.md           # шаблоны контрактов
    CRYSTALS.yaml              # начальные кристаллы
🔧 Интеграция
Хук в orchestrator/wuwei/engine.py (ветка DIRECT_PASS)

Состояние хранится в _UTILIZER_STATE_STORE по operator_id/session_id

Бытовая проекция в services/bytovaya_projection.py для человеческого языка

Выбор режима через meta.utilizer_mode в UI

🧪 Пример теста сброса фазы
python
import asyncio
from api.main import signal, SignalIn

async def test():
    r1 = await signal(SignalIn(
        operator_id='test', 
        payload='мне скучно', 
        psl_id='p1', 
        psl_tag='[FACT]', 
        source='operator', 
        resonance_score=1.0
    ))
    print('Phase 1:', r1['decision']['meta']['utilizer_state']['phase'])  # RESONANCE
    
    r2 = await signal(SignalIn(
        operator_id='test', 
        payload='любой ответ', 
        psl_id='p2', 
        psl_tag='[FACT]', 
        source='operator', 
        resonance_score=1.0, 
        reset_phase=True
    ))
    print('Phase 2 (reset):', r2['decision']['meta']['utilizer_state']['phase'])  # DISTILL

asyncio.run(test())
📊 Status
✅ MVP is running:

REST OK

WS events OK

Rollback queue OK

UI OK

Utilizer 5-phase FSM OK

Phase reset OK

