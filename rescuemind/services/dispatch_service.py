"""Dispatch service coordinating prioritization, CSP assignment, optimization, and routing."""
from __future__ import annotations
import copy
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rescuemind.algorithms.assignment import RescueTeamCSP, CSPResult
from rescuemind.algorithms.optimization import BranchAndBoundAssigner, OptimizationResult
from rescuemind.models.dispatch import DispatchAssignment, DispatchPlan, RouteResult
from rescuemind.models.incident import Incident, IncidentStatus
from rescuemind.models.rescue_team import RescueTeam, TeamStatus
from rescuemind.services.explanation_service import ExplanationService
from rescuemind.services.incident_service import IncidentService
from rescuemind.services.routing_service import RoutingService
from rescuemind.utils.validators import ValidationError


class DispatchService:
    """Central coordinator orchestrating multi-algorithm rescue planning."""

    def __init__(
        self,
        incident_service: IncidentService,
        routing_service: RoutingService,
        teams_data_path: Optional[Path] = None,
    ):
        self.incident_service = incident_service
        self.routing_service = routing_service
        self.teams: Dict[str, RescueTeam] = {}
        self._initial_teams: Dict[str, RescueTeam] = {}
        self.current_plan: Optional[DispatchPlan] = None
        self.previous_plan: Optional[DispatchPlan] = None
        self.planning_horizon: int = 5  # Max incidents considered per planning batch
        self.routing_algorithm: str = "A*"
        self.plan_counter = 1

        if teams_data_path:
            self.load_teams_from_json(teams_data_path)

    def load_teams_from_json(self, file_path: Path):
        """Load rescue teams from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.teams.clear()
        for item in data.get("teams", []):
            team = RescueTeam.from_dict(item)
            self.teams[team.team_id] = team

        self._initial_teams = copy.deepcopy(self.teams)

    def reset_to_initial(self):
        """Reset teams and plans to initial state."""
        self.teams = copy.deepcopy(self._initial_teams)
        self.current_plan = None
        self.previous_plan = None
        self.plan_counter = 1

    def get_team(self, team_id: str) -> Optional[RescueTeam]:
        return self.teams.get(team_id)

    def get_all_teams(self) -> List[RescueTeam]:
        return list(self.teams.values())

    def get_available_teams(self) -> List[RescueTeam]:
        return [t for t in self.teams.values() if t.is_available_for_dispatch()]

    def update_team_status(self, team_id: str, new_status: TeamStatus):
        """Update team status."""
        team = self.teams.get(team_id)
        if not team:
            raise ValidationError(f"Team '{team_id}' not found.")
        team.status = new_status

    def update_team_location(self, team_id: str, new_node_id: str):
        """Relocate team to a different graph node."""
        team = self.teams.get(team_id)
        if not team:
            raise ValidationError(f"Team '{team_id}' not found.")
        node = self.routing_service.get_node(new_node_id)
        if not node:
            raise ValidationError(f"Graph node '{new_node_id}' does not exist.")
        team.current_location_id = new_node_id
        team.latitude = node.latitude
        team.longitude = node.longitude

    def run_dispatch_cycle(
        self,
        use_optimization: bool = False,
        routing_algo: Optional[str] = None,
    ) -> DispatchPlan:
        """Execute a full AI dispatch coordination cycle:
        1. Priority queue ranking of active incidents.
        2. Windowing to planning horizon.
        3. CSP feasibility check / Branch-and-Bound optimization.
        4. Route calculation for each assigned pair.
        5. Explainability generation.
        """
        algo_name = routing_algo or self.routing_algorithm
        self.routing_algorithm = algo_name

        # 1. Prioritize active incidents
        ranked_incidents = self.incident_service.recompute_priorities()
        target_incidents = ranked_incidents[:self.planning_horizon]

        # Archive current plan before overwriting
        if self.current_plan:
            self.previous_plan = copy.deepcopy(self.current_plan)

        assignments_list: List[DispatchAssignment] = []
        unassigned_map: Dict[str, str] = {}
        explanations: List[str] = []
        total_cost = 0.0

        if not target_incidents:
            plan = DispatchPlan(
                plan_id=f"PLAN-{self.plan_counter}",
                timestamp=int(time.time()),
                assignments=[],
                unassigned_incidents={},
                total_cost=0.0,
                algorithm_used="None (No active incidents)",
                explanations=["No active incidents awaiting dispatch."],
            )
            self.plan_counter += 1
            self.current_plan = plan
            return plan

        # 2. Assignment via Branch-and-Bound or CSP
        if use_optimization:
            optimizer = BranchAndBoundAssigner(
                incidents=target_incidents,
                teams=list(self.teams.values()),
                graph=self.routing_service.graph,
            )
            opt_result = optimizer.solve()
            assigned_pairs = opt_result.assignment
            algorithm_label = "Branch-and-Bound Optimization"
            explanations.append(opt_result.explanation)
        else:
            csp = RescueTeamCSP(
                incidents=target_incidents,
                teams=list(self.teams.values()),
                graph=self.routing_service.graph,
            )
            csp_result = csp.solve([inc.incident_id for inc in target_incidents])
            assigned_pairs = csp_result.assignment
            unassigned_map.update(csp_result.unassigned)
            algorithm_label = "CSP Backtracking with MRV & Forward Checking"
            explanations.append(csp_result.explanation)

        # Clear existing simulated active assignments from teams before applying new plan
        for t in self.teams.values():
            t.current_assignments.clear()
            if t.status == TeamStatus.DISPATCHED:
                t.status = TeamStatus.AVAILABLE

        # 3. Process assigned incidents
        for inc_id, team_id in assigned_pairs.items():
            incident = self.incident_service.get_incident(inc_id)
            team = self.teams.get(team_id)
            if not incident or not team:
                continue

            # Calculate route from team current location to incident location
            route = self.routing_service.calculate_route(
                start=team.current_location_id,
                goal=incident.location_id,
                algorithm=algo_name,
            )

            # Apply state update
            team.assign_incident(inc_id)
            incident.assigned_team_id = team_id
            incident.status = IncidentStatus.ASSIGNED
            incident.estimated_cost = route.cost if route.success else None
            incident.estimated_time = route.travel_time if route.success else None

            assignment = DispatchAssignment(
                incident_id=inc_id,
                team_id=team_id,
                route=route,
                cost=route.cost if route.success else 0.0,
                feasibility_checks={
                    "availability": True,
                    "skills_verified": True,
                    "category_supported": True,
                    "capacity_respected": True,
                    "route_found": route.success,
                },
                notes=f"Route calculated via {algo_name}",
            )
            assignments_list.append(assignment)
            total_cost += assignment.cost

            expl = ExplanationService.explain_assignment(
                incident=incident,
                team=team,
                route=route,
                is_optimized=use_optimization,
            )
            explanations.append(expl)

        # 4. Process unassigned incidents in planning horizon
        for inc in target_incidents:
            if inc.incident_id not in assigned_pairs:
                if inc.incident_id not in unassigned_map:
                    unassigned_map[inc.incident_id] = "No available qualified rescue team could be allocated."
                inc.assigned_team_id = None
                if inc.status == IncidentStatus.ASSIGNED:
                    inc.status = IncidentStatus.ASSESSED
                expl = ExplanationService.explain_unassigned(inc, unassigned_map[inc.incident_id])
                explanations.append(expl)

        plan = DispatchPlan(
            plan_id=f"PLAN-{self.plan_counter}",
            timestamp=int(time.time()),
            assignments=assignments_list,
            unassigned_incidents=unassigned_map,
            total_cost=round(total_cost, 2),
            algorithm_used=algorithm_label,
            explanations=explanations,
        )
        self.plan_counter += 1
        self.current_plan = plan
        return plan

    def replan_disrupted_routes(self, u: str, v: str) -> List[str]:
        """Check all active assignments; if any route traversed (u, v), recalculate detour."""
        if not self.current_plan:
            return ["No active dispatch plan currently running."]

        replan_notes: List[str] = []
        blocked_desc = f"{u} <-> {v}"

        for assignment in self.current_plan.assignments:
            if assignment.route and assignment.route.success:
                if self.routing_service.route_contains_edge(assignment.route.path, u, v):
                    # Route is severed! Replan
                    team = self.teams.get(assignment.team_id)
                    incident = self.incident_service.get_incident(assignment.incident_id)
                    if team and incident:
                        old_route = copy.deepcopy(assignment.route)
                        new_route = self.routing_service.calculate_route(
                            start=team.current_location_id,
                            goal=incident.location_id,
                            algorithm=self.routing_algorithm,
                        )
                        assignment.route = new_route
                        assignment.cost = new_route.cost if new_route.success else float("inf")
                        incident.estimated_cost = new_route.cost if new_route.success else None
                        incident.estimated_time = new_route.travel_time if new_route.success else None

                        note = ExplanationService.explain_replan(
                            incident_id=incident.incident_id,
                            team_name=team.name,
                            old_route=old_route,
                            new_route=new_route,
                            blocked_road_desc=blocked_desc,
                        )
                        replan_notes.append(note)

        # Update total plan cost
        self.current_plan.total_cost = round(
            sum(a.cost for a in self.current_plan.assignments if a.route and a.route.success), 2
        )
        return replan_notes
