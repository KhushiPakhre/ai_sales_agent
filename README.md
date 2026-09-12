# Qdesq AI Sales Agent — Technical Assignment

A prototype agent that takes an inbound workspace lead, structures the
requirement, qualifies it, recommends matching workspaces from a mock
inventory, and decides/drafts the next sales action.

## Phase 3 — backend (this round)

Phases 1-2 were already persisting state, just to flat JSON files
(`sessions.json`, `calendar.json`, `bookings.json`) - functional for a
demo, but not queryable, not relational, and not something a dashboard or
a second process could safely read/write concurrently. Phase 3 swaps that
for a real SQLite database (`agent/db.py`), on purpose without adding an
ORM or new dependency - the point was a real schema with constraints and
joins, not a specific vendor. Swapping SQLite for Postgres later only
touches `db.py`'s connection setup; every other module is unchanged.

10. **Database** (`agent/db.py`) — schema for `workspaces`, `availability`,
    `leads`, `conversation_history`, `lead_recommendations_cache`, `tours`,
    and `bookings`, with foreign keys between them. `init_db()` is
    idempotent (safe to call on every process start) and seeds inventory
    from `data/workspaces.seed.json` on first run only.
11. **Lead storage** (`agent/session_store.py`) — leads and their full
    conversation history now live in the `leads` / `conversation_history`
    tables. Same public function signatures as Phase 1/2, so
    `orchestrator.py`, `tour.py`, and `followups.py` needed zero changes.
12. **Inventory management** (`agent/recommender.py`, `agent/availability.py`)
    — the workspace catalog and per-date calendar are now `workspaces` /
    `availability` tables, queried directly rather than loaded-and-scanned
    from a JSON file on every call.
13. **Booking storage** (`agent/booking_store.py`) — bookings are now rows
    in the `bookings` table, queryable by lead, workspace, date, or status,
    with the same create/lookup/update-status interface as Phase 2.

Verified by re-running the full `main.py` demo against the DB and
confirming byte-for-byte identical decisions to the last known-good
Phase 2 run (same 17 next-actions, same sequence), then inspecting the
actual SQLite tables directly to confirm real persistence (14 leads, 34
conversation turns, 7 bookings, 4 tours after one run) and that `init_db()`
is safe to call twice without re-seeding or erroring.

**Deliberately not done here:** swapping in a real ORM/migration tool
(Alembic, SQLAlchemy) or a client-server DB (Postgres/MySQL) - those are
infra decisions a team would make based on deployment target, not
something to lock in from a single-file SQLite prototype.

## Phase 2 — core functionality

Building on Phase 1's fixes, this round implemented the 5 core-functionality
items:

5. **Proper availability** (`agent/availability.py`) — replaced the flat,
   permanently-depleting `slots_available` counter with a real per-date
   calendar. Capacity is defined once per workspace (`daily_capacity`) and
   reservations are tracked per date, so booking out tomorrow's meeting
   room no longer touches today's availability (Section 6a/6b in
   `main.py` demonstrates two different dates on the same workspace
   booking independently).
6. **Date/time bookings** (`agent/extractor.py`) — leads can now specify
   *when*: "today", "tomorrow", weekday names ("this Friday"), explicit
   dates ("15th September"), and a time of day ("at 3pm"). `requested_date`
   is now a required field for instant-book types — a booking has to know
   which day it's reserving.
7. **Booking confirmation** (`agent/booking_store.py`) — confirmed bookings
   are now persistent, queryable records (unique ID, date, time, seats,
   status) instead of a single session-local dict that got overwritten on
   the next message. Supports lookup by lead, and a `status` field ready
   for cancellation/no-show/completed transitions.
8. **Tour scheduling** (`agent/tour.py`) — a lead who names their own
   preferred date/time for a tour now gets a tour proposed for *that* slot
   instead of a generic tier-based offset (Section 6c).
