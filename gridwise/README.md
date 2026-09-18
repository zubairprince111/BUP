# GridWise Energy Optimization Platform — BUP CSE Fest 2026

Production-ready submission for **BUP CSE Fest 2026 Hackathon (Preliminary Round)**. GridWise interprets natural language operator notes using Groq LLM, validates directives with deterministic guardrails, solves a 24-hour Mixed-Integer Linear Programming (MILP) energy schedule using PuLP + CBC, verifies the plan with replay validation, and provides an interactive Supabase-inspired React dashboard.

---

## 1. Project Overview
GridWise optimizes campus energy schedules over 24 discrete 1-hour intervals. It processes hourly electricity demand forecasts, rooftop solar generation, dynamic grid tariffs, battery storage parameters, and 1 to 3 natural language operator notes. It outputs the cost-minimal valid 24-hour dispatch plan along with AI directive interpretations, hourly schedules, and verified cost totals.

---

## 2. Architecture Diagram
```
                     Natural Language Operator Notes
                                    │
                                    ▼
                      ┌──────────────────────────┐
                      │ 1. Groq LLM Interpreter  │  (llama-3.3-70b-versatile, temp=0.0)
                      └─────────────┬────────────┘
                                    │ Structured Directives JSON
                                    ▼
                      ┌──────────────────────────┐
                      │ 2. Guardrail Validator   │  (Deterministic Bounds & Schema)
                      └─────────────┬────────────┘
                                    │ Validated Directives
                                    ▼
                      ┌──────────────────────────┐
                      │ 3. PuLP MILP Optimizer   │  (CBC Solver, Mutual Exclusion)
                      └─────────────┬────────────┘
                                    │ 24-Hour Dispatch Schedule
                                    ▼
                      ┌──────────────────────────┐
                      │ 4. Final Plan Validator  │  (24-Hour Replay, 0.01 kWh Tolerance)
                      └─────────────┬────────────┘
                                    │ Independent Totals & Summary
                                    ▼
                       REST API JSON / React Dashboard
```

---

## 3. Backend Setup
```bash
cd gridwise

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

---

## 4. Frontend Setup
```bash
cd gridwise/frontend

# Install node dependencies
npm install

# Build frontend
npm run build
```

---

## 5. Environment Variables
Copy `.env.example` to `.env` in `gridwise/`:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
PORT=8000
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Your Groq API Key |
| `GROQ_MODEL` | No | Model ID (defaults to `llama-3.3-70b-versatile`) |
| `PORT` | No | Server port (defaults to `8000`) |

---

## 6. Groq Model/Provider
- **Provider**: Groq Cloud API (`groq` Python SDK)
- **Model**: `llama-3.3-70b-versatile`
- **Temperature**: `0.0` (Maximum determinism)
- **Response Format**: `json_object`

---

## 7. LLM Role
The LLM translates 1-3 natural language operator notes into structured directives covering 6 canonical types:
1. `solar_reduction`: `{"hours": [...], "factor": float}`
2. `minimum_battery_reserve`: `{"hours": [...], "minimum_energy_kwh": float}`
3. `no_charge_window`: `{"hours": [...]}`
4. `no_discharge_window`: `{"hours": [...]}`
5. `max_grid_window`: `{"hours": [...], "max_grid_kwh": float}`
6. `no_op`: `applies=false`, `structured_adjustment=null`

---

## 8. Guardrails
Deterministic validation executes after LLM output to guarantee safety:
- Verifies `note_index`, `applies` boolean logic, valid directive types.
- Enforces unique sorted hours in `0-23`.
- Validates factor bounds ($0.0 \le \text{factor} \le 1.0$), non-negative reserve levels, and max grid caps.
- Automatically converts malformed LLM outputs to safe `no_op` directives.

---

## 9. MILP Optimizer
The optimizer formulates a **Mixed-Integer Linear Programming (MILP)** model in PuLP with CBC solver:
- **Objective**: Minimize total electricity purchasing cost:
  $$\text{Minimize } \sum_{h=0}^{23} (\text{grid\_kwh}[h] \times \text{tariff\_bdt}[h])$$
- **Subject to**:
  - Hourly energy balance: $\text{grid} + \text{solar\_used} + \text{discharge} = \text{demand} + \text{charge}$
  - Effective solar limit: $\text{solar\_used}[h] \le \text{solar\_kwh}[h] \times \text{factor}$
  - Battery capacity and minimum reserve bounds
  - Binary mutual exclusion: $\text{is\_charge}[h] + \text{is\_discharge}[h] \le 1$
  - End-of-day battery neutrality: $\text{battery\_energy}[23] == \text{initial\_energy\_kwh}$

---

## 10. Final Validator
The final validator replays the 24-hour hourly schedule to verify:
- Exactly 24 hours (0-23) in ascending order.
- All balance equations and rate limits hold within a `0.01 kWh` tolerance.
- End-of-day battery neutrality holds.
- Recalculates `total_grid_kwh`, `total_cost_bdt`, and `peak_grid_kwh` independently.

---

## 11. Local Backend Command
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## 12. Local Frontend Command
```bash
cd gridwise/frontend
npm run dev
# Frontend runs on http://localhost:5173
```

---

## 13. Swagger / OpenAPI Testing
Open browser to:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 14. Health Test
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

---

## 15. Public Sample Test Command
To run all 10 official BUP public sample test cases (`SAMPLE-01` to `SAMPLE-10`):
```bash
python -m unittest tests/test_samples.py
```

---

## 16. Complete Test Command
To run the full test suite (Public samples + Unit tests + API tests + LLM tests):
```bash
python -m unittest discover -s tests
```

---

## 17. Docker Build
```bash
docker build -t gridwise .
```

---

## 18. Docker Run
```bash
docker run -d -p 8000:8000 -e GROQ_API_KEY="your_groq_api_key_here" --name gridwise-app gridwise
```

---

## 19. Deployment
- **API URL**: `http://localhost:8000`
- **Endpoints**: `GET /health` and `POST /optimize-energy`
- No authentication or VPN required for evaluation.

