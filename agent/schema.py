"""Data model for a structured lead requirement."""
from dataclasses import dataclass, field, asdict
from typing import Optional, List

REQUIRED_FIELDS = [
    "location",
    "team_size",
    "workspace_type",
    "budget_per_seat",
    "move_in_timeline",
]

VALID_WORKSPACE_TYPES = [
    "hot_desk",
    "dedicated_desk",
    "private_cabin",
    "managed_office",
    "day_pass",
    "meeting_room",
]

CHANNELS = ["whatsapp", "email", "chat"]

# Per the product pitch (Smart Handoff): these two types are low-commitment,
# fixed-price bookings the AI can close on its own. Everything else routes
# through a human for negotiation/relationship-building.
INSTANT_BOOK_TYPES = ["day_pass", "meeting_room"]

# Explicitly called out on the "Human Closes" side of Smart Handoff. hot_desk
# is deliberately left out of both lists - the deck never assigns it to
# either bucket, so it keeps the original self-serve, score-driven behavior.
HUMAN_CLOSE_TYPES = ["private_cabin", "dedicated_desk", "managed_office"]

# Booking a day pass or meeting room doesn't need budget/timeline haggling -
# it's same-day, listed-price. It does need to know *which day*, though -
# without that there's no calendar slot to check or reserve.
INSTANT_BOOK_REQUIRED_FIELDS = ["location", "workspace_type", "team_size", "requested_date"]


@dataclass
class LeadRequirement:
    lead_id: Optional[str] = None
    channel: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    location: Optional[str] = None
    team_size: Optional[int] = None
    workspace_type: Optional[str] = None
    budget_per_seat: Optional[int] = None  # monthly, INR
    move_in_timeline: Optional[str] = None  # "immediate" | "<n> days" | "<n> weeks" etc.
    requested_date: Optional[str] = None  # ISO "YYYY-MM-DD", for day_pass / meeting_room bookings
    requested_time: Optional[str] = None  # "HH:MM" 24h, optional even for instant-book types
    raw_text: str = ""
    extraction_notes: List[str] = field(default_factory=list)

    def missing_fields(self, fields: Optional[List[str]] = None) -> List[str]:
        fields = fields or REQUIRED_FIELDS
        return [f for f in fields if getattr(self, f) in (None, "")]

    def is_instant_bookable_type(self) -> bool:
        return self.workspace_type in INSTANT_BOOK_TYPES

    def is_human_close_type(self) -> bool:
        return self.workspace_type in HUMAN_CLOSE_TYPES

    def missing_fields_for_action(self) -> List[str]:
        """Which fields block the agent from acting at all, given the type.

        Day passes / meeting rooms only need enough to find and hold a slot;
        everything else needs the full requirement (used for lead scoring).
        """
        if self.is_instant_bookable_type():
            return self.missing_fields(INSTANT_BOOK_REQUIRED_FIELDS)
        return self.missing_fields()

    def to_dict(self) -> dict:
        return asdict(self)

