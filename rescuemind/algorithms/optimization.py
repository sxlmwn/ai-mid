"""Branch-and-Bound (B&B) optimization for cost-optimal rescue team dispatch.

Problem Formulation:
- Given: A set of active incidents I and candidate rescue teams T.
- Goal: Find a feasible assignment A: I -> T that minimizes the total dispatch travel cost:
    Minimize Objective = Sum_{(i, t) in A} Cost(t, i)
- Subject to all hard operational constraints (availability, skills, animal category, capacity, reachability).
- Branch-and-Bound Strategy:
  - Branching: Assign next incident to each eligible candidate team.
  - Lower Bound (Admissible):
      LB(remaining) = Sum_{i in unassigned} min_{t eligible} Cost(t, i)
  - Pruning Rule:
      If (accumulated_cost + LB(remaining) >= best_cost_found), PRUNE branch.
"""
from __future__ import annotations
import collections
import copy
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.algorithms.search import ucs_search
from rescuemind.models.incident import Incident
from rescuemind.models.rescue_team import RescueTeam


@dataclass
class OptimizationResult:
    is_feasible: bool
    assignment: Dict[str, str]  # incident_id -> team_id
    total_cost: float
    nodes_explored: int
    branches_pruned: int
    runtime_ms: float
    optimal_guaranteed: bool
    explanation: str
    all_candidate_costs: Dict[str, Dict[str, float]] = field(default_factory=dict)


