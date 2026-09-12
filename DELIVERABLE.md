# Qdesq Sales+ - Final Deliverable

See `ARCHITECTURE_REPORT.md` for the Phase 1 audit. This doc covers the
final deliverable checklist.

## 1. Final project structure

```
qdesq-sales-plus/
├── agent/                     # UNCHANGED - existing Phase 1-3 pipeline
├── data/
│   └── workspaces.seed.json   # UNCHANGED
├── main.py                    # UNCHANGED - CLI demo still works as-is
├── requirements.txt           # extended with fastapi/uvicorn/pydantic/pytest/httpx
├── pytest.ini
├── ARCHITECTURE_REPORT.md
├── DELIVERABLE.md             # this file
├── .env.example
├── backend/
│   ├── app.py                 # FastAPI entrypoint (CORS, error handling)
│   ├── api/                   # leads, chat, workspaces, availability,
│   │                          # bookings, tours, handoffs, analytics
│   ├── schemas/                # Pydantic request/response models
│   ├── services/               # business logic, wraps agent.* modules
│   └── tests/                  # pytest suite (9 required flows)
└── frontend/
    ├── package.json / vite.config.js / tailwind.config.js
    ├── .env.example
    └── src/
        ├── api/client.js       # single fetch wrapper, typed errors
        ├── components/         # AppLayout, Toast, Feedback (empty/error/
        │                       # skeleton states), MetricCard, chat/*
        ├── hooks/useApiData.js
        └── pages/               # Dashboard, ChatPage, Leads, LeadDetail,
                                  # Workspaces, WorkspaceDetail, Bookings,
                                  # Tours, Handoffs, Analytics
```

## 2. Backend API list

| Resource | Endpoints |
|---|---|
| Leads | `GET /api/leads`, `GET /api/leads/{lead_id}`, `POST /api/leads`, `PATCH /api/leads/{lead_id}` |
| Chat | `POST /api/chat/message`, `GET /api/chat/{lead_id}/history` |
| Workspaces | `GET /api/workspaces` (filters: city, workspace_type, min_capacity, max_price, amenity), `GET /api/workspaces/{id}`, `POST /api/workspaces`, `PATCH /api/workspaces/{id}` |
| Availability | `GET /api/workspaces/{id}/availability` (date, start_time, end_time, capacity) |
| Bookings | `GET /api/bookings`, `GET /api/bookings/{id}`, `POST /api/bookings`, `PATCH /api/bookings/{id}` |
| Tours | `GET /api/tours`, `GET /api/tours/{lead_id}`, `POST /api/tours`, `PATCH /api/tours/{lead_id}` |
| Handoffs | `GET /api/handoffs` (optional `pending_only=true`), `GET /api/handoffs/{lead_id}` |
| Analytics | `GET /api/analytics` |
| Health | `GET /api/health` |

Note: a "tour_id" is the lead_id - see `ARCHITECTURE_REPORT.md`.

## 3. Frontend page list

Dashboard (`/`), Chat (`/chat`, `/chat/:leadId`), Leads (`/leads`), Lead
Detail (`/leads/:leadId`), Workspaces (`/workspaces`), Workspace Detail
(`/workspaces/:workspaceId`), Bookings (`/bookings`), Tours (`/tours`),
Handoffs (`/handoffs`), Analytics (`/analytics`).

## 4. Database changes

None. Same SQLite schema as the existing `agent/db.py`. Two new write paths
were added at the *service* layer (not the schema): workspace CRUD, and
operator-initiated (non-chat) booking/tour creation - both go through the
existing tables via the existing modules (`agent.db`, `agent.booking_store`,
`agent.session_store`, `agent.availability`).

## 5. How the frontend talks to the backend

Plain `fetch` via `frontend/src/api/client.js`, base path `/api`. In dev,
Vite's proxy (`vite.config.js`) forwards `/api/*` to
`VITE_API_PROXY_TARGET` (default `http://localhost:8000`) so there's no
CORS friction locally. In production, set `VITE_API_BASE_URL` to the
deployed backend's full origin, and set `QDESQ_ALLOWED_ORIGINS` on the
backend to the deployed frontend's origin.

## 6. How to run the backend

