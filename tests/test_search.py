"""Tests for manual AI search algorithms: BFS, DFS, UCS, A*, and Greedy."""
import pytest
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.algorithms.search import (
    bfs_search,
    dfs_search,
    ucs_search,
    a_star_search,
    greedy_best_first_search,
)
from rescuemind.models.road import GraphNode, RoadEdge


@pytest.fixture
def classic_search_graph():
    """Graph designed specifically to contrast BFS hop-count vs UCS/A* minimum cost."""
    graph = RoadGraph()
    # A (start) at (33.70, 73.00), B at (33.70, 73.02), C at (33.70, 73.04), D (goal) at (33.70, 73.06)
    nodes = [
        GraphNode("A", "Node A", 33.70, 73.00),
        GraphNode("B", "Node B", 33.70, 73.02),
        GraphNode("C", "Node C", 33.70, 73.04),
        GraphNode("D", "Node D", 33.70, 73.06),
        GraphNode("HIGHWAY_HOP", "Highway Single Hop", 33.72, 73.03),
    ]
    for n in nodes:
        graph.add_node(n)

    # Path 1 (Few edges, very high cost): A -> HIGHWAY_HOP -> D (2 edges, total cost 20)
    graph.add_edge(RoadEdge("A", "HIGHWAY_HOP", 10.0, 10.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("HIGHWAY_HOP", "D", 10.0, 10.0, is_bidirectional=True))

    # Path 2 (More edges, low cost): A -> B -> C -> D (3 edges, total cost 2 + 2 + 2 = 6)
    graph.add_edge(RoadEdge("A", "B", 2.0, 2.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("B", "C", 2.0, 2.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("C", "D", 2.0, 2.0, is_bidirectional=True))

    return graph


def test_bfs_vs_ucs_essential_contrast(classic_search_graph):
    """ESSENTIAL TEST: Verify BFS chooses fewer edges with higher cost, while UCS chooses minimum cost."""
    bfs_res = bfs_search(classic_search_graph, "A", "D")
    ucs_res = ucs_search(classic_search_graph, "A", "D")

    assert bfs_res.success is True
    assert ucs_res.success is True

    # BFS chooses Path 1: ['A', 'HIGHWAY_HOP', 'D'] (2 edges, cost 20.0)
    assert bfs_res.edge_count == 2
    assert bfs_res.cost == 20.0
    assert bfs_res.path == ["A", "HIGHWAY_HOP", "D"]

    # UCS chooses Path 2: ['A', 'B', 'C', 'D'] (3 edges, cost 6.0)
    assert ucs_res.edge_count == 3
    assert ucs_res.cost == 6.0
    assert ucs_res.path == ["A", "B", "C", "D"]

    # Mathematical contrast verification
    assert bfs_res.edge_count < ucs_res.edge_count
    assert bfs_res.cost > ucs_res.cost


def test_a_star_optimality_matches_ucs(classic_search_graph):
    """Verify A* with admissible heuristic finds the identical optimal cost as UCS."""
    ucs_res = ucs_search(classic_search_graph, "A", "D")
    a_star_res = a_star_search(classic_search_graph, "A", "D")

    assert a_star_res.success is True
    assert a_star_res.cost == ucs_res.cost
    assert a_star_res.path == ucs_res.path


def test_greedy_best_first_search(classic_search_graph):
    """Greedy search prioritizes nodes closer in Euclidean/Haversine distance to goal."""
    res = greedy_best_first_search(classic_search_graph, "A", "D")
    assert res.success is True
    assert res.path[0] == "A"
    assert res.path[-1] == "D"


def test_dfs_deterministic_traversal(classic_search_graph):
    """DFS should find a valid path while deterministically exploring deep nodes."""
    res = dfs_search(classic_search_graph, "A", "D")
    assert res.success is True
    assert res.path[0] == "A"
    assert res.path[-1] == "D"


def test_search_start_equals_goal(classic_search_graph):
    """All algorithms should handle start == goal gracefully."""
    for fn in [bfs_search, dfs_search, ucs_search, a_star_search, greedy_best_first_search]:
        res = fn(classic_search_graph, "A", "A")
        assert res.success is True
        assert res.path == ["A"]
        assert res.cost == 0.0


def test_search_unreachable_node(classic_search_graph):
    """Graph with an isolated disconnected island node."""
    isolated = GraphNode("ISLAND", "Isolated Point", 33.80, 73.10)
    classic_search_graph.add_node(isolated)

    for fn in [bfs_search, dfs_search, ucs_search, a_star_search, greedy_best_first_search]:
        res = fn(classic_search_graph, "A", "ISLAND")
        assert res.success is False
        assert len(res.path) == 0


def test_search_missing_node(classic_search_graph):
    for fn in [bfs_search, dfs_search, ucs_search, a_star_search, greedy_best_first_search]:
        res = fn(classic_search_graph, "A", "NON_EXISTENT")
        assert res.success is False