---

## 20. API Request Example
`POST /optimize-energy`
```json
{
  "scenario_id": "SAMPLE-01",
  "operator_notes": [
    "Facilities will wash rooftop solar panels from noon until 2 PM. Usable solar should be treated as roughly 25% of forecast.",
    "The sports office moved next month's registration deadline."
  ],
  "hours": [
    {"hour": 0, "demand_kwh": 90.0, "solar_kwh": 0.0, "tariff_bdt_per_kwh": 6.0}
    /* ... 23 more entries, hours 0-23 */
  ],
  "battery": {
    "capacity_kwh": 500.0,
    "initial_energy_kwh": 200.0,
    "minimum_energy_kwh": 50.0,
    "max_charge_kwh_per_hour": 100.0,
    "max_discharge_kwh_per_hour": 100.0
  }
}
```

---

## 21. API Response Example
```json
{
  "scenario_id": "SAMPLE-01",
  "directive_interpretation": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "solar_reduction",
      "structured_adjustment": { "hours": [12, 13], "factor": 0.25 },
      "explanation": "Solar panel cleaning reduces usable solar to 25% from 12 PM to 2 PM."
    },
    {
      "note_index": 1,
      "applies": false,
      "directive_type": "no_op",
      "structured_adjustment": null,
      "explanation": "Administrative deadline note does not affect energy schedule."
    }
  ],
  "hourly_plan": [
    {
      "hour": 0,
      "grid_kwh": 90.0,
      "solar_used_kwh": 0.0,
      "battery_action": "idle",
      "battery_kwh": 0.0,
      "battery_energy_after_kwh": 200.0
    }
    /* ... 23 more entries */
  ],
  "total_grid_kwh": 2450.5,
  "total_cost_bdt": 38200.0,
  "peak_grid_kwh": 210.0,
  "plan_summary": "Applied solar_reduction directive during noon-2PM window. Ignored 1 irrelevant note..."
}
```

---

## 22. Known Limitations
- Requires a valid `GROQ_API_KEY` for LLM interpretation. If key is missing or invalid, raises `LLMInterpretationError` (HTTP 500) rather than silently discarding notes.
- Severely over-constrained inputs (e.g. 0 grid draw limit with 500 kWh demand and empty battery) will return HTTP 422 (Optimization Infeasible).
