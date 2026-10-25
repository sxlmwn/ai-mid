"""Constraint Satisfaction Problem (CSP) for rescue team dispatch.

Formal CSP formulation:
- Variables X = {I_1, I_2, ..., I_k}: Set of high-priority active rescue incidents.
- Domains D(I_i) = {T_1, T_2, ..., T_m}: Available rescue teams.
- Hard Constraints C:
  1. Availability: Team status must be available / not off duty.
  2. Skill Match: Skills(T) >= RequiredSkills(I).
  3. Category Match: T supports AnimalCategory(I).
  4. Capacity: Total simultaneous assignments to T <= Capacity(T).
  5. Uniqueness: Each incident assigned to at most one team.
  6. Reachability: An open route exists between Team location and Incident location in the road graph.

Heuristics implemented:
- Variable Ordering: Minimum Remaining Values (MRV) - fail-first principle.
- Value Ordering: Deterministic (by team ID) or proximity-based (lowest route cost first).
- Inference: Forward checking with domain pruning.
"""
from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.models.incident import Incident
from rescuemind.models.rescue_team import RescueTeam


@dataclass
class CandidateRejection:
    incident_id: str
    team_id: str
    failed_constraint: str
    explanation: str


@dataclass
class CSPResult:
    is_feasible: bool
    # incident_id -> team_id
    assignment: Dict[str, str] = field(default_factory=dict)
    unassigned: Dict[str, str] = field(default_factory=dict)  # incident_id -> explanation
    rejections: List[CandidateRejection] = field(default_factory=list)
    nodes_explored: int = 0
    backtrack_count: int = 0
    explanation: str = ""


