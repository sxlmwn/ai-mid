"""Dispatch and routing result models."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RouteResult:
    algorithm_name: str
    path: List[str]  # ordered list of node IDs
    cost: float  # total travel cost
    travel_time: float  # total estimated travel time
    explored_nodes: int  # count of explored/expanded nodes
    generated_nodes: int  # count of generated/pushed nodes
    runtime_ms: float  # execution time in milliseconds
    success: bool
    explanation: str
    step_trace: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def edge_count(self) -> int:
        return max(0, len(self.path) - 1) if self.success else 0

    def to_dict(self) -> dict:
        return {
            "algorithm_name": self.algorithm_name,
            "path": list(self.path),
            "cost": self.cost,
            "travel_time": self.travel_time,
            "edge_count": self.edge_count,
            "explored_nodes": self.explored_nodes,
            "generated_nodes": self.generated_nodes,
            "runtime_ms": self.runtime_ms,
            "success": self.success,
            "explanation": self.explanation,
        }


@dataclass
class DispatchAssignment:
    incident_id: str
    team_id: str
    route: Optional[RouteResult] = None
    cost: float = 0.0
    feasibility_checks: Dict[str, bool] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "team_id": self.team_id,
            "cost": self.cost,
            "feasibility_checks": self.feasibility_checks,
            "notes": self.notes,
            "route": self.route.to_dict() if self.route else None,
        }


@dataclass
class DispatchPlan:
    plan_id: str
    timestamp: int
    assignments: List[DispatchAssignment] = field(default_factory=list)
    unassigned_incidents: Dict[str, str] = field(default_factory=dict)  # incident_id -> rejection reason
    total_cost: float = 0.0
    algorithm_used: str = "CSP_Backtracking"
    explanations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "timestamp": self.timestamp,
            "assignments": [a.to_dict() for a in self.assignments],
            "unassigned_incidents": dict(self.unassigned_incidents),
            "total_cost": self.total_cost,
            "algorithm_used": self.algorithm_used,
            "explanations": list(self.explanations),
        }
