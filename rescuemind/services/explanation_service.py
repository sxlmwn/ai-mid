"""Explanation service generating evidence-grounded, human-readable rationale."""
from __future__ import annotations
from typing import Dict, List, Optional
from rescuemind.algorithms.priority import IncidentPriorityQueue
from rescuemind.models.dispatch import DispatchAssignment, DispatchPlan, RouteResult
from rescuemind.models.incident import Incident
from rescuemind.models.rescue_team import RescueTeam
from rescuemind.utils.constants import DISCLAIMER_TEXT


class ExplanationService:
    """Generates transparent, student-defensible explanations directly from algorithm outputs."""

    @staticmethod
    def explain_priority_queue(ranked_incidents: List[Incident]) -> List[str]:
        """Explain the rationale behind the ordering in the active priority queue."""
        explanations = []
        for i in range(len(ranked_incidents)):
            inc = ranked_incidents[i]
            bd = inc.priority_breakdown
            text = (
                f"#{i+1}: Incident {inc.incident_id} ('{inc.title}') scored {inc.priority_score:.1f} pts "
                f"[Urgency: {bd.get('urgency_contribution', 0.0):.1f} pts, "
                f"Wait: {bd.get('waiting_contribution', 0.0):.1f} pts ({bd.get('waiting_minutes', 0.0):.0f} min), "
                f"Vulnerability: {bd.get('vulnerability_contribution', 0.0):.1f} pts]."
            )
            explanations.append(text)
        return explanations

    @staticmethod
    def explain_assignment(
        incident: Incident,
        team: RescueTeam,
        route: Optional[RouteResult],
        is_optimized: bool = False,
    ) -> str:
        """Explain why a team was dispatched to a specific incident."""
        route_text = (
            f"via optimal route { ' -> '.join(route.path) } (cost: {route.cost:.1f}, time: {route.travel_time:.1f}m)"
            if route and route.success else "with route pending confirmation"
        )
        optimization_note = (
            "Selected via Branch-and-Bound global travel-cost optimization."
            if is_optimized else
            "Selected via CSP backtracking satisfying all operational constraints."
        )

        return (
            f"Assigned Team '{team.name}' ({team.team_id}) to Incident {incident.incident_id} ('{incident.title}'). "
            f"Team met all mandatory skill requirements ({', '.join(incident.required_skills) or 'none required'}), "
            f"had available capacity ({len(team.current_assignments)}/{team.capacity}), and dispatched {route_text}. "
            f"{optimization_note}"
        )

    @staticmethod
    def explain_unassigned(incident: Incident, reason: str) -> str:
        """Explain why an incident remained unassigned."""
        return (
            f"Incident {incident.incident_id} ('{incident.title}', Priority: {incident.priority_score:.1f}) "
            f"remains unassigned: {reason}"
        )

    @staticmethod
    def explain_replan(
        incident_id: str,
        team_name: str,
        old_route: Optional[RouteResult],
        new_route: Optional[RouteResult],
        blocked_road_desc: str,
    ) -> str:
        """Explain route replanning following a road network disruption."""
        if not new_route or not new_route.success:
            return (
                f"Disruption alert: Road blockage ({blocked_road_desc}) severed the active route for Team '{team_name}' "
                f"to Incident {incident_id}. No alternative open route exists in the network. "
                f"Action: Team recall recommended."
            )

        cost_diff = round(new_route.cost - (old_route.cost if old_route else 0.0), 2)
        diff_str = f"+{cost_diff}" if cost_diff >= 0 else f"{cost_diff}"
        return (
            f"Route replanned for Team '{team_name}' to Incident {incident_id} following disruption ({blocked_road_desc}). "
            f"New detour path: {' -> '.join(new_route.path)}. Route cost adjusted to {new_route.cost:.1f} ({diff_str} km)."
        )

    @staticmethod
    def get_disclaimer() -> str:
        """Return research and educational simulator disclaimer."""
        return DISCLAIMER_TEXT
