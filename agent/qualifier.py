"""Scores lead completeness/urgency and assigns a qualification tier."""
from dataclasses import dataclass
from typing import List

from agent.schema import LeadRequirement, REQUIRED_FIELDS

CLARIFYING_QUESTIONS = {
    "location": "Which city (or specific area) are you looking for a workspace in?",
    "team_size": "How many people will be using the space?",
    "workspace_type": "Are you looking for a hot desk, dedicated desk, private cabin, or a fully managed office?",
    "budget_per_seat": "What's your monthly budget per seat (approximately)?",
    "move_in_timeline": "When are you looking to move in — immediately, or within a specific timeframe?",
    "requested_date": "Which date would you like to book it for?",
}


@dataclass
class QualificationResult:
    tier: str  # "hot" | "warm" | "cold"
    score: int  # 0-100
    missing_fields: List[str]
    clarifying_questions: List[str]
    reasons: List[str]


def qualify_lead(lead: LeadRequirement) -> QualificationResult:
    missing = lead.missing_fields()
    reasons = []
    score = 0

    completeness = (len(REQUIRED_FIELDS) - len(missing)) / len(REQUIRED_FIELDS)
    score += round(completeness * 50)
    reasons.append(f"completeness {round(completeness * 100)}% (+{round(completeness * 50)})")

    if lead.move_in_timeline == "immediate":
        score += 25
        reasons.append("immediate move-in timeline (+25)")
    elif lead.move_in_timeline:
        # parse "n days/weeks/months" - reward near-term timelines
        parts = lead.move_in_timeline.split()
        if len(parts) == 2 and parts[0].isdigit():
            n, unit = int(parts[0]), parts[1]
            days = n * {"day": 1, "days": 1, "week": 7, "weeks": 7,
                        "month": 30, "months": 30}.get(unit, 30)
            if days <= 30:
                score += 15
                reasons.append(f"near-term timeline ({lead.move_in_timeline}) (+15)")
            else:
                score += 5
                reasons.append(f"longer-term timeline ({lead.move_in_timeline}) (+5)")

    if lead.team_size:
        if lead.team_size >= 10:
            score += 15
            reasons.append(f"team size {lead.team_size} - meaningful deal size (+15)")
        else:
            score += 8
            reasons.append(f"team size {lead.team_size} (+8)")

    if lead.budget_per_seat:
        score += 10
        reasons.append("explicit budget given (+10)")

    score = min(score, 100)

    if score >= 70:
        tier = "hot"
    elif score >= 40:
        tier = "warm"
    else:
        tier = "cold"

    questions = [CLARIFYING_QUESTIONS[f] for f in missing]

    return QualificationResult(
        tier=tier,
        score=score,
        missing_fields=missing,
        clarifying_questions=questions,
        reasons=reasons,
    )
