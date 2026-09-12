"""
Classifies an inbound message before it's treated as "here is my
requirement." Without this step, a lead asking a follow-up question about
a workspace the agent already recommended ("does it have parking?") gets
run through the extractor as if it were a new, mostly-empty lead.

Kept as simple heuristics, same spirit as the rest of the extraction layer:
cheap, fast, auditable, and only reaches for something heavier (an LLM
call) if this project later needs to handle messier phrasing.
"""
import re

from agent.amenities import AMENITY_KEYWORDS

QUESTION_MARKERS = [
    "does it have", "does this have", "is there", "what about", "how much",
    "can i", "do you have", "what time", "when is", "where is", "any parking",
]



def classify_intent(text: str, has_prior_recommendations: bool) -> str:
    """
    Returns one of:
      - "question": a follow-up question about something already shown
      - "new_or_update_requirement": a new lead, or a lead adding/changing
        requirement details (the default, and the only option before any
        recommendations exist)
    """
    if not has_prior_recommendations:
        return "new_or_update_requirement"

    lower = text.lower()
    looks_like_question = "?" in lower or any(m in lower for m in QUESTION_MARKERS)
    mentions_amenity = any(kw in lower for kw in AMENITY_KEYWORDS)

    # A question mark alone isn't enough - "do you have anything in Pune?"
    # is a new requirement, not a question about a prior recommendation.
    has_new_structured_signal = bool(
        re.search(r"\d{1,4}\s*(?:people|employees|seats|members|person|pax|team)", lower)
        or re.search(r"budget|per seat|per desk", lower)
    )

    if looks_like_question and (mentions_amenity or "how much" in lower) and not has_new_structured_signal:
        return "question"

    return "new_or_update_requirement"
