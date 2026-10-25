"""Constants and configuration defaults for RescueMind."""

# Map center (Islamabad - Rawalpindi Twin Cities area)
DEFAULT_MAP_CENTER = [33.6844, 73.0479]
DEFAULT_ZOOM_LEVEL = 12

# Synthetic scoring weights
DEFAULT_WEIGHT_URGENCY = 0.45
DEFAULT_WEIGHT_WAITING = 0.35
DEFAULT_WEIGHT_VULNERABILITY = 0.20

# Standard required capabilities
ALL_SKILLS = [
    "veterinary_care",
    "trapped_animal_extrication",
    "transport",
    "handling_aggressive",
    "wildlife_rescue",
    "water_rescue",
]

# Animal categories
ANIMAL_CATEGORIES = [
    "dog",
    "cat",
    "bird",
    "livestock",
    "wildlife",
    "other",
]

# Simulation Notice
DISCLAIMER_TEXT = (
    "RescueMind is an educational and research simulator designed for academic demonstration. "
    "All incidents, teams, telemetry, and road networks are purely synthetic representations "
    "of the Islamabad-Rawalpindi metropolitan area. It does NOT dispatch real-world personnel, "
    "access emergency databases, or provide medically certified veterinary triage."
)
