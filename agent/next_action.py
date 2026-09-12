"""Decides what the agent should do next and drafts the outbound message."""
from dataclasses import dataclass
from datetime import datetime, timezone, date
from typing import List, Optional

from agent.schema import LeadRequirement
from agent.qualifier import QualificationResult, CLARIFYING_QUESTIONS
from agent.recommender import RecommendationResult, book
from agent import booking_store
from agent.tour import propose_tour

TIER_TOUR_PHRASING = {
    "hot": "tomorrow",
    "warm": "later this week",
    "cold": "whenever works for you - no rush",
}


@dataclass
class NextAction:
    action: str
    message: str
    assign_to_human: bool
    booking: Optional[dict] = None  # set when a real slot was held, for the caller to log


def _format_date(date_str: str) -> str:
    try:
        return datetime.fromisoformat(date_str).strftime("%a %d %b")
    except ValueError:
        return date_str


def decide_and_draft(
    lead: LeadRequirement,
    qualification: QualificationResult,
    recommendations: List[RecommendationResult],
    now: Optional[datetime] = None,
) -> NextAction:

    name = lead.contact_name or "there"
    missing_for_action = lead.missing_fields_for_action()

    # Case 1: critical info missing -> ask before recommending. Day passes /
    # meeting rooms only block on the smaller instant-book field set (which
    # now includes requested_date - a booking has to know *which day*);
    # every other type blocks on the full requirement used for lead scoring.
    if len(missing_for_action) > 1:
        questions = "\n".join(f"- {CLARIFYING_QUESTIONS[f]}" for f in missing_for_action)
        message = (
            f"Hi {name}, thanks for reaching out to Qdesq! To find the right "
            f"workspace for you, could you share a bit more detail?\n{questions}"
        )
        return NextAction(action="request_missing_info", message=message, assign_to_human=False)

    # Case 1a: this lead already has a confirmed booking for this workspace
    # type + date on file - resend the existing confirmation rather than
    # booking a second slot for the same request (e.g. a retried message).
    # requested_date can be the one field the <=1-missing gate let through,
    # so fall back to today rather than querying/booking against None.
    effective_date = lead.requested_date or date.today().isoformat()
    if lead.is_instant_bookable_type():
        existing = booking_store.get_active_booking(lead.lead_id, lead.workspace_type, effective_date)
        if existing:
            message = (
                f"Hi {name}, you're already booked — {existing['workspace_name']} "
                f"({existing['city']}) on {_format_date(existing['date'])}"
                + (f" at {existing['time']}" if existing.get("time") else "")
                + f", booking ref {existing['booking_id']}. Let me know if you'd like to change "
                  f"or add another booking instead."
            )
            return NextAction(action="instant_book_already_confirmed", message=message, assign_to_human=False)

    # Case 1b: day pass / meeting room with a match -> AI closes it instantly,
    # independent of lead score. Actually holds the slot on the calendar for
    # the specific requested_date, and creates a persistent booking record -
    # if every match is full that day, that's an escalation, not a false
    # "you're booked" message. Reserves seats for the whole party.
    if lead.is_instant_bookable_type() and recommendations:
        seats_needed = lead.team_size or 1
        # Only attempt to book workspaces that are actually the requested
        # type - a same-city hot_desk shown as a soft-matched alternate
        # isn't a valid stand-in for the day pass / meeting room the lead
        # asked for, and shouldn't have a slot reserved on its behalf.
        exact_type_matches = [r for r in recommendations if r.workspace["workspace_type"] == lead.workspace_type]
        for rec in exact_type_matches:
            ws = rec.workspace
            if book(ws["id"], effective_date, seats_needed=seats_needed):
                record = booking_store.create_booking(
                    lead.lead_id, ws, effective_date, lead.requested_time, seats_needed,
                )
                when = _format_date(effective_date) + (f" at {lead.requested_time}" if lead.requested_time else "")
                message = (
                    f"Hi {name}, you're booked! {ws['name']} ({ws['city']}) is confirmed "
                    f"for your {ws['workspace_type'].replace('_', ' ')} on {when} "
                    f"(₹{ws['price_per_seat_inr']}/seat, {seats_needed} seat(s)) — booking ref "
                    f"{record.booking_id}. Confirmation is on its way to your email/WhatsApp. "
                    f"Reply here if your plans change."
                )
                return NextAction(
                    action="instant_book_confirmed", message=message, assign_to_human=False,
                    booking={
                        "booking_id": record.booking_id, "date": record.date, "seats": record.seats,
                        "time": record.time, "workspace_name": record.workspace_name,
                        "workspace_type": record.workspace_type, "city": record.city,
                    },
                )
        when = _format_date(effective_date)
        if exact_type_matches:
            message = (
                f"Hi {name}, the {lead.workspace_type.replace('_', ' ')} options I found are fully "
                f"booked on {when}, so I'm flagging this to the team to find you the next available slot."
            )
        else:
            message = (
                f"Hi {name}, I don't have a {lead.workspace_type.replace('_', ' ')} available matching "
                f"your requirement for {when}, so I'm flagging this to the team to check other options."
            )
        return NextAction(action="escalate_no_slots_available", message=message, assign_to_human=True)

    # Case 2: qualified but no matching inventory -> escalate, don't fabricate options
    if not recommendations:
        message = (
            f"Hi {name}, thanks for the details. We don't have a perfect match in our "
            f"current inventory for your exact requirement, so I'm looping in our sales "
            f"team to check upcoming availability / off-catalog options for you."
        )
        return NextAction(action="escalate_no_inventory_match", message=message, assign_to_human=True)

    top = recommendations[0].workspace
    listing = "\n".join(
        f"{i+1}. {r.workspace['name']} ({r.workspace['city']}) - "
        f"₹{r.workspace['price_per_seat_inr']}/seat/month, "
        f"{r.workspace['workspace_type'].replace('_', ' ')}, "
        f"capacity {r.workspace['capacity_min']}-{r.workspace['capacity_max']}, "
        f"rated {r.workspace['rating']}"
        for i, r in enumerate(recommendations)
    )

    # Case 3: private cabin / dedicated desk / managed office -> explicitly
    # "Human Closes" territory (negotiation, custom terms, relationship-
    # building), so this always hands off to a rep, regardless of lead score.
    # The AI still does the useful part: recommend + propose a concrete tour
    # slot (honoring a lead's preferred date if they gave one), so the rep
    # picks up a warm, scheduled conversation, not a cold one.
    if lead.is_human_close_type():
        tour = propose_tour(lead, top, qualification.tier, now=now)
        proposed_dt = datetime.fromisoformat(tour.proposed_time)
        when_phrase = TIER_TOUR_PHRASING.get(qualification.tier, "in the next few days")
        message = (
            f"Hi {name}, based on your requirement here are our best options:\n{listing}\n\n"
            f"{top['name']} looks like the strongest fit. I've pencilled in a tour "
            f"{when_phrase} ({proposed_dt.strftime('%a %d %b, %I:%M %p UTC')}) - our team will "
            f"reach out to confirm the time and go over pricing/terms with you."
        )
        return NextAction(action="schedule_tour_handoff", message=message, assign_to_human=True)

    # Case 4: hot_desk (or any type the deck doesn't explicitly assign) ->
    # original self-serve, score-driven behavior.
    if qualification.tier == "hot":
        message = (
            f"Hi {name}, based on your requirement here are our best options:\n{listing}\n\n"
            f"{top['name']} looks like the strongest fit. Would you be free for a quick "
            f"call today or tomorrow to lock in a site visit?"
        )
        return NextAction(action="send_recommendations_book_call", message=message, assign_to_human=False)

    if qualification.tier == "warm":
        message = (
            f"Hi {name}, thanks for sharing your requirement. Here are a few options that "
            f"could work:\n{listing}\n\nLet me know if you'd like more details on any of these, "
            f"or if you'd like to schedule a walkthrough."
        )
        return NextAction(action="send_recommendations_nurture", message=message, assign_to_human=False)

    message = (
        f"Hi {name}, here are a couple of workspace options based on what you've shared "
        f"so far:\n{listing}\n\nFeel free to reach out whenever your requirement firms up "
        f"and we'll take it from there."
    )
    return NextAction(action="send_recommendations_low_touch", message=message, assign_to_human=False)
