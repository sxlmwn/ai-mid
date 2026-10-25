"""Rescue team domain model."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from rescuemind.utils.validators import ValidationError, validate_coordinates, validate_id, validate_non_negative


class TeamStatus(str, Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    ON_SCENE = "on_scene"
    RESTING = "resting"
    OFF_DUTY = "off_duty"


@dataclass
class RescueTeam:
    team_id: str
    name: str
    base_location_id: str
    current_location_id: str
    latitude: float
    longitude: float
    skills: List[str] = field(default_factory=list)
    status: TeamStatus = TeamStatus.AVAILABLE
    capacity: int = 1
    current_assignments: List[str] = field(default_factory=list)
    travel_budget: Optional[float] = None  # Max allowed route cost
    supported_categories: List[str] = field(default_factory=list)  # Empty means all
    last_update_time: int = 0

    def __post_init__(self):
        self.team_id = validate_id(self.team_id, "Team ID")
        self.name = validate_id(self.name, "Team Name")
        self.base_location_id = validate_id(self.base_location_id, "Base Location ID")
        self.current_location_id = validate_id(self.current_location_id, "Current Location ID")
        self.latitude, self.longitude = validate_coordinates(self.latitude, self.longitude)
        if self.capacity < 1:
            raise ValidationError(f"Team capacity must be at least 1, got {self.capacity}.")
        if self.travel_budget is not None:
            self.travel_budget = validate_non_negative(self.travel_budget, "Travel budget")
        if isinstance(self.status, str):
            self.status = TeamStatus(self.status)

    def is_available_for_dispatch(self) -> bool:
        """Check if team can accept another simultaneous assignment."""
        if self.status != TeamStatus.AVAILABLE and len(self.current_assignments) == 0:
            return False
        return len(self.current_assignments) < self.capacity

    def has_required_skills(self, required_skills: List[str]) -> bool:
        """Verify team possesses all mandatory skills."""
        team_skills_set = set(self.skills)
        return all(skill in team_skills_set for skill in required_skills)

    def can_handle_category(self, category: str) -> bool:
        """Verify team supports the animal category."""
        if not self.supported_categories:
            return True
        return category in self.supported_categories

    def assign_incident(self, incident_id: str):
        """Record an assignment to this team."""
        if not self.is_available_for_dispatch():
            raise ValidationError(
                f"Team {self.team_id} cannot be assigned incident {incident_id}: "
                f"capacity {self.capacity} reached or status is {self.status.value}."
            )
        if incident_id not in self.current_assignments:
            self.current_assignments.append(incident_id)
        if len(self.current_assignments) >= self.capacity:
            self.status = TeamStatus.DISPATCHED

    def release_incident(self, incident_id: str):
        """Release an assigned incident from team."""
        if incident_id in self.current_assignments:
            self.current_assignments.remove(incident_id)
        if len(self.current_assignments) < self.capacity and self.status == TeamStatus.DISPATCHED:
            self.status = TeamStatus.AVAILABLE

    def to_dict(self) -> dict:
        """Serialize team to dictionary."""
        return {
            "team_id": self.team_id,
            "name": self.name,
            "base_location_id": self.base_location_id,
            "current_location_id": self.current_location_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "skills": list(self.skills),
            "status": self.status.value,
            "capacity": self.capacity,
            "current_assignments": list(self.current_assignments),
            "travel_budget": self.travel_budget,
            "supported_categories": list(self.supported_categories),
            "last_update_time": self.last_update_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RescueTeam:
        """Deserialize from dictionary."""
        return cls(
            team_id=data["team_id"],
            name=data.get("name", data["team_id"]),
            base_location_id=data["base_location_id"],
            current_location_id=data.get("current_location_id", data["base_location_id"]),
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            skills=list(data.get("skills", [])),
            status=TeamStatus(data.get("status", "available")),
            capacity=int(data.get("capacity", 1)),
            current_assignments=list(data.get("current_assignments", [])),
            travel_budget=data.get("travel_budget"),
            supported_categories=list(data.get("supported_categories", [])),
            last_update_time=int(data.get("last_update_time", 0)),
        )
