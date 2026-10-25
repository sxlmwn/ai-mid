"""Tests for Branch-and-Bound optimization validated against exhaustive enumeration."""
import pytest
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.algorithms.optimization import BranchAndBoundAssigner
from rescuemind.models.incident import Incident, AnimalCategory
from rescuemind.models.rescue_team import RescueTeam
from rescuemind.models.road import GraphNode, RoadEdge


@pytest.fixture
def small_optimization_world():
    graph = RoadGraph()
    # 4 nodes: Base 1 (B1), Base 2 (B2), Incident 1 (I1), Incident 2 (I2)
    # Distances designed so:
    # B1 -> I1 cost 2.0, B1 -> I2 cost 8.0
    # B2 -> I1 cost 7.0, B2 -> I2 cost 3.0
    nodes = [
        GraphNode("B1", "Base 1", 33.70, 73.00),
        GraphNode("B2", "Base 2", 33.60, 73.10),
        GraphNode("LOC1", "Location 1", 33.71, 73.01),
        GraphNode("LOC2", "Location 2", 33.61, 73.09),
    ]
    for n in nodes:
        graph.add_node(n)

    graph.add_edge(RoadEdge("B1", "LOC1", 2.0, 2.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("B1", "LOC2", 8.0, 8.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("B2", "LOC1", 7.0, 7.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("B2", "LOC2", 3.0, 3.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("LOC1", "LOC2", 10.0, 10.0, is_bidirectional=True))

    teams = [
        RescueTeam("T1", "Team 1", "B1", "B1", 33.70, 73.00, skills=["transport"], capacity=1),
        RescueTeam("T2", "Team 2", "B2", "B2", 33.60, 73.10, skills=["transport"], capacity=1),
    ]

    incidents = [
        Incident("INC1", "Inc 1", "desc", "LOC1", 33.71, 73.01, AnimalCategory.DOG, 3, required_skills=["transport"]),
        Incident("INC2", "Inc 2", "desc", "LOC2", 33.61, 73.09, AnimalCategory.DOG, 3, required_skills=["transport"]),
    ]

    return graph, teams, incidents


def test_branch_and_bound_optimality_matches_exhaustive(small_optimization_world):
    """Verify B&B finds the exact same optimal assignment and minimum cost as exhaustive brute-force."""
    graph, teams, incidents = small_optimization_world

    optimizer = BranchAndBoundAssigner(incidents, teams, graph)
    bb_res = optimizer.solve()
    ex_assignment, ex_cost = optimizer.solve_exhaustive()

    assert bb_res.is_feasible is True
    # B1 to LOC1 (2.0) + B2 to LOC2 (3.0) = 5.0
    # Cross assignment B1 to LOC2 (8.0) + B2 to LOC1 (7.0) = 15.0
    assert bb_res.total_cost == 5.0
    assert bb_res.assignment == {"INC1": "T1", "INC2": "T2"}

    # Mathematical equivalence check
    assert bb_res.total_cost == ex_cost
    assert bb_res.assignment == ex_assignment


def test_branch_and_bound_infeasible(small_optimization_world):
    graph, teams, incidents = small_optimization_world
    # Require an impossible skill
    incidents[0].required_skills = ["water_rescue"]

    optimizer = BranchAndBoundAssigner(incidents, teams, graph)
    res = optimizer.solve()

    assert res.is_feasible is False
    assert len(res.assignment) == 0
