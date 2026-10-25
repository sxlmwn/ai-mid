"""Incident domain model."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from rescuemind.utils.validators import ValidationError, validate_coordinates, validate_id, validate_non_negative


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    ASSESSED = "assessed"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class AnimalCategory(str, Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    LIVESTOCK = "livestock"
    WILDLIFE = "wildlife"
    OTHER = "other"


@dataclass
class Incident:
    incident_id: str
    title: str
    description: str
    location_id: str
    latitude: float
    longitude: float
    animal_category: AnimalCategory
    urgency: int  # 1 (low) to 5 (life-threatening)
    waiting_time: float = 0.0  # simulated minutes
    is_vulnerable: bool = False
    required_skills: List[str] = field(default_factory=list)
    status: IncidentStatus = IncidentStatus.REPORTED
    assigned_team_id: Optional[str] = None
    estimated_cost: Optional[float] = None
    estimated_time: Optional[float] = None
    creation_sequence: int = 0
    operator_notes: str = ""
    priority_score: float = 0.0
    priority_breakdown: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.incident_id = validate_id(self.incident_id, "Incident ID")
        self.location_id = validate_id(self.location_id, "Location ID")
        self.latitude, self.longitude = validate_coordinates(self.latitude, self.longitude)
        if not (1 <= self.urgency <= 5):
            raise ValidationError(f"Urgency must be integer between 1 and 5, got {self.urgency}.")
        self.waiting_time = validate_non_negative(self.waiting_time, "Waiting time")
        if isinstance(self.status, str):
            self.status = IncidentStatus(self.status)
        if isinstance(self.animal_category, str):
            self.animal_category = AnimalCategory(self.animal_category)

    def is_active(self) -> bool:
        """Return True if the incident is actively requiring rescue coordination."""
        return self.status in {
            IncidentStatus.REPORTED,
            IncidentStatus.ASSESSED,
            IncidentStatus.ASSIGNED,
            IncidentStatus.IN_PROGRESS,
        }

    def can_transition_to(self, target_status: IncidentStatus) -> bool:
        """Validate state transition logic."""
        if self.status in {IncidentStatus.RESOLVED, IncidentStatus.CANCELLED}:
            # Cannot change directly unless reopened
            return target_status in {IncidentStatus.REPORTED, self.status}
        return True

    def transition_to(self, target_status: IncidentStatus, notes: str = ""):
        """Perform validated state transition."""
        if not self.can_transition_to(target_status):
            raise ValidationError(
                f"Invalid transition: Cannot transition incident {self.incident_id} from "
                f"'{self.status.value}' to '{target_status.value}' without explicit reopening."
            )
        self.status = target_status
        if target_status in {IncidentStatus.RESOLVED, IncidentStatus.CANCELLED}:
            self.assigned_team_id = None
        if notes:
            self.operator_notes = f"{self.operator_notes}\n{notes}".strip()

    def to_dict(self) -> dict:
        """Serialize incident to dictionary."""
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "location_id": self.location_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "animal_category": self.animal_category.value,
            "urgency": self.urgency,
            "waiting_time": self.waiting_time,
            "is_vulnerable": self.is_vulnerable,
            "required_skills": list(self.required_skills),
            "status": self.status.value,
            "assigned_team_id": self.assigned_team_id,
            "estimated_cost": self.estimated_cost,
            "estimated_time": self.estimated_time,
            "creation_sequence": self.creation_sequence,
            "operator_notes": self.operator_notes,
            "priority_score": self.priority_score,
            "priority_breakdown": self.priority_breakdown,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Incident:
        """Deserialize from dictionary."""
        return cls(
            incident_id=data["incident_id"],
            title=data.get("title", "Animal Incident"),
            description=data.get("description", ""),
            location_id=data["location_id"],
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            animal_category=AnimalCategory(data.get("animal_category", "other")),
            urgency=int(data.get("urgency", 3)),
            waiting_time=float(data.get("waiting_time", 0.0)),
            is_vulnerable=bool(data.get("is_vulnerable", False)),
            required_skills=list(data.get("required_skills", [])),
            status=IncidentStatus(data.get("status", "reported")),
            assigned_team_id=data.get("assigned_team_id"),
            estimated_cost=data.get("estimated_cost"),
            estimated_time=data.get("estimated_time"),
            creation_sequence=int(data.get("creation_sequence", 0)),
            operator_notes=data.get("operator_notes", ""),
            priority_score=float(data.get("priority_score", 0.0)),
            priority_breakdown=data.get("priority_breakdown", {}),
        )
