"""
Covers the flows called out in the assignment:
  1. Lead creation
  2. Chat message
  3. Requirement extraction (via chat, asserted through the parsed lead)
  4. Availability
  5. Booking
  6. Duplicate booking
  7. Tour creation
  8. Human handoff
  9. Lead history

Run with:  pytest backend/tests -v
"""
from datetime import date, timedelta


def _tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


# 1. Lead creation -----------------------------------------------------------

def test_create_lead_directly(client):
    resp = client.post("/api/leads", json={
        "lead_id": "test:lead-001",
        "contact_name": "Asha",
        "company_name": "Loopwork",
        "location": "Bangalore",
        "team_size": 6,
        "workspace_type": "hot_desk",
        "budget_per_seat": 7000,
        "move_in_timeline": "immediate",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["lead_id"] == "test:lead-001"
    assert body["requirement"]["contact_name"] == "Asha"
    assert body["requirement"]["location"] == "Bangalore"

    get_resp = client.get("/api/leads/test:lead-001")
    assert get_resp.status_code == 200
    assert get_resp.json()["requirement"]["company_name"] == "Loopwork"


def test_get_unknown_lead_404(client):
    resp = client.get("/api/leads/does-not-exist")
    assert resp.status_code == 404


# 2 & 3. Chat message + requirement extraction -------------------------------

def test_chat_message_extracts_requirement_and_recommends(client):
    resp = client.post("/api/chat/message", json={
        "lead_id": "chat:test-100",
        "channel": "chat",
        "message": (
            "Hi, I'm Rohan from Finlytics. Need a dedicated desk in Bangalore "
            "for a team of 12, budget around 9000 per seat, moving in immediately."
        ),
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead_id"] == "chat:test-100"
    assert body["qualification"]["tier"] in ("hot", "warm", "cold")
    assert body["action"] in (
        "send_recommendations_book_call", "send_recommendations_nurture",
        "send_recommendations_low_touch", "schedule_tour_handoff",
    )

    # Requirement extraction: fetch the lead back and check parsed fields.
    lead = client.get("/api/leads/chat:test-100").json()
    req = lead["requirement"]
    assert req["location"] == "Bangalore"
    assert req["team_size"] == 12
    assert req["workspace_type"] == "dedicated_desk"
    assert req["budget_per_seat"] == 9000


def test_chat_message_missing_info_asks_clarifying_questions(client):
    resp = client.post("/api/chat/message", json={
        "lead_id": "chat:test-101",
        "channel": "chat",
        "message": "I need a meeting room in Gurgaon.",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "request_missing_info"
    assert body["booking"] is None


# 4. Availability -------------------------------------------------------------

def test_availability_defaults_to_full_capacity(client, a_workspace_id):
    ws_id = a_workspace_id["id"]
    resp = client.get(f"/api/workspaces/{ws_id}/availability", params={"date": _tomorrow()})
    assert resp.status_code == 200
    body = resp.json()
    assert body["workspace_id"] == ws_id
    assert body["slots_remaining"] == body["daily_capacity"]
    assert body["is_available"] is True


def test_availability_unknown_workspace_404(client):
    resp = client.get("/api/workspaces/WS-DOES-NOT-EXIST/availability")
    assert resp.status_code == 404


# 5. Booking --------------------------------------------------------------------

def test_create_booking_reserves_a_slot(client, a_workspace_id):
    ws_id = a_workspace_id["id"]
    when = _tomorrow()

    resp = client.post("/api/bookings", json={
        "lead_id": "chat:test-200", "workspace_id": ws_id, "date": when, "seats": 2,
    })
    assert resp.status_code == 201
    booking = resp.json()
    assert booking["status"] == "confirmed"
    assert booking["seats"] == 2

    avail = client.get(f"/api/workspaces/{ws_id}/availability", params={"date": when}).json()
    assert avail["slots_remaining"] == avail["daily_capacity"] - 2


# 6. Duplicate booking ------------------------------------------------------

def test_duplicate_booking_returns_existing_not_a_second_slot(client, a_workspace_id):
    ws_id = a_workspace_id["id"]
    when = _tomorrow()

    first = client.post("/api/bookings", json={
        "lead_id": "chat:test-300", "workspace_id": ws_id, "date": when, "seats": 1,
    }).json()
    second = client.post("/api/bookings", json={
        "lead_id": "chat:test-300", "workspace_id": ws_id, "date": when, "seats": 1,
    }).json()

    assert first["booking_id"] == second["booking_id"]

    avail = client.get(f"/api/workspaces/{ws_id}/availability", params={"date": when}).json()
    # Only ONE seat should have been decremented, not two.
    assert avail["slots_remaining"] == avail["daily_capacity"] - 1


def test_direct_booking_for_unknown_lead_creates_minimal_lead_record(client, a_workspace_id):
    """A direct POST /api/bookings for a lead_id that has never been seen
    before (no prior /api/leads or /api/chat/message call) must succeed by
    upserting a minimal lead row - not fail with a foreign-key error - and
    that lead must then be visible via the leads API."""
    ws_id = a_workspace_id["id"]
    when = _tomorrow()
    lead_id = "chat:brand-new-lead-999"

    resp = client.post("/api/bookings", json={
        "lead_id": lead_id, "workspace_id": ws_id, "date": when, "seats": 1,
    })
    assert resp.status_code == 201
    assert resp.json()["lead_id"] == lead_id

    lead_resp = client.get(f"/api/leads/{lead_id}")
    assert lead_resp.status_code == 200
    assert lead_resp.json()["lead_id"] == lead_id
    assert any(b["booking_id"] == resp.json()["booking_id"] for b in lead_resp.json()["bookings"])


def test_booking_unknown_workspace_returns_clean_4xx_not_raw_sqlite_error(client):
    """An invalid workspace_id must surface as a clean 4xx with no sqlite
    internals in the response body."""
    resp = client.post("/api/bookings", json={
        "lead_id": "chat:test-unknown-ws", "workspace_id": "does-not-exist", "date": _tomorrow(), "seats": 1,
    })
    assert 400 <= resp.status_code < 500
    body = resp.text.lower()
    assert "sqlite" not in body
    assert "traceback" not in body


def test_chat_duplicate_message_does_not_double_book(client):
    lead_id = "chat:test-301"
    message = "Can we book a meeting room in Mumbai for 4 people, need it this week."

    first = client.post("/api/chat/message", json={
        "lead_id": lead_id, "channel": "chat", "message": message,
    }).json()
    second = client.post("/api/chat/message", json={
        "lead_id": lead_id, "channel": "chat", "message": message,
    }).json()

    assert first["action"] == "instant_book_confirmed"
    assert second["action"] == "instant_book_already_confirmed"
    assert second["booking"] is None  # resent confirmation, no new booking object


# 7. Tour creation ------------------------------------------------------------

def test_tour_created_for_human_close_type(client):
    resp = client.post("/api/chat/message", json={
        "lead_id": "email:test-400@example.com",
        "channel": "email",
        "message": (
            "Hi, this is Priya from Nimbus Retail. Private cabin in Mumbai, "
            "team of 15, budget 18000 per seat, moving in immediately."
        ),
    })
    body = resp.json()
    assert body["action"] == "schedule_tour_handoff"
    assert body["tour"] is not None
    assert body["tour"]["status"] == "proposed"

    tour_resp = client.get("/api/tours/email:test-400@example.com")
    assert tour_resp.status_code == 200
    assert tour_resp.json()["workspace_id"] == body["tour"]["workspace_id"]


def test_direct_tour_creation(client, a_workspace_id):
    resp = client.post("/api/tours", json={
        "lead_id": "manual:test-500",
        "workspace_id": a_workspace_id["id"],
        "proposed_time": "2027-01-01T11:00:00+00:00",
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "proposed"


# 8. Human handoff ------------------------------------------------------------

def test_no_inventory_match_creates_pending_handoff(client):
    resp = client.post("/api/chat/message", json={
        "lead_id": "chat:test-600",
        "channel": "chat",
        "message": (
            "I'm Aditya. Need a managed office in Chennai for 40 people, "
            "budget is tight at 4000 per seat, want it within 2 weeks."
        ),
    })
    body = resp.json()
    assert body["action"] == "escalate_no_inventory_match"
    assert body["handoff"] is not None
    assert body["handoff"]["urgency"] in ("urgent", "normal")

    handoffs = client.get("/api/handoffs", params={"pending_only": True}).json()
    assert any(h["lead_id"] == "chat:test-600" for h in handoffs)

    single = client.get("/api/handoffs/chat:test-600")
    assert single.status_code == 200
    assert "reason" in single.json()


# 9. Lead history ---------------------------------------------------------------

def test_chat_history_accumulates_across_turns(client):
    lead_id = "chat:test-700"
    client.post("/api/chat/message", json={
        "lead_id": lead_id, "channel": "chat", "message": "Hi, looking for office space.",
    })
    client.post("/api/chat/message", json={
        "lead_id": lead_id, "channel": "chat", "message": "Bangalore, team of 5, budget 8000.",
    })

    history = client.get(f"/api/chat/{lead_id}/history").json()["history"]
    # 2 inbound + 2 outbound turns
    assert len(history) == 4
    assert history[0]["direction"] == "inbound"
    assert history[-1]["direction"] == "outbound"


# Analytics smoke test ---------------------------------------------------------

def test_analytics_reflects_real_data_only(client, a_workspace_id):
    client.post("/api/chat/message", json={
        "lead_id": "chat:test-800", "channel": "chat",
        "message": "Need a day pass in Bangalore for 2 of us tomorrow.",
    })
    analytics = client.get("/api/analytics").json()
    assert analytics["total_leads"] >= 1
    assert analytics["total_bookings"] >= 1
    assert 0 <= analytics["conversion_rate"] <= 100
