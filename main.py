"""
Demo runner for the Qdesq AI Sales Agent.

Run:  python main.py

Section 1 replays the original single-shot leads (unchanged behavior).
Section 2 demonstrates the v2 capabilities that the original pipeline was
missing: conversation memory across messages, FAQ answering, instant
booking that actually holds a slot, human handoff with full context, and
tour reminder / no-show simulation.
"""
import json
from datetime import datetime, timedelta, timezone

from agent.orchestrator import run_agent
from agent import tour as tour_module

SAMPLE_LEADS = [
    # Fully specified -> should be a hot lead with strong recommendations
    "Hi, I'm Rohan from Finlytics Solutions. We need a dedicated desk setup "
    "in Bangalore for a team of 12, budget around ₹9000 per seat. Looking to "
    "move in immediately.",

    # Missing budget and timeline -> should trigger clarifying questions
    "Hello, this is Priya from Nimbus Retail. We're looking for a private "
    "cabin in Mumbai for about 15 people.",

    # Fully specified but no inventory match (budget too low for the type) -> escalate
    "I'm Aditya. Need a managed office in Chennai for 40 people, budget is "
    "tight at 4000 per seat, want it within 2 weeks.",

    # Vague, mostly incomplete -> cold / mostly clarifying questions
    "hi looking for some office space maybe, not sure of details yet",

    # Day pass request -> should be instant-booked by the AI, no human handoff
    "Hey, need a day pass in Bangalore for 2 of us tomorrow.",

    # Meeting room request -> same instant-book path, different type/city
    "Can we book a meeting room in Gurgaon for 4 people, need it this week.",
]


def print_result(i, lead_text, result):
    print(f"\n--- Lead {i} ---")
    print(f"Incoming message: {lead_text}\n")
    print(f"Intent: {result.get('intent')}")
    print(f"Parsed requirement: {json.dumps(result['lead'], indent=2)}")
    if result["qualification"]:
        q = result["qualification"]
        print(f"\nQualification: {q['tier'].upper()} (score {q['score']}/100)")
        if q["missing_fields"]:
            print(f"Missing fields: {q['missing_fields']}")
        print(f"Reasons: {q['reasons']}")
    if result["recommendations"]:
        print("\nTop recommendations:")
        for r in result["recommendations"]:
            w = r["workspace"]
            print(f"  - {w['name']} ({w['city']}) | ₹{w['price_per_seat_inr']}/seat | "
                  f"score {r['match_score']} | {r['match_reasons']}")
    print(f"\nNext action: {result['next_action']['action']} "
          f"(assign_to_human={result['next_action']['assign_to_human']})")
    print(f"Drafted message:\n{result['next_action']['message']}")
    if "conversation_history" in result:
        print(f"\n[Full context handed to human - {len(result['conversation_history'])} turn(s) on file]")
    if "handoff" in result:
        h = result["handoff"]
        print(f"[Handoff packet] urgency={h['urgency']} | reason={h['reason']}")
        print(f"  summary: {h['summary']}")
        print(f"  suggested next step: {h['suggested_next_step']}")
    print("-" * 70)


def section_1_single_shot_leads():
    print("=" * 70)
    print("SECTION 1: ORIGINAL SINGLE-SHOT LEADS (unchanged behavior)")
    print("=" * 70)
    for i, lead_text in enumerate(SAMPLE_LEADS, 1):
        result = run_agent(lead_text)
        print_result(i, lead_text, result)


def section_2_conversation_memory():
    print("\n" + "=" * 70)
    print("SECTION 2: CONVERSATION MEMORY ACROSS MESSAGES (same lead_id)")
    print("=" * 70)
    lead_id = "whatsapp:+91-90000-00001"

    turn1 = "Hi, I'm Meera. Looking for a private cabin in Pune."
    r1 = run_agent(turn1, lead_id=lead_id, channel="whatsapp")
    print_result("2a", turn1, r1)

    # Reply to the agent's own clarifying question - old pipeline would have
    # parsed this alone and lost "Meera / Pune / private cabin" entirely.
    turn2 = "Team of 12, budget 8000 per seat, need it within a month."
    r2 = run_agent(turn2, lead_id=lead_id, channel="whatsapp")
    print_result("2b", turn2, r2)


def section_3_faq_and_instant_booking():
    print("\n" + "=" * 70)
    print("SECTION 3: FAQ HANDLING + INSTANT BOOKING THAT HOLDS A REAL SLOT")
    print("=" * 70)
    lead_id = "chat:session-8842"

    turn1 = "Need a day pass in Bangalore for 2 people, tomorrow."
    r1 = run_agent(turn1, lead_id=lead_id, channel="chat")
    print_result("3a", turn1, r1)

    turn2 = "Does it have parking?"
    r2 = run_agent(turn2, lead_id=lead_id, channel="chat")
    print_result("3b", turn2, r2)


