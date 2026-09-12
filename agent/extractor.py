"""
Extracts a structured LeadRequirement from a raw lead message.

Two modes:
  - Heuristic mode (default, no API key needed): regex + keyword rules.
  - LLM-augmented mode (if ANTHROPIC_API_KEY is set): asks Claude to fill in
    whatever the heuristics couldn't confidently resolve, using tool-call
    style structured output. This is the "agentic" extraction layer -
    the heuristic pass runs first and only the gaps are handed to the LLM,
    which keeps cost/latency low and keeps the system usable offline.
"""
import os
import re
import json
from datetime import date, timedelta
from typing import Optional

from agent.schema import LeadRequirement, VALID_WORKSPACE_TYPES

KNOWN_CITIES = [
    "bangalore", "bengaluru", "mumbai", "gurgaon", "gurugram", "delhi",
    "new delhi", "noida", "kolkata", "hyderabad", "pune", "chennai",
    "kharagpur", "ahmedabad", "jaipur", "chandigarh",
]

WORKSPACE_TYPE_KEYWORDS = {
    # Checked before the more generic "desk"/"office" categories below so
    # e.g. "meeting room" doesn't fall through to a cabin/office match.
    "day_pass": ["day pass", "day passes", "single day use", "one-day pass", "one day pass"],
    "meeting_room": ["meeting room", "conference room", "boardroom"],
    "hot_desk": ["hot desk", "hotdesk", "flexi desk", "flexible desk"],
    "dedicated_desk": ["dedicated desk", "fixed desk", "dedicated seat"],
    "private_cabin": ["private cabin", "cabin", "private office", "private room"],
    "managed_office": ["managed office", "full office", "entire floor", "custom office"],
}

TIMELINE_KEYWORDS = {
    "immediate": ["immediately", "asap", "urgent", "right away", "this week", "today", "tomorrow"],
}

# Small-number words, since leads write "a team of six" as often as "6 people".
WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "a": 1, "an": 1,
    "couple": 2, "few": 3,
}
_WORD_NUM_PATTERN = "|".join(WORD_NUMBERS.keys())


def _extract_city(text: str) -> Optional[str]:
    lower = text.lower()
    for city in KNOWN_CITIES:
        if city in lower:
            if city == "bengaluru":
                return "Bangalore"
            if city == "gurugram":
                return "Gurgaon"
            if city == "new delhi":
                return "Delhi"
            return city.title()
    return None


def _extract_team_size(text: str) -> Optional[int]:
    # Solo / just-me phrasing has no number in it at all.
    if re.search(r"\b(just me|myself|it'?s just me|solo|one person)\b", text, re.I):
        return 1

    m = re.search(r"(\d{1,4})\s*(?:people|employees|seats|members|person|pax|team)", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"team of\s*(\d{1,4})", text, re.I)
    if m:
        return int(m.group(1))
    # "2 of us", "5 of us"
    m = re.search(r"(\d{1,4})\s*of us\b", text, re.I)
    if m:
        return int(m.group(1))
    # Word numbers: "team of six", "a couple of us", "for three people"
    m = re.search(rf"team of\s+({_WORD_NUM_PATTERN})\b", text, re.I)
    if m:
        return WORD_NUMBERS[m.group(1).lower()]
    m = re.search(rf"\b({_WORD_NUM_PATTERN})\s*of us\b", text, re.I)
    if m:
        return WORD_NUMBERS[m.group(1).lower()]
    return None


def _extract_budget(text: str) -> Optional[int]:
    # Range form: "8000-10000 per seat", "8-10k per seat" -> use the lower
    # bound, since that's the number a qualifier/recommender should treat
    # as the lead's stated floor, not an average that overstates it.
    m = re.search(
        r"(?:₹|rs\.?|inr)?\s*([\d,]{2,7})\s*(k)?\s*(?:-|to)\s*(?:₹|rs\.?|inr)?\s*([\d,]{2,7})\s*(k)?"
        r"\s*(?:/|per)\s*(?:seat|desk|person|head)",
        text, re.I,
    )
    if m:
        low_raw, low_k = m.group(1).replace(",", ""), m.group(2)
        val = int(low_raw)
        if low_k or (m.group(4) and val < 1000):
            val *= 1000
        return val

    # Matches: "₹8000/seat", "8k per seat", "budget of 10000 per desk", "Rs 7,500 per seat"
    m = re.search(
        r"(?:₹|rs\.?|inr)?\s*([\d,]{3,7})\s*(?:k)?\s*(?:/|per)\s*(?:seat|desk|person|head)",
        text, re.I,
    )
    if m:
        raw = m.group(1).replace(",", "")
        val = int(raw)
        if "k" in m.group(0).lower() and val < 1000:
            val *= 1000
        return val
    m = re.search(r"budget[^\d]{0,15}(?:₹|rs\.?|inr)?\s*([\d,]{3,7})\s*(k)?", text, re.I)
    if m:
        raw = m.group(1).replace(",", "")
        val = int(raw)
        if m.group(2):
            val *= 1000
        return val
    return None


def _extract_workspace_type(text: str) -> Optional[str]:
    lower = text.lower()
    for wtype, keywords in WORKSPACE_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return wtype
    return None


def _extract_timeline(text: str) -> Optional[str]:
    lower = text.lower()
    for label, keywords in TIMELINE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return label
    m = re.search(r"(?:within|in|next)\s*(\d{1,3})\s*(day|days|week|weeks|month|months)", lower)
    if m:
        n, unit = m.group(1), m.group(2)
        return f"{n} {unit}"
    # "within a month", "within a week" - word-number timelines
    m = re.search(rf"(?:within|in|next)\s+({_WORD_NUM_PATTERN})\s*(day|days|week|weeks|month|months)", lower)
    if m:
        n = WORD_NUMBERS[m.group(1)]
        unit = m.group(2)
        return f"{n} {unit}"
    return None


WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = [
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
]


def _extract_requested_date(text: str, reference: Optional[date] = None) -> Optional[str]:
    """
    Returns an ISO "YYYY-MM-DD" string for when the lead wants to actually
    use a day pass / meeting room. Without this, instant-booking has no
    concept of *which day* it's reserving a slot for - every booking was
    silently treated as "right now," which breaks the moment two leads
    book the same resource for different days.
    """
    reference = reference or date.today()
    lower = text.lower()

    if re.search(r"\btoday\b", lower):
        return reference.isoformat()
    if re.search(r"\btomorrow\b", lower):
        return (reference + timedelta(days=1)).isoformat()

    # Explicit weekday: "this Friday", "on Monday" -> next occurrence
    # (today counts as "this <weekday>" only if the text says "today" instead).
    for i, wd in enumerate(WEEKDAYS):
        if wd in lower:
            days_ahead = (i - reference.weekday()) % 7
            days_ahead = days_ahead or 7  # "on Monday" said on a Monday means next Monday
            return (reference + timedelta(days=days_ahead)).isoformat()

    # Explicit date: "15th September", "15 Sep", "September 15"
    m = re.search(
        rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({'|'.join(MONTHS)})", lower,
    ) or re.search(
        rf"({'|'.join(MONTHS)})\s+(\d{{1,2}})(?:st|nd|rd|th)?", lower,
    )
    if m:
        groups = m.groups()
        day_str, month_str = (groups[0], groups[1]) if groups[0].isdigit() else (groups[1], groups[0])
        month_num = MONTHS.index(month_str) + 1
        year = reference.year
        try:
            candidate = date(year, month_num, int(day_str))
            if candidate < reference:
                candidate = date(year + 1, month_num, int(day_str))
            return candidate.isoformat()
        except ValueError:
            return None

    # "this week" is too vague to pin to a single date - leave it for a
    # clarifying question rather than guessing which day.
    return None


def _extract_requested_time(text: str) -> Optional[str]:
    """Returns "HH:MM" 24h, e.g. "3pm" / "3 PM" / "15:00" -> "15:00"."""
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text, re.I)
    if m:
        hour, minute, meridiem = int(m.group(1)), int(m.group(2) or 0), m.group(3).lower()
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
    m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return None


def heuristic_extract(raw_text: str) -> LeadRequirement:
    lead = LeadRequirement(raw_text=raw_text)
    lead.location = _extract_city(raw_text)
    lead.team_size = _extract_team_size(raw_text)
    lead.workspace_type = _extract_workspace_type(raw_text)
    lead.budget_per_seat = _extract_budget(raw_text)
    lead.move_in_timeline = _extract_timeline(raw_text)
    lead.requested_date = _extract_requested_date(raw_text)
    lead.requested_time = _extract_requested_time(raw_text)

    # crude name/company heuristics - real system would use NER
    m = re.search(r"(?:i am|i'm|this is)\s+([A-Z][a-zA-Z]+)", raw_text, re.I)
    if m:
        lead.contact_name = m.group(1)
    m = re.search(r"(?:at|from|with)\s+([A-Z][\w&.]+(?:\s+[A-Z][\w&.]+)*)\s*(?:,|\.|$)", raw_text)
    if m:
        lead.company_name = m.group(1).strip()

    lead.extraction_notes.append("heuristic_pass")
    return lead


LLM_TOOL_SCHEMA = {
    "name": "record_lead_requirement",
    "description": "Record the structured requirement extracted from a workspace lead's message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "company_name": {"type": ["string", "null"]},
            "contact_name": {"type": ["string", "null"]},
            "location": {"type": ["string", "null"], "description": "City the lead wants a workspace in"},
            "team_size": {"type": ["integer", "null"]},
            "workspace_type": {
                "type": ["string", "null"],
                "enum": VALID_WORKSPACE_TYPES + [None],
            },
            "budget_per_seat": {"type": ["integer", "null"], "description": "Monthly budget per seat in INR"},
            "move_in_timeline": {"type": ["string", "null"]},
        },
        "required": [],
    },
}


def llm_augment(lead: LeadRequirement) -> LeadRequirement:
    """
    If fields are still missing after the heuristic pass AND an API key is
    configured, ask Claude to fill the gaps using tool-call structured output.
    Falls back silently to the heuristic result if no key / call fails, so
    the pipeline never hard-depends on network access.
    """
    missing = lead.missing_fields()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not missing or not api_key:
        return lead

    try:
        import anthropic
    except ImportError:
        lead.extraction_notes.append("llm_skipped: anthropic package not installed")
        return lead

    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "Extract the missing workspace-lead fields from this message. "
            f"Fields already known: {json.dumps(lead.to_dict())}. "
            f"Only these fields are still missing: {missing}. "
            "Call the tool with your best-guess values for the missing fields "
            "only (leave a field null if it truly isn't mentioned or implied).\n\n"
            f"Message:\n{lead.raw_text}"
        )
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            tools=[LLM_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "record_lead_requirement"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in resp.content:
            if block.type == "tool_use":
                data = block.input
                for field_name in missing:
                    val = data.get(field_name)
                    if val not in (None, ""):
                        setattr(lead, field_name, val)
                lead.extraction_notes.append("llm_augmented")
    except Exception as exc:  # noqa: BLE001 - demo-grade resilience
        lead.extraction_notes.append(f"llm_error: {exc}")

    return lead


def extract_lead(raw_text: str) -> LeadRequirement:
    lead = heuristic_extract(raw_text)
    lead = llm_augment(lead)
    return lead
