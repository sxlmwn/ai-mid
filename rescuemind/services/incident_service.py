"""Incident lifecycle and priority queue management service."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Dict, List, Optional
from rescuemind.algorithms.priority import IncidentPriorityQueue, PriorityWeights
from rescuemind.models.incident import Incident, IncidentStatus, AnimalCategory
from rescuemind.utils.validators import ValidationError


class IncidentService:
    """Service managing incident state, validation, updates, and priority queues."""

    def __init__(self, data_path: Optional[Path] = None):
        self.incidents: Dict[str, Incident] = {}
        self._initial_incidents: Dict[str, Incident] = {}
        self.priority_weights = PriorityWeights()
        self.priority_queue = IncidentPriorityQueue(self.priority_weights)
        self.next_sequence = 1

        if data_path:
            self.load_from_json(data_path)

    def load_from_json(self, file_path: Path):
        """Load incidents from JSON file with data integrity validation."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.incidents.clear()
        for item in data.get("incidents", []):
            incident = Incident.from_dict(item)
            self.incidents[incident.incident_id] = incident
            if incident.creation_sequence >= self.next_sequence:
                self.next_sequence = incident.creation_sequence + 1

        self._initial_incidents = copy.deepcopy(self.incidents)
        self.recompute_priorities()

    def reset_to_initial(self):
        """Reset incidents to initial scenario state."""
        self.incidents = copy.deepcopy(self._initial_incidents)
        self.recompute_priorities()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.incidents.get(incident_id)

    def get_all_incidents(self) -> List[Incident]:
        return list(self.incidents.values())

    def get_active_incidents(self) -> List[Incident]:
        return [inc for inc in self.incidents.values() if inc.is_active()]

    def get_unassigned_incidents(self) -> List[Incident]:
        return [
            inc for inc in self.incidents.values()
            if inc.is_active() and inc.assigned_team_id is None
        ]

    def add_incident(
        self,
        title: str,
        description: str,
        location_id: str,
        latitude: float,
        longitude: float,
        animal_category: AnimalCategory,
        urgency: int,
        is_vulnerable: bool = False,
        required_skills: Optional[List[str]] = None,
        operator_notes: str = "",
    ) -> Incident:
        """Register a new simulated animal incident."""
        incident_id = f"INC-{100 + len(self.incidents) + 1}"
        # Ensure unique ID
        counter = len(self.incidents) + 1
        while incident_id in self.incidents:
            counter += 1
            incident_id = f"INC-{100 + counter}"

        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            location_id=location_id,
            latitude=latitude,
            longitude=longitude,
            animal_category=animal_category,
            urgency=urgency,
            waiting_time=0.0,
            is_vulnerable=is_vulnerable,
            required_skills=required_skills or [],
            status=IncidentStatus.REPORTED,
            creation_sequence=self.next_sequence,
            operator_notes=operator_notes,
        )
        self.next_sequence += 1
        self.incidents[incident_id] = incident
        self.recompute_priorities()
        return incident

    def update_incident(
        self,
        incident_id: str,
        urgency: Optional[int] = None,
        is_vulnerable: Optional[bool] = None,
        operator_notes: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
    ) -> Incident:
        """Update incident attributes and recalculate priority score."""
        incident = self.incidents.get(incident_id)
        if not incident:
            raise ValidationError(f"Incident '{incident_id}' not found.")

        if urgency is not None:
            if not (1 <= urgency <= 5):
                raise ValidationError("Urgency must be between 1 and 5.")
            incident.urgency = urgency
        if is_vulnerable is not None:
            incident.is_vulnerable = is_vulnerable
        if operator_notes is not None:
            incident.operator_notes = operator_notes
        if required_skills is not None:
            incident.required_skills = list(required_skills)

        self.recompute_priorities()
        return incident

    def update_status(self, incident_id: str, target_status: IncidentStatus, notes: str = ""):
        """Perform validated status transition."""
        incident = self.incidents.get(incident_id)
        if not incident:
            raise ValidationError(f"Incident '{incident_id}' not found.")
        incident.transition_to(target_status, notes)
        self.recompute_priorities()

    def advance_waiting_time(self, minutes: float = 10.0):
        """Increase waiting time for active, unassigned incidents."""
        for inc in self.incidents.values():
            if inc.is_active() and inc.assigned_team_id is None:
                inc.waiting_time += minutes
        self.recompute_priorities()

    def set_priority_weights(self, weights: PriorityWeights):
        """Update scoring policy weights and recalculate queue."""
        self.priority_weights = weights.normalize()
        self.recompute_priorities()

    def recompute_priorities(self) -> List[Incident]:
        """Recalculate priorities and return sorted active queue."""
        active = self.get_active_incidents()
        ranked = self.priority_queue.rebuild_queue(active, self.priority_weights)
        return ranked