class BranchAndBoundAssigner:
    """Branch-and-Bound optimizer for global dispatch travel-cost minimization."""

    def __init__(
        self,
        incidents: List[Incident],
        teams: List[RescueTeam],
        graph: RoadGraph,
    ):
        self.incidents = [inc for inc in incidents if inc.is_active()]
        self.teams = copy.deepcopy(teams)
        self.graph = graph
        self.cost_matrix: Dict[str, Dict[str, float]] = {}  # incident_id -> {team_id: cost}
        self.explored_nodes = 0
        self.branches_pruned = 0
        self._precompute_cost_matrix()

    def _precompute_cost_matrix(self):
        """Precompute UCS shortest path costs between all eligible (team, incident) pairs."""
        for inc in self.incidents:
            self.cost_matrix[inc.incident_id] = {}
            for team in self.teams:
                # Check hard constraints
                if not team.is_available_for_dispatch():
                    continue
                if not team.has_required_skills(inc.required_skills):
                    continue
                if not team.can_handle_category(inc.animal_category.value):
                    continue

                route = ucs_search(self.graph, team.current_location_id, inc.location_id)
                if route.success:
                    self.cost_matrix[inc.incident_id][team.team_id] = route.cost

    def _compute_lower_bound(self, remaining_incidents: List[str]) -> float:
        """Calculate admissible lower bound: sum of minimum possible costs for remaining incidents."""
        lb = 0.0
        for inc_id in remaining_incidents:
            costs = self.cost_matrix.get(inc_id, {}).values()
            if costs:
                lb += min(costs)
            else:
                # If an incident has no reachable team, lower bound is effectively infinite
                return float("inf")
        return lb

    def solve(self) -> OptimizationResult:
        """Run Branch-and-Bound search to find the minimum-cost team assignment."""
        import time
        t0 = time.perf_counter()

        if not self.incidents:
            return OptimizationResult(
                is_feasible=True,
                assignment={},
                total_cost=0.0,
                nodes_explored=0,
                branches_pruned=0,
                runtime_ms=0.0,
                optimal_guaranteed=True,
                explanation="No active incidents to optimize.",
                all_candidate_costs=self.cost_matrix,
            )

        incident_ids = [inc.incident_id for inc in self.incidents]

        # Verify every incident has at least one candidate
        for inc_id in incident_ids:
            if not self.cost_matrix.get(inc_id):
                runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
                return OptimizationResult(
                    is_feasible=False,
                    assignment={},
                    total_cost=float("inf"),
                    nodes_explored=0,
                    branches_pruned=0,
                    runtime_ms=runtime_ms,
                    optimal_guaranteed=False,
                    explanation=f"Cannot optimize: Incident '{inc_id}' has no reachable, qualified teams.",
                    all_candidate_costs=self.cost_matrix,
                )

        best_assignment: Optional[Dict[str, str]] = None
        best_cost = float("inf")
        remaining_capacity = {t.team_id: t.capacity - len(t.current_assignments) for t in self.teams}

        self.explored_nodes = 0
        self.branches_pruned = 0

        def _branch(
            index: int,
            current_cost: float,
            current_assignment: Dict[str, str],
            capacity_left: Dict[str, int],
        ):
            nonlocal best_cost, best_assignment
            self.explored_nodes += 1

            if index == len(incident_ids):
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_assignment = dict(current_assignment)
                return

            inc_id = incident_ids[index]
            remaining = incident_ids[index + 1:]
            lower_bound = self._compute_lower_bound(remaining)

            # Pruning condition
            if current_cost + lower_bound >= best_cost:
                self.branches_pruned += 1
                return

            candidates = sorted(
                self.cost_matrix[inc_id].items(),
                key=lambda item: item[1]  # branch towards lower costs first
            )

            for team_id, cost in candidates:
                if capacity_left.get(team_id, 0) > 0:
                    current_assignment[inc_id] = team_id
                    capacity_left[team_id] -= 1

                    _branch(
                        index + 1,
                        current_cost + cost,
                        current_assignment,
                        capacity_left,
                    )

                    del current_assignment[inc_id]
                    capacity_left[team_id] += 1

        _branch(0, 0.0, {}, remaining_capacity)

        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        if best_assignment is not None:
            return OptimizationResult(
                is_feasible=True,
                assignment=best_assignment,
                total_cost=round(best_cost, 3),
                nodes_explored=self.explored_nodes,
                branches_pruned=self.branches_pruned,
                runtime_ms=runtime_ms,
                optimal_guaranteed=True,
                explanation=(
                    f"Branch-and-Bound found cost-optimal assignment with minimum total travel cost {round(best_cost, 3)}. "
                    f"Explored {self.explored_nodes} states and successfully pruned {self.branches_pruned} suboptimal branches."
                ),
                all_candidate_costs=self.cost_matrix,
            )
        else:
            return OptimizationResult(
                is_feasible=False,
                assignment={},
                total_cost=float("inf"),
                nodes_explored=self.explored_nodes,
                branches_pruned=self.branches_pruned,
                runtime_ms=runtime_ms,
                optimal_guaranteed=False,
                explanation="No assignment could satisfy all capacity and capability constraints simultaneously.",
                all_candidate_costs=self.cost_matrix,
            )

    def solve_exhaustive(self) -> Tuple[Optional[Dict[str, str]], float]:
        """Exhaustive brute-force enumeration for testing and mathematical optimality verification."""
        incident_ids = [inc.incident_id for inc in self.incidents]
        candidate_lists = [list(self.cost_matrix.get(inc_id, {}).keys()) for inc_id in incident_ids]

        if any(len(c) == 0 for c in candidate_lists):
            return None, float("inf")

        best_cost = float("inf")
        best_assignment: Optional[Dict[str, str]] = None
        base_capacities = {t.team_id: t.capacity - len(t.current_assignments) for t in self.teams}

        for combination in itertools.product(*candidate_lists):
            # Check team capacity
            counts = collections.Counter(combination)
            if any(counts[tid] > base_capacities.get(tid, 0) for tid in counts):
                continue
            total_c = sum(self.cost_matrix[inc_id][tid] for inc_id, tid in zip(incident_ids, combination))
            if total_c < best_cost:
                best_cost = total_c
                best_assignment = dict(zip(incident_ids, combination))

        return best_assignment, round(best_cost, 3) if best_assignment else float("inf")