9. **Reminders and follow-ups** (`agent/followups.py`) — added a second,
   broader follow-up mechanism alongside Phase 1's tour reminders: a
   nurture sweep for warm/cold leads who never replied. It deliberately
   excludes leads with an active confirmed booking or a pending tour
   (those already have their own resolution path) so a lead doesn't get a
   tone-deaf "still looking?" message after they've already booked.

Also fixed along the way: the follow-up sweep initially surfaced leads who
had already gotten a confirmed instant booking — caught and excluded in
testing before delivery, along with the equivalent case for leads with a
pending tour.

## Phase 1 — fix current agent

Following the agreed build order (Phase 1: fix current agent → Phase 2:
core functionality → Phase 3: backend → Phase 4: dashboard → Phase 5:
integrations → Phase 6: product features), this round closed out Phase 1:

1. **Improve extraction** (`agent/extractor.py`) — team size now parses "a
   couple of us", "2 of us", and word numbers ("team of six"), not just
   "N people"; timelines parse "within a week/month" including word
   numbers; budgets parse ranges ("8-10k per seat" → uses the lower bound);
   a few more cities added.
2. **Fix booking validation** (`agent/recommender.py::book_slot`,
   `agent/next_action.py`) — booking a day pass/meeting room now reserves
   the whole party's seats (not always 1), only ever attempts to book
   inventory that's actually the requested type (a soft-matched hot_desk
   alternate can no longer get a phantom slot decremented on a day-pass
   request), and a duplicate message from the same lead resends the
   existing confirmation instead of booking a second slot.
3. **Improve inventory matching** (`agent/recommender.py`) — availability
   (`available_from`) is now checked against the lead's move-in timeline
   (previously ignored entirely — an "immediate" lead could be shown a
   workspace 60 days out); amenities the lead explicitly asked for
   ("need parking") now boost matching workspaces.
4. **Improve handoff logic** (`agent/handoff.py`) — every human handoff now
   carries a structured internal packet (urgency, reason, one-line
   requirement summary, suggested next step) alongside the full
   conversation history, instead of a rep having to re-derive all of that
   from the raw transcript.

Verified via `main.py` Section 5, plus a regression pass confirming
Sections 1–4 from the prior round still behave correctly.

## v2 — closing gaps against the Qdesq Sales+ pitch deck

The original pipeline (see "Architecture" below) was single-shot: every
message was parsed as if it were the first and only thing a lead ever said,
and the AI/human split was driven purely by lead score, not by what was
actually being booked. That contradicted the deck's own "Smart Handoff"
slide, which splits AI-handled vs. human-closed by **workspace type**, not
lead value. v2 adds:

- **Conversation memory** (`agent/session_store.py`) — messages from the
  same `lead_id` now merge into one accumulating requirement instead of
  each being parsed in isolation. A reply of "team of 12, budget 8000" to
  the agent's own clarifying question is no longer treated as a new, empty
  lead.
- **Intent routing** (`agent/intent.py`, `agent/faq.py`) — a follow-up
  question about a workspace already recommended ("does it have parking?")
  is answered directly instead of being re-run through extraction as a
  fresh, mostly-empty requirement.
- **Type-driven Smart Handoff** (`agent/next_action.py`) — day passes and
  meeting rooms are booked instantly by the AI (`agent/recommender.py::book_slot`
  actually decrements a real `slots_available` count, so two leads can't be
  told they got the same last slot); private cabins, dedicated desks, and
  managed offices always hand off to a human for negotiation, regardless of
  lead score — matching "Human Closes" on the pitch deck. `hot_desk` keeps
  the original score-driven self-serve behavior, since the deck never
  assigns it to either bucket explicitly.
- **Tour scheduling, reminders, and no-show follow-up** (`agent/tour.py`) —
  a human handoff now proposes a concrete tour slot (timed by lead tier),
  and a `check_reminders` sweep / `mark_no_show` follow-up exist for a
  scheduler to call — both explicitly listed as AI-handled on the deck but
  entirely absent before.