```bash
cd qdesq-sales-plus
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

First request (or the moment `backend.app` is imported) calls
`agent.db.init_db()`, creating `data/qdesq.db` and seeding inventory - no
separate migration step, matching how `main.py` already behaves.

The original CLI demo still works unmodified: `python main.py`.

## 7. How to run the frontend

```bash
cd qdesq-sales-plus/frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. `npm run build` produces a static bundle in
`dist/`.

## 8. Environment variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `QDESQ_ALLOWED_ORIGINS` | backend | `http://localhost:5173,http://127.0.0.1:5173` | CORS allow-list |
| `ANTHROPIC_API_KEY` | backend (optional) | unset | Enables `agent/extractor.py`'s LLM-augmented extraction pass |
| `VITE_API_BASE_URL` | frontend (optional) | `/api` | Override if calling a backend on a different origin |
| `VITE_API_PROXY_TARGET` | frontend (dev only) | `http://localhost:8000` | Where the Vite dev proxy forwards `/api/*` |

## 9. Test commands

```bash
# Backend (from project root)
pytest backend/tests -v

# Original agent regression (unchanged, still passes)
python main.py
```

Frontend has no component tests included given the scope/time budget;
`vitest` is wired into `package.json` (`npm run test`) for anyone who adds
some. Manual verification: `npm run dev` and walk the 5 flows below.

## 10. Example API requests

```bash
# Chat message -> agent response
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"lead_id":"chat:session-123","channel":"chat",
       "message":"I need a meeting room in Gurgaon tomorrow for 4 people around 3 PM"}'

# List leads
curl http://localhost:8000/api/leads

# Check availability
curl "http://localhost:8000/api/workspaces/WS014/availability?date=2026-09-20"

# Manual booking (operator-entered, not via chat)
curl -X POST http://localhost:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{"lead_id":"phone:9998887776","workspace_id":"WS014","date":"2026-09-20","seats":3}'

# Analytics
curl http://localhost:8000/api/analytics
```

## 11. Known limitations

- **Not executed end-to-end in this environment.** The sandbox this was
  built in has no network access, so `fastapi`/`uvicorn`/`pytest` and the
  frontend's `npm` dependencies could not be installed or run here. The
  existing `agent/` pipeline *was* verified (full `python main.py`
  regression, byte-for-byte consistent with its own README). The new
  backend code was syntax-checked (`py_compile`, all files clean) and the
  new frontend code was syntax-checked (`esbuild` transform on all 23
  JS/JSX files, zero failures), and both were written and manually traced
  against the existing agent's actual behavior and seed data - but you
  should run `pytest backend/tests -v` and `npm run dev` yourself as the
  real verification step before treating this as production-ready.
- No authentication/authorization yet (flagged as a to-do; the API is
  structured so a dependency-based auth check can be added to
  `backend/app.py`/routers without restructuring anything).
- `tours` table's one-tour-per-lead design (inherited from `agent/db.py`,
  not changed here) means the API can't represent a lead with two
  simultaneous scheduled tours.
- Handoffs are derived from `crm_log.json`, a flat-file mirror - fine for
  an MVP, but a real deployment should promote this to a DB table if
  handoff SLAs/ownership need to be tracked more rigorously.
- No rate limiting, request logging middleware, or production ASGI server
  config (gunicorn+uvicorn workers, etc.) - left for deployment-time setup.
- Frontend has no automated component tests (see item 9).

## 12. Recommended next steps for production

1. Run `pytest backend/tests -v` and `npm run dev` for real, fix anything
   environment-specific that only shows up on an actual install.
2. Add auth (even a simple API-key header for the operator dashboard) before
   deploying anywhere reachable from the internet.
3. Promote `crm_log.json`-derived handoffs to a real `handoffs` table if
   the sales team needs SLA tracking/ownership assignment.
4. Wire `agent/tour.py::check_reminders` and
   `agent/followups.py::check_stale_leads` to an actual scheduler (cron /
   Celery beat / APScheduler) - both are already written to be called this
   way, just never wired to a live trigger.
5. Add the real channel integrations the existing README already calls
   out as next steps (WhatsApp Business webhook, email inbox poller) -
   `channel` is currently just a label, not a live integration.
6. Swap SQLite for Postgres if concurrent write volume grows - `agent/db.py`
   is already written so this only touches its connection setup.
