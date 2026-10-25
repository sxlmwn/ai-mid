"""Metrics and analytical evaluation service for rescue operations."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from rescuemind.algorithms.comparison import run_all_search_algorithms, summarize_comparison
from rescuemind.models.dispatch import DispatchPlan
from rescuemind.services.dispatch_service import DispatchService
from rescuemind.services.incident_service import IncidentService
from rescuemind.services.routing_service import RoutingService


class MetricsService:
    """Computes transparent empirical evaluation metrics directly from running simulation state."""

    def __init__(
        self,
        incident_service: IncidentService,
        dispatch_service: DispatchService,
        routing_service: RoutingService,
    ):
        self.incident_service = incident_service
        self.dispatch_service = dispatch_service
        self.routing_service = routing_service

    def get_summary_kpis(self) -> Dict[str, Any]:
        """Core top-level Key Performance Indicators."""
        all_incidents = self.incident_service.get_all_incidents()
        active = self.incident_service.get_active_incidents()
        unassigned = self.incident_service.get_unassigned_incidents()
        teams = self.dispatch_service.get_all_teams()
        available_teams = self.dispatch_service.get_available_teams()

        assigned_count = len(active) - len(unassigned)
        coverage_pct = round((assigned_count / len(active) * 100.0), 1) if active else 100.0

        current_plan = self.dispatch_service.current_plan
        total_plan_cost = current_plan.total_cost if current_plan else 0.0

        blocked_count = sum(1 for e in self.routing_service.get_all_edges() if not e.is_open)

        return {
            "total_incidents": len(all_incidents),
            "active_incidents": len(active),
            "unassigned_incidents": len(unassigned),
            "coverage_rate_pct": coverage_pct,
            "total_teams": len(teams),
            "available_teams": len(available_teams),
            "blocked_roads": blocked_count,
            "current_plan_cost": total_plan_cost,
        }

    def get_priority_distribution(self) -> Dict[str, Any]:
        """Urgency level distribution and average score."""
        active = self.incident_service.get_active_incidents()
        urgency_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for inc in active:
            urgency_counts[inc.urgency] = urgency_counts.get(inc.urgency, 0) + 1

        avg_score = (
            round(sum(inc.priority_score for inc in active) / len(active), 2)
            if active else 0.0
        )
        return {
            "urgency_counts": urgency_counts,
            "average_priority_score": avg_score,
        }

    def evaluate_search_benchmark(self, start: str, goal: str) -> List[Dict[str, Any]]:
        """Run all 5 search algorithms between endpoints and return comparative summary."""
        results = run_all_search_algorithms(self.routing_service.graph, start, goal)
        return summarize_comparison(results)

    def compare_csp_vs_optimization(self) -> Dict[str, Any]:
        """Compare basic CSP feasible solution against Branch-and-Bound optimal solution."""
        active = self.incident_service.get_active_incidents()[:self.dispatch_service.planning_horizon]
        teams = self.dispatch_service.get_all_teams()
        graph = self.routing_service.graph

        from rescuemind.algorithms.assignment import RescueTeamCSP
        from rescuemind.algorithms.optimization import BranchAndBoundAssigner

        csp = RescueTeamCSP(active, teams, graph)
        csp_res = csp.solve([i.incident_id for i in active])

        # Calculate CSP total travel cost
        csp_cost = 0.0
        for inc_id, t_id in csp_res.assignment.items():
            inc = self.incident_service.get_incident(inc_id)
            team = self.dispatch_service.get_team(t_id)
            if inc and team:
                route = self.routing_service.calculate_route(team.current_location_id, inc.location_id, "A*")
                if route.success:
                    csp_cost += route.cost

        optimizer = BranchAndBoundAssigner(active, teams, graph)
        opt_res = optimizer.solve()

        savings = round(csp_cost - opt_res.total_cost, 2) if opt_res.is_feasible else 0.0

        return {
            "csp_feasible": csp_res.is_feasible,
            "csp_assignments": csp_res.assignment,
            "csp_total_cost": round(csp_cost, 2),
            "csp_nodes_explored": csp_res.nodes_explored,
            "opt_feasible": opt_res.is_feasible,
            "opt_assignments": opt_res.assignment,
            "opt_total_cost": opt_res.total_cost,
            "opt_nodes_explored": opt_res.nodes_explored,
            "opt_branches_pruned": opt_res.branches_pruned,
            "cost_reduction_km": max(0.0, savings),
        }
