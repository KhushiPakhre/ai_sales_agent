# Architecture Report (Phase 1 Audit)

## Current architecture (before this round)

`agent/` is a mature, already-working Phase 1-3 pipeline:

```
raw text -> extractor -> qualifier -> recommender -> next_action -> (booking_store / tour / handoff)
                              ^
                        session_store (conversation memory, DB-backed)
```

- `agent/orchestrator.py::run_agent` is the single entry point. It classifies
  intent (new requirement vs. follow-up question), merges the new message
  into the lead's accumulated requirement, qualifies, recommends, decides
  the next action (which may instant-book, propose a tour, or escalate to
  a human), and logs every decision to `crm_log.json`.
- `agent/db.py` already has a real SQLite schema: `workspaces`,
  `availability`, `leads`, `conversation_history`,
  `lead_recommendations_cache`, `tours`, `bookings`. `init_db()` is
  idempotent and seeds inventory from `data/workspaces.seed.json` on first
  run only.
- Every module (`session_store`, `booking_store`, `availability`,
  `recommender`) already talks to this DB - there is no legacy
  JSON-file-based code left to retire.
- `main.py` is a demo runner that calls `run_agent` directly and prints
  results; it has no API surface at all.

## Reusable modules (used as-is, unmodified)

Every file in `agent/` and `data/workspaces.seed.json`. Nothing here needed
rewriting - the backend is a thin adapter on top of it.

## What was missing

1. **No API layer.** `run_agent` was only callable from a Python process
   importing `agent.orchestrator` directly - nothing a browser could call.
2. **No inventory write path.** The agent could read workspaces but nothing
   could create/update one (there was no operator-facing use case yet).
3. **No "list everything" views.** `session_store`/`booking_store` are built
   around a single `lead_id` at a time (correct for the chat use case), but
   a dashboard needs "all leads", "all bookings", "all tours" listings.
4. **No persisted handoff record.** A handoff is a per-message decision;
   the full packet is already logged to `crm_log.json` on every escalation,
   but nothing read that log back out for a dashboard.
5. **No frontend at all.**

## Changes made

All additive, in a new `backend/` (Python) and `frontend/` (React) tree.
**Zero lines in `agent/`, `main.py`, or `data/` were changed.**

- `backend/services/*` - one file per domain, each a thin layer that calls
  into `agent.*` for anything resembling business logic (extraction,
  qualification, recommendation, booking, tours, chat) and only reaches
  into `agent.db` directly for read-only listing queries or the two
  genuinely new write paths (workspace CRUD, direct/manual booking and tour
  creation for operator use, which the chat-only pipeline never needed).
- `backend/api/*` - FastAPI routers, one per resource, matching the spec's
  suggested `backend/api/{leads,chat,workspaces,availability,bookings,
  tours,analytics}.py` structure (plus `handoffs.py`).
- `backend/schemas/*` - Pydantic request/response models. These are a
  presentation-layer concern; `agent.schema.LeadRequirement` (a dataclass)
  is still the one source of truth for the lead shape - the Pydantic
  models mirror it, they don't replace it.
- Handoffs are served by reading `crm_log.json` (the orchestrator's
  existing mock-CRM mirror) rather than inventing a new DB table for
  something already being persisted.
- Workspace/manual-booking/manual-tour writes go straight through
  `agent.db`/`agent.booking_store`/`agent.session_store` - the same
  connection and tables the agent itself uses, so there is exactly one
  source of truth regardless of whether a booking came from chat or from
  the dashboard.

## Frontend architecture

React + Vite + Tailwind, no additional state-management library - each
page owns its own fetch via a small `useApiData` hook, and shows
loading/error/empty states explicitly rather than assuming success. Routing
via `react-router-dom`. The chatbot is a first-class page (`/chat`), not a
widget bolted onto the dashboard, per the "chatbot is the primary
user-facing experience" instruction - the operator dashboard pages
(`/leads`, `/workspaces`, `/bookings`, `/tours`, `/handoffs`, `/analytics`)
sit alongside it in the same nav.

## Database considerations

No schema changes. The existing `bookings`/`tours`/`leads`/`workspaces`
tables cover everything the API needs. One structural note worth flagging:
`tours` is keyed by `lead_id` (one active tour per lead, by design - see
`agent/db.py`), so `GET/PATCH /api/tours/{tour_id}` uses `lead_id` as the
identifier rather than a separate tour ID. Documented in
`backend/services/tours_service.py` and the API router.