class RescueTeamCSP:
    """CSP Backtracking solver with MRV and Forward Checking."""

    def __init__(
        self,
        incidents: List[Incident],
        teams: List[RescueTeam],
        graph: Optional[RoadGraph] = None,
    ):
        self.incidents = {inc.incident_id: inc for inc in incidents if inc.is_active()}
        self.teams = {t.team_id: copy.deepcopy(t) for t in teams}
        self.graph = graph
        self.rejections: List[CandidateRejection] = []
        self.nodes_explored = 0
        self.backtrack_count = 0

    def check_hard_constraints(self, incident: Incident, team: RescueTeam) -> Tuple[bool, Optional[str], Optional[str]]:
        """Evaluate hard operational constraints for a candidate team on an incident.
        Returns (is_satisfied, constraint_name, explanation).
        """
        # Constraint 1: Availability
        if not team.is_available_for_dispatch():
            return False, "AVAILABILITY", f"Team '{team.name}' has no spare capacity ({len(team.current_assignments)}/{team.capacity}) or is {team.status.value}."

        # Constraint 2: Mandatory Skill Compatibility
        if not team.has_required_skills(incident.required_skills):
            missing = set(incident.required_skills) - set(team.skills)
            return False, "SKILL_DEFICIT", f"Team '{team.name}' lacks mandatory skills: {', '.join(sorted(missing))}."

        # Constraint 3: Animal Category Support
        if not team.can_handle_category(incident.animal_category.value):
            return False, "CATEGORY_MISMATCH", f"Team '{team.name}' is restricted and does not handle category '{incident.animal_category.value}'."

        # Constraint 4: Road Graph Reachability
        if self.graph is not None:
            if not self.graph.route_exists(team.current_location_id, incident.location_id):
                return False, "UNREACHABLE_ROUTE", f"No open road path exists between team at '{team.current_location_id}' and incident at '{incident.location_id}'."

        return True, None, None

    def build_initial_domains(self, variable_ids: List[str]) -> Dict[str, List[str]]:
        """Construct candidate domains for each incident variable."""
        domains: Dict[str, List[str]] = {}
        for inc_id in variable_ids:
            incident = self.incidents[inc_id]
            valid_teams: List[str] = []
            for team_id in sorted(self.teams.keys()):
                team = self.teams[team_id]
                passed, constraint, expl = self.check_hard_constraints(incident, team)
                if passed:
                    valid_teams.append(team_id)
                else:
                    self.rejections.append(CandidateRejection(
                        incident_id=inc_id,
                        team_id=team_id,
                        failed_constraint=constraint or "UNKNOWN",
                        explanation=expl or "Constraint violated.",
                    ))
            domains[inc_id] = valid_teams
        return domains

    def select_unassigned_variable_mrv(
        self,
        unassigned_vars: List[str],
        domains: Dict[str, List[str]],
    ) -> str:
        """Minimum Remaining Values (MRV) heuristic.
        Select variable with fewest remaining legal values.
        Tie-breaker: priority order (earlier index in incident list).
        """
        return min(unassigned_vars, key=lambda var: (len(domains.get(var, [])), self.incidents[var].creation_sequence))

    def solve(self, incident_ids: Optional[List[str]] = None) -> CSPResult:
        """Execute CSP backtracking search with MRV and forward checking."""
        if incident_ids is None:
            target_vars = list(self.incidents.keys())
        else:
            target_vars = [i_id for i_id in incident_ids if i_id in self.incidents]

        if not target_vars:
            return CSPResult(
                is_feasible=True,
                assignment={},
                explanation="No active incidents required assignment.",
            )

        domains = self.build_initial_domains(target_vars)

        # Immediate check: if any incident has 0 eligible candidates, fail-fast
        for var in target_vars:
            if not domains[var]:
                reasons = [r.explanation for r in self.rejections if r.incident_id == var]
                reason_summary = "; ".join(reasons) if reasons else "No qualified teams available."
                return CSPResult(
                    is_feasible=False,
                    assignment={},
                    unassigned={var: f"Domain empty for {var}: {reason_summary}"},
                    rejections=self.rejections,
                    explanation=f"CSP Infeasible: Incident '{var}' has no eligible teams satisfying all hard constraints.",
                )

        assignment: Dict[str, Optional[str]] = {}
        best_assignment: Dict[str, str] = {}
        best_assigned_count = 0

        # Track remaining team capacities: team_id -> remaining_slots
        remaining_capacity: Dict[str, int] = {
            t_id: max(0, t.capacity - len(t.current_assignments))
            for t_id, t in self.teams.items()
        }

        def _evaluate_assignment(curr: Dict[str, Optional[str]]):
            nonlocal best_assignment, best_assigned_count
            assigned_only = {k: v for k, v in curr.items() if v is not None}
            if len(assigned_only) > best_assigned_count:
                best_assigned_count = len(assigned_only)
                best_assignment = dict(assigned_only)

        self._backtrack(
            unassigned_vars=list(target_vars),
            domains=domains,
            assignment=assignment,
            remaining_capacity=remaining_capacity,
            record_best_fn=_evaluate_assignment,
        )

        unassigned_dict: Dict[str, str] = {}
        for v in target_vars:
            if v not in best_assignment:
                reasons = [r.explanation for r in self.rejections if r.incident_id == v]
                if reasons:
                    unassigned_dict[v] = "; ".join(reasons)
                else:
                    unassigned_dict[v] = "All compatible rescue teams were committed to other active missions."

        is_fully_feasible = (len(best_assignment) == len(target_vars))

        return CSPResult(
            is_feasible=is_fully_feasible,
            assignment=best_assignment,
            unassigned=unassigned_dict,
            rejections=self.rejections,
            nodes_explored=self.nodes_explored,
            backtrack_count=self.backtrack_count,
            explanation=(
                f"CSP solver allocated {len(best_assignment)}/{len(target_vars)} incidents "
                f"satisfying all hard constraints ({self.nodes_explored} nodes explored, "
                f"{self.backtrack_count} backtracks)."
            ),
        )

    def _backtrack(
        self,
        unassigned_vars: List[str],
        domains: Dict[str, List[str]],
        assignment: Dict[str, Optional[str]],
        remaining_capacity: Dict[str, int],
        record_best_fn=None,
    ) -> bool:
        """Recursive backtracking procedure with forward checking and partial assignment support."""
        if record_best_fn:
            record_best_fn(assignment)

        if not unassigned_vars:
            # If all target variables are assigned (not None), complete solution found
            return all(assignment.get(v) is not None for v in assignment)

        self.nodes_explored += 1
        # 1. Variable ordering using MRV
        var = self.select_unassigned_variable_mrv(unassigned_vars, domains)
        unassigned_vars_next = [v for v in unassigned_vars if v != var]

        # 2. Value ordering (sorted by team_id for determinism)
        candidate_teams = sorted(domains[var])

        # Try assigning candidate teams first
        for team_id in candidate_teams:
            if remaining_capacity.get(team_id, 0) <= 0:
                continue

            assignment[var] = team_id
            remaining_capacity[team_id] -= 1

            # Forward checking
            pruned: Dict[str, List[str]] = {}
            forward_check_ok = True

            if remaining_capacity[team_id] == 0:
                for other_var in unassigned_vars_next:
                    if team_id in domains[other_var]:
                        if other_var not in pruned:
                            pruned[other_var] = []
                        domains[other_var].remove(team_id)
                        pruned[other_var].append(team_id)

            if forward_check_ok:
                if self._backtrack(
                    unassigned_vars_next,
                    domains,
                    assignment,
                    remaining_capacity,
                    record_best_fn=record_best_fn,
                ):
                    return True

            # Backtrack
            self.backtrack_count += 1
            del assignment[var]
            remaining_capacity[team_id] += 1
            for other_var, restored_teams in pruned.items():
                domains[other_var].extend(restored_teams)

        # 3. Also allow leaving var unassigned (None) so bottlenecked incidents do not block other independent rescues
        assignment[var] = None
        if self._backtrack(
            unassigned_vars_next,
            domains,
            assignment,
            remaining_capacity,
            record_best_fn=record_best_fn,
        ):
            return True
        del assignment[var]

        return False
