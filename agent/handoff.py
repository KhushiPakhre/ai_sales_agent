"""
Builds the internal note that goes to a human rep on any handoff or
escalation - separate from the lead-facing message, since a rep needs
different information than the lead does: why this landed with them, how
urgent it is, and what's already been offered.

Previously, a handoff only carried the raw conversation (see orchestrator's
"full context handoff") with nothing summarizing it - a rep had to re-read
and re-derive the lead's tier, requirement, and top match every time.
"""
from typing import List, Optional

URGENT_ACTIONS = {
    "escalate_no_slots_available",
    "escalate_no_inventory_match",
    "escalate_unanswered_question",
}

REASON_BY_ACTION = {
    "escalate_no_inventory_match": "No inventory matches the lead's exact requirement.",
    "escalate_no_slots_available": "Instant-book inventory is fully booked for this request.",
    "escalate_unanswered_question": "Lead asked something the FAQ layer couldn't confidently answer.",
    "schedule_tour_handoff": (
        "Workspace type requires human negotiation/relationship-building "
        "(private cabin, dedicated desk, or managed office)."
    ),
}

SUGGESTED_NEXT_STEP_BY_ACTION = {
    "escalate_no_inventory_match": "Check off-catalog or upcoming inventory manually.",
    "escalate_no_slots_available": "Offer the next available slot or a nearby alternate workspace.",
    "escalate_unanswered_question": "Answer the lead's question directly.",
    "schedule_tour_handoff": "Confirm the proposed tour time and prepare the pricing/terms discussion.",
}


def build_handoff_packet(
    lead_dict: dict,
    qualification: Optional[dict],
    recommendations: List[dict],
    action_name: str,
    tour: Optional[dict] = None,
) -> dict:
    tier = qualification["tier"] if qualification else None
    urgency = "urgent" if (tier == "hot" or action_name in URGENT_ACTIONS) else "normal"

    summary_bits = [
        (lead_dict.get("contact_name") or "Unnamed lead")
        + (f" ({lead_dict['company_name']})" if lead_dict.get("company_name") else ""),
        f"wants {lead_dict.get('workspace_type') or 'unspecified type'} in "
        f"{lead_dict.get('location') or 'unspecified city'}",
        f"team size {lead_dict.get('team_size') or '?'}, "
        f"budget ₹{lead_dict.get('budget_per_seat') or '?'}/seat",
    ]
    if tier:
        summary_bits.append(f"lead score: {tier.upper()} ({qualification['score']}/100)")
    if recommendations:
        top = recommendations[0]["workspace"]
        summary_bits.append(f"top match: {top['name']} ({top['city']})")
    if tour:
        summary_bits.append(f"tour pencilled for {tour['proposed_time']}")

    return {
        "urgency": urgency,
        "reason": REASON_BY_ACTION.get(action_name, "Routed to a human by policy."),
        "summary": " | ".join(summary_bits),
        "suggested_next_step": SUGGESTED_NEXT_STEP_BY_ACTION.get(action_name, "Review and respond to the lead."),
    }
