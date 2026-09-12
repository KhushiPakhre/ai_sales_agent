"""
Handles "quick questions on pricing & amenities" (Smart Handoff, AI side) -
a lead asking about a workspace the agent already recommended, rather than
stating a new requirement.
"""
from dataclasses import dataclass
from typing import List, Optional

from agent.amenities import AMENITY_KEYWORDS



@dataclass
class FaqAnswer:
    resolved: bool
    message: str


def answer_question(text: str, last_recommendations: List[dict], contact_name: Optional[str]) -> FaqAnswer:
    name = contact_name or "there"
    lower = text.lower()

    if not last_recommendations:
        return FaqAnswer(
            resolved=False,
            message=(
                f"Hi {name}, I don't have an active recommendation on file to answer that "
                f"against - could you remind me which option, or share your requirement again?"
            ),
        )

    top = last_recommendations[0]
    amenities = [a.lower() for a in top.get("amenities", [])]

    if "how much" in lower or "price" in lower or "cost" in lower:
        return FaqAnswer(
            resolved=True,
            message=(
                f"Hi {name}, {top['name']} is ₹{top['price_per_seat_inr']}/seat/month. "
                f"Let me know if you'd like to go ahead."
            ),
        )

    asked_amenities = [kw for kw in AMENITY_KEYWORDS if kw in lower]
    if asked_amenities:
        found = [kw for kw in asked_amenities if any(kw in a for a in amenities)]
        not_found = [kw for kw in asked_amenities if kw not in found]
        parts = []
        if found:
            parts.append(f"yes, {top['name']} has {', '.join(found)}")
        if not_found:
            parts.append(f"I don't have {', '.join(not_found)} listed for it - let me confirm with the team")
        return FaqAnswer(resolved=bool(found) and not not_found, message=f"Hi {name}, " + "; ".join(parts) + ".")

    return FaqAnswer(
        resolved=False,
        message=(
            f"Hi {name}, good question - let me check that with the team and get back to you "
            f"on {top['name']}."
        ),
    )