def section_4_tour_reminder_and_no_show():
    print("\n" + "=" * 70)
    print("SECTION 4: TOUR SCHEDULING, REMINDER SWEEP, NO-SHOW FOLLOW-UP")
    print("=" * 70)
    lead_id = "email:priya@nimbusretail.com"

    turn1 = ("Hello, this is Priya from Nimbus Retail. Private cabin in "
             "Mumbai, team of 15, budget 18000 per seat, moving in immediately.")
    r1 = run_agent(turn1, lead_id=lead_id, channel="email")
    print_result("4a", turn1, r1)

    # Simulate a scheduler running ~23 hours later - the tour proposed above
    # for "hot" tier is ~24h out, so it should now be due for a reminder.
    simulated_now = datetime.now(timezone.utc) + timedelta(hours=23)
    due = tour_module.check_reminders(now=simulated_now)
    print(f"\n[Reminder sweep @ {simulated_now.isoformat()}] {len(due)} tour(s) due:")
    for d in due:
        print(f"  - lead_id={d['lead_id']} tour={d['tour']['workspace_name']} "
              f"at {d['tour']['proposed_time']}")

    # Simulate the lead not showing up.
    followup = tour_module.mark_no_show(lead_id)
    print(f"\n[No-show follow-up drafted]\n{followup}")


def section_5_extraction_and_validation_fixes():
    print("\n" + "=" * 70)
    print("SECTION 5: EXTRACTION IMPROVEMENTS + BOOKING VALIDATION")
    print("=" * 70)

    # Previously unparsed: word numbers, "of us" phrasing, "within a month".
    turn = "Hey, need a day pass in Bangalore, a couple of us, within a week."
    r = run_agent(turn, lead_id="chat:session-9001", channel="chat")
    print_result("5a", turn, r)

    # Party of 4 booking a meeting room: book_slot must reserve 4 seats, not 1.
    lead_id = "chat:session-9002"
    turn_a = "Can we book a meeting room in Mumbai for 4 people, need it this week."
    r_a = run_agent(turn_a, lead_id=lead_id, channel="chat")
    print_result("5b", turn_a, r_a)

    # Same lead resending the identical request - should NOT double-book;
    # should resend the existing confirmation instead.
    r_b = run_agent(turn_a, lead_id=lead_id, channel="chat")
    print_result("5c (duplicate message, same lead)", turn_a, r_b)


def section_6_phase2_availability_dates_and_followups():
    print("\n" + "=" * 70)
    print("SECTION 6: PHASE 2 - CALENDAR AVAILABILITY, DATES, CONFIRMATIONS, FOLLOW-UPS")
    print("=" * 70)

    # Two different leads both booking the same meeting room for the SAME
    # date should compete for that date's capacity...
    turn_a = "Can we book a meeting room in Gurgaon for 3 people this Friday."
    r_a = run_agent(turn_a, lead_id="chat:session-9101", channel="chat")
    print_result("6a", turn_a, r_a)

    # ...but a request for a DIFFERENT date on the same workspace should be
    # unaffected - this is the point of the calendar (Phase 1's flat pool
    # would have treated these as the same shrinking bucket).
    turn_b = "Can we book a meeting room in Gurgaon for 3 people next Monday."
    r_b = run_agent(turn_b, lead_id="chat:session-9102", channel="chat")
    print_result("6b (different date, same workspace)", turn_b, r_b)

    # Booking confirmation is now a real, queryable record, not just a
    # session-local dict.
    from agent import booking_store
    lead_bookings = booking_store.bookings_for_lead("chat:session-9101")
    print(f"\n[booking_store] chat:session-9101 has {len(lead_bookings)} confirmed booking(s) on file:")
    for b in lead_bookings:
        print(f"  - {b['booking_id']}: {b['workspace_name']} on {b['date']}, {b['seats']} seat(s), status={b['status']}")

    # A private cabin lead who names their own preferred tour date should
    # get a tour proposed for THAT date, not a generic tier-based offset.
    turn_c = ("Hi, I'm Karan from Vantage Labs. Private cabin in Bangalore, team of 8, "
              "budget 15000 per seat, want a tour this Friday at 3pm.")
    r_c = run_agent(turn_c, lead_id="email:karan@vantagelabs.com", channel="email")
    print_result("6c (tour honors lead's requested date/time)", turn_c, r_c)

    # Stale-lead follow-up sweep: a warm/cold lead that never replied
    # should be surfaced by a scheduler-style check.
    from agent import followups
    simulated_now = datetime.now(timezone.utc) + timedelta(hours=130)
    stale = followups.check_stale_leads(now=simulated_now)
    print(f"\n[Follow-up sweep @ {simulated_now.isoformat()}] {len(stale)} stale lead(s) due:")
    for s in stale[:5]:
        draft = followups.draft_followup(s["lead_id"])
        print(f"  - lead_id={s['lead_id']} tier={s['tier']} last_outbound={s['last_outbound']}")
        print(f"    drafted follow-up: {draft}")


def main():
    section_1_single_shot_leads()
    section_2_conversation_memory()
    section_3_faq_and_instant_booking()
    section_4_tour_reminder_and_no_show()
    section_5_extraction_and_validation_fixes()
    section_6_phase2_availability_dates_and_followups()
    print("\nFull run log written to crm_log.json; sessions in data/sessions.json")


if __name__ == "__main__":
    main()