- **Full-context handoff** — any time `assign_to_human` is true, the CRM
  log entry now includes the lead's whole conversation history, not just
  the single message that triggered escalation ("no cold leads, ever").

Run `python3 main.py` to see all of this exercised: Section 1 replays the
original single-shot leads (note Lead 1 now correctly hands off to a human —
it's a dedicated desk, which the deck puts on the human-closes side, a
behavior the v1 code never encoded), Section 2 shows memory across two
messages from the same lead, Section 3 shows FAQ handling + real slot
booking, Section 4 simulates a reminder sweep and a no-show.

**Not in scope for this repo** — these are separate product surfaces the
deck describes, not fixes to this decision engine: the operator dashboard
(inventory/pricing UI, preview mode, real-time analytics), real channel
ingestion (WhatsApp Business webhook, email inbox polling, chat widget),
real CRM/PMS integration (still a JSON log here), and multi-tenant white-
label config (messages still hardcode "Qdesq" rather than reading an
operator's brand settings).

## Quick start


```bash
cd qdesq_sales_agent
python3 main.py
```

No API key or install required — the core pipeline runs entirely offline
on heuristics. Every run appends a record to `crm_log.json` to simulate a
CRM write-back.

Optional: set `ANTHROPIC_API_KEY` and `pip install anthropic` to turn on the
LLM-augmented extraction pass (see "LLM augmentation" below).

## Architecture

```
raw lead text
      │
      ▼
┌─────────────────┐
│   Extractor      │  heuristic regex/keyword pass → LeadRequirement
│ (perceive)       │  optional LLM tool-call pass fills remaining gaps
└─────────────────┘
      │
      ▼
┌─────────────────┐
│   Qualifier      │  scores completeness + urgency + deal size
│ (reason)         │  → tier (hot/warm/cold) + missing-field questions
└─────────────────┘
      │
      ▼
┌─────────────────┐
│  Recommender     │  filters/ranks mock inventory by city, capacity,
│ (reason)         │  workspace type, budget
└─────────────────┘
      │
      ▼
┌─────────────────┐
│  Next-Action     │  decision tree: ask for missing info / send
│ (act)            │  recommendations + push for a call / escalate to
└─────────────────┘  a human when nothing in inventory fits
      │
      ▼
  mock CRM log (crm_log.json)
```

Each stage is a small, independently testable module (`agent/extractor.py`,
`agent/qualifier.py`, `agent/recommender.py`, `agent/next_action.py`),
orchestrated by `agent/orchestrator.py`. I chose a **pipeline of
inspectable stages** over a single end-to-end LLM call for a few reasons:

- **Auditability.** A sales team needs to trust *why* a lead was scored hot
  vs cold, and *why* a workspace was or wasn't recommended. Each stage
  returns its own reasoning (`qualification.reasons`, `match_reasons`),
  not just a final answer.
- **Reliability without a model in the loop.** The extraction and
  recommendation logic work correctly with zero LLM calls, so the agent
  degrades gracefully if an API is down or a key isn't configured —
  important for something meant to run unattended on live leads.
- **Cheap to run at volume.** Most fields in a real lead message (city,
  team size, budget) are cleanly regex/keyword-extractable; reserving the
  LLM for only the genuinely ambiguous remainder keeps latency and cost
  down.

### LLM augmentation

`agent/extractor.py::llm_augment` demonstrates the agentic/tool-use layer:
after the heuristic pass, if fields are still missing *and* an API key is
present, it calls Claude with a forced tool-call (`record_lead_requirement`)
so the output is always structured JSON, never free text to re-parse. This
is the natural extension point for messier real-world lead text (e.g. long
rambling emails) where regex alone won't cut it. It fails silently back to
the heuristic result on any error so the pipeline never hard-depends on
network access.

### Recommendation logic

`agent/recommender.py` applies hard filters (city must match if given,
team size must fit within capacity, price can't be more than 15% over
budget) and a soft score on top (workspace-type match, rating) — so the
agent never recommends something the lead explicitly can't use, but still
ranks among the valid options.

### Next-action decision tree

`agent/next_action.py` picks one of five actions:

| Condition | Action |
|---|---|
| >1 required field missing | `request_missing_info` — ask clarifying questions |
| all fields known, no inventory match | `escalate_no_inventory_match` — hand to a human rather than force-fit a bad recommendation |
| hot lead + matches found | `send_recommendations_book_call` — push straight to a call |
| warm lead + matches found | `send_recommendations_nurture` — softer follow-up |
| cold lead + matches found | `send_recommendations_low_touch` — keep in pipeline |

Messages are template-drafted here (not LLM-generated) to keep tone
consistent and reviewable; swapping in an LLM call for more natural
phrasing is a drop-in change to `decide_and_draft`.

## Files

```
qdesq_sales_agent/
├── main.py                  # demo runner - single-shot leads + all v2/Phase1/2/3 scenarios
├── data/
│   ├── workspaces.seed.json # inventory seed data (15 listings, 7 cities) - loaded into DB on first run
│   └── qdesq.db             # generated - SQLite DB: leads, history, inventory, availability, bookings, tours
├── agent/
│   ├── db.py                 # SQLite schema + connection management (Phase 3)
│   ├── schema.py            # LeadRequirement data model + type taxonomy
│   ├── extractor.py         # text -> structured requirement (incl. date/time)
│   ├── qualifier.py         # scoring + missing-field questions
│   ├── recommender.py       # inventory matching + calendar-aware slot booking (DB-backed)
│   ├── availability.py      # per-date calendar for instant-book types (DB-backed)
│   ├── booking_store.py     # persistent, queryable booking records (DB-backed)
│   ├── amenities.py         # shared amenity keyword vocabulary
│   ├── intent.py            # question vs. new/update-requirement routing
│   ├── faq.py                # answers questions about prior recommendations
│   ├── tour.py               # tour proposals (date-aware), reminders, no-show follow-up
│   ├── followups.py         # nurture sweep for stale warm/cold leads
│   ├── handoff.py            # internal handoff packet for human reps
│   ├── session_store.py     # conversation memory, keyed by lead_id (DB-backed)
│   ├── next_action.py       # decision tree + message drafting
│   └── orchestrator.py      # wires the pipeline together, initializes the DB, logs to mock CRM
├── requirements.txt
└── crm_log.json             # generated on first run - external CRM mirror, not the DB itself
```

## What I'd add for a production version

- **Structured lead intake** (webhook/form schema) so extraction only has
  to handle genuinely free-text fields, not everything.
- **Real CRM integration** (e.g. HubSpot/Zoho API) in place of the JSON
  log, with idempotent upserts keyed on contact/company.
- **Real channel ingestion** — an actual WhatsApp Business webhook handler,
  email inbox poller, and chat widget backend; today `channel` is just a
  label passed into `run_agent`, not something wired to a live integration.
- **Multi-tenant / white-label config** — an operator profile (brand name,
  badge on/off, subdomain) that `next_action.py` reads when drafting
  messages, instead of hardcoding "Qdesq".
- **Semantic retrieval over workspace descriptions** (embeddings + vector
  search) once the catalog grows beyond a size hand-written filters can
  cover well — e.g. matching "quiet space for focused dev work" to
  amenities text.
- **A real scheduler** driving `tour.check_reminders` and human review of
  `mark_no_show` follow-ups, instead of both being called directly in the
  demo.
- **Human-in-the-loop review queue** for the `escalate_*` actions and for
  any lead where extraction confidence is low, before anything is sent.
- **Evaluation set** of real (anonymized) past leads to tune the scoring
  weights in `qualifier.py` against actual conversion outcomes rather than
  hand-picked weights.

## Notes on the assignment's other questions

The extractor/recommender/agent code above is what I built for this
assignment specifically. I don't have a public GitHub/portfolio link or a
deployed AI Resume Evaluator to point you to yet — happy to walk through
this code's design choices live instead, or take a follow-up assignment
that's closer to what you'd want to see next.
