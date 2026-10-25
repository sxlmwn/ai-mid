"""Incident priority scoring and priority queue implementation."""
from __future__ import annotations
import heapq
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from rescuemind.models.incident import Incident, IncidentStatus
from rescuemind.utils.constants import (
    DEFAULT_WEIGHT_URGENCY,
    DEFAULT_WEIGHT_WAITING,
    DEFAULT_WEIGHT_VULNERABILITY,
)


@dataclass
class PriorityWeights:
    weight_urgency: float = DEFAULT_WEIGHT_URGENCY
    weight_waiting: float = DEFAULT_WEIGHT_WAITING
    weight_vulnerability: float = DEFAULT_WEIGHT_VULNERABILITY
    max_waiting_minutes: float = 60.0  # Time at which waiting penalty saturates

    def normalize(self) -> PriorityWeights:
        """Ensure sum of weights equals 1.0."""
        total = self.weight_urgency + self.weight_waiting + self.weight_vulnerability
        if total <= 0:
            return PriorityWeights(0.45, 0.35, 0.20)
        return PriorityWeights(
            weight_urgency=round(self.weight_urgency / total, 4),
            weight_waiting=round(self.weight_waiting / total, 4),
            weight_vulnerability=round(self.weight_vulnerability / total, 4),
            max_waiting_minutes=self.max_waiting_minutes,
        )


def calculate_incident_score(incident: Incident, weights: PriorityWeights) -> Tuple[float, Dict[str, float]]:
    """Compute transparent multi-factor priority score on a 0.0 - 100.0 scale.
    Formula:
        Score = 100 * [
            w_urgency * (urgency / 5.0) +
            w_waiting * min(waiting_time / max_wait, 1.0) +
            w_vulnerability * (1.0 if is_vulnerable else 0.0)
        ]
    """
    w = weights.normalize()
    urgency_ratio = min(max(incident.urgency / 5.0, 0.0), 1.0)
    waiting_ratio = min(max(incident.waiting_time / max(w.max_waiting_minutes, 1.0), 0.0), 1.0)
    vuln_ratio = 1.0 if incident.is_vulnerable else 0.0

    urgency_pts = round(100.0 * w.weight_urgency * urgency_ratio, 2)
    waiting_pts = round(100.0 * w.weight_waiting * waiting_ratio, 2)
    vuln_pts = round(100.0 * w.weight_vulnerability * vuln_ratio, 2)

    total_score = round(urgency_pts + waiting_pts + vuln_pts, 2)
    breakdown = {
        "urgency_contribution": urgency_pts,
        "waiting_contribution": waiting_pts,
        "vulnerability_contribution": vuln_pts,
        "urgency_raw": incident.urgency,
        "waiting_minutes": round(incident.waiting_time, 1),
        "is_vulnerable": incident.is_vulnerable,
    }
    return total_score, breakdown


class IncidentPriorityQueue:
    """Deterministic min-heap priority queue storing (-score, creation_seq, incident_id, incident)."""

    def __init__(self, weights: Optional[PriorityWeights] = None):
        self.weights = weights or PriorityWeights()
        self._heap: List[Tuple[float, int, str, Incident]] = []

    def push(self, incident: Incident):
        """Add incident to queue if eligible (active, not resolved/cancelled)."""
        if not incident.is_active():
            return
        score, breakdown = calculate_incident_score(incident, self.weights)
        incident.priority_score = score
        incident.priority_breakdown = breakdown

        # Python heapq is a min-heap; negate score for highest priority first
        entry = (-score, incident.creation_sequence, incident.incident_id, incident)
        heapq.heappush(self._heap, entry)

    def pop(self) -> Optional[Incident]:
        """Pop and return the highest priority incident."""
        while self._heap:
            _, _, _, incident = heapq.heappop(self._heap)
            if incident.is_active():
                return incident
        return None

    def rebuild_queue(self, incidents: List[Incident], weights: Optional[PriorityWeights] = None) -> List[Incident]:
        """Recalculate priorities and return sorted list of active incidents."""
        if weights:
            self.weights = weights
        self._heap.clear()
        for inc in incidents:
            if inc.is_active():
                self.push(inc)

        # Extract in strict priority order
        ranked: List[Incident] = []
        temp_heap = list(self._heap)
        while temp_heap:
            _, _, _, incident = heapq.heappop(temp_heap)
            if incident.is_active():
                ranked.append(incident)
        return ranked

    @staticmethod
    def explain_priority_difference(inc_a: Incident, inc_b: Incident) -> str:
        """Generate human-readable transparent explanation of why inc_a is prioritized over inc_b."""
        score_a = inc_a.priority_score
        score_b = inc_b.priority_score

        if score_a > score_b:
            diff = round(score_a - score_b, 2)
            reasons = []
            if inc_a.urgency > inc_b.urgency:
                reasons.append(f"higher reported urgency ({inc_a.urgency}/5 vs {inc_b.urgency}/5)")
            if inc_a.waiting_time > inc_b.waiting_time:
                reasons.append(f"longer waiting time ({round(inc_a.waiting_time, 1)}m vs {round(inc_b.waiting_time, 1)}m)")
            if inc_a.is_vulnerable and not inc_b.is_vulnerable:
                reasons.append("special vulnerability flag is active")

            reason_str = ", ".join(reasons) if reasons else "higher weighted multi-factor evaluation"
            return (
                f"Incident '{inc_a.incident_id}' ({score_a} pts) ranked ahead of '{inc_b.incident_id}' "
                f"({score_b} pts) by {diff} points due to {reason_str}."
            )
        elif score_a == score_b:
            return (
                f"Incidents '{inc_a.incident_id}' and '{inc_b.incident_id}' have identical scores "
                f"({score_a} pts). Tied resolved deterministically by earlier registration sequence "
                f"(seq {inc_a.creation_sequence} vs {inc_b.creation_sequence})."
            )
        else:
            return f"Incident '{inc_b.incident_id}' has higher priority than '{inc_a.incident_id}'."
