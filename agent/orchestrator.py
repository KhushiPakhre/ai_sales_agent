"""
Top-level agent loop: perceive (parse) -> reason (qualify, recommend) -> act (next step).

This is deliberately structured as discrete, inspectable stages rather than
one opaque LLM call, so each decision (why a field is missing, why a
workspace was/wasn't recommended, why this action was chosen) is traceable -
important for a sales tool a human team has to trust and audit.

v2 adds three things the pitch deck promises but the original pipeline
couldn't do:
  - conversation memory across messages from the same lead (session_store)
  - intent routing, so a follow-up question doesn't get parsed as a new,
    empty lead (intent.py / faq.py)
  - full conversation context handed to a human on any escalation/handoff,
    not just the single message that triggered it
"""
import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from agent.extractor import extract_lead
from agent.qualifier import qualify_lead
from agent.recommender import recommend_workspaces
from agent.next_action import decide_and_draft, NextAction
from agent.intent import classify_intent
from agent.faq import answer_question
from agent.handoff import build_handoff_packet
from agent import session_store
from agent import db
from agent.schema import LeadRequirement

CRM_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "crm_log.json")

# Ensures tables exist (and inventory is seeded) before anything else in
# this process touches the database - importing the orchestrator is enough
# to get a ready-to-use backend, no separate setup step required.
db.init_db()


def _log_to_mock_crm(entry: dict) -> None:
    log = []
    if os.path.exists(CRM_LOG_PATH):
        with open(CRM_LOG_PATH, "r") as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                log = []
    log.append(entry)
    with open(CRM_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def run_agent(raw_lead_text: str, lead_id: str = None, channel: str = None, now=None) -> dict:
    """
    lead_id identifies "the same lead" across messages (e.g. derived from
    phone number + channel, or email address). If omitted, each call is
    treated as its own anonymous, one-off lead - matching the original
    single-shot behavior for backward compatibility.
    """
    lead_id = lead_id or f"anon-{uuid.uuid4().hex[:8]}"
    timestamp = (now or datetime.now(timezone.utc)).isoformat()

    session_store.append_history(lead_id, channel, "inbound", raw_lead_text, timestamp)

    prior_recommendations = session_store.get_last_recommendations(lead_id)
    intent = classify_intent(raw_lead_text, has_prior_recommendations=bool(prior_recommendations))

    if intent == "question":
        stored_requirement = session_store.get_session(lead_id).get("requirement") or {}
        contact_name = stored_requirement.get("contact_name")
        faq = answer_question(raw_lead_text, prior_recommendations, contact_name)
        action = NextAction(
            action="answered_question" if faq.resolved else "escalate_unanswered_question",
            message=faq.message,
            assign_to_human=not faq.resolved,
        )
        result = {
            "timestamp": timestamp,
            "lead_id": lead_id,
            "intent": intent,
            "lead": stored_requirement,
            "qualification": None,
            "recommendations": [],
            "next_action": asdict(action),
        }
        if action.assign_to_human:
            result["conversation_history"] = session_store.get_full_history(lead_id)
            result["handoff"] = build_handoff_packet(
                stored_requirement, qualification=None, recommendations=[], action_name=action.action,
            )
        _log_to_mock_crm(result)
        session_store.append_history(lead_id, channel, "outbound", action.message, timestamp)
        return result

    # intent == "new_or_update_requirement"
    new_lead = extract_lead(raw_lead_text)
    new_lead.channel = channel
    lead = session_store.merge_requirement(lead_id, new_lead)
    lead.lead_id = lead_id

    qualification = qualify_lead(lead)
    session_store.set_last_tier(lead_id, qualification.tier)
    recommendations = recommend_workspaces(lead) if len(lead.missing_fields_for_action()) <= 1 else []
    if recommendations:
        session_store.set_last_recommendations(lead_id, [r.workspace for r in recommendations])

    action = decide_and_draft(lead, qualification, recommendations, now=now)

    result = {
        "timestamp": timestamp,
        "lead_id": lead_id,
        "intent": intent,
        "lead": lead.to_dict(),
        "qualification": {
            "tier": qualification.tier,
            "score": qualification.score,
            "missing_fields": qualification.missing_fields,
            "reasons": qualification.reasons,
        },
        "recommendations": [
            {"workspace": r.workspace, "match_score": r.match_score, "match_reasons": r.match_reasons}
            for r in recommendations
        ],
        "next_action": asdict(action),
    }
    # Full context handoff (Smart Handoff: "no cold leads, ever") - a human
    # picking this up sees the whole conversation, not just the message
    # that triggered the handoff.
    if action.assign_to_human:
        result["conversation_history"] = session_store.get_full_history(lead_id)
        result["handoff"] = build_handoff_packet(
            lead.to_dict(),
            qualification=result["qualification"],
            recommendations=result["recommendations"],
            action_name=action.action,
            tour=session_store.get_tour(lead_id),
        )

    _log_to_mock_crm(result)
    session_store.append_history(lead_id, channel, "outbound", action.message, timestamp)
    return result
