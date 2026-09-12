"""Shared amenity vocabulary - single source of truth so the recommender's
amenity matching and the FAQ/intent modules' keyword lists can't drift
apart."""

AMENITY_KEYWORDS = [
    "parking", "wifi", "cafeteria", "meeting room", "printing", "reception",
    "24x7", "coffee", "projector", "whiteboard", "video conferencing",
]


def requested_amenities(text: str) -> list:
    lower = text.lower()
    return [kw for kw in AMENITY_KEYWORDS if kw in lower]
