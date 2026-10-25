"""Tests for graph topology, edge weights, and road disruptions."""
import pytest
from rescuemind.algorithms.graph import RoadGraph, haversine_distance_km
from rescuemind.models.road import GraphNode, RoadEdge
from rescuemind.utils.validators import ValidationError


@pytest.fixture
def sample_graph():
    graph = RoadGraph()
    n1 = GraphNode("N1", "Node 1", 33.70, 73.05, "junction")
    n2 = GraphNode("N2", "Node 2", 33.71, 73.06, "junction")
    n3 = GraphNode("N3", "Node 3", 33.72, 73.07, "junction")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.add_edge(RoadEdge("N1", "N2", 2.0, 4.0, is_bidirectional=True))
    graph.add_edge(RoadEdge("N2", "N3", 3.0, 6.0, is_bidirectional=True))
    graph.store_snapshot()
    return graph


def test_add_node_duplicate(sample_graph):
    with pytest.raises(ValidationError):
        sample_graph.add_node(GraphNode("N1", "Duplicate", 33.70, 73.05))


def test_add_edge_missing_node(sample_graph):
    with pytest.raises(ValidationError):
        sample_graph.add_edge(RoadEdge("N1", "UNKNOWN", 1.0, 2.0))


def test_edge_negative_cost():
    with pytest.raises(ValidationError):
        RoadEdge("N1", "N2", -5.0, 2.0)


def test_road_blocking_and_unblocking(sample_graph):
    assert sample_graph.route_exists("N1", "N3") is True
    # Block N1 - N2
    sample_graph.block_road("N1", "N2")
    assert sample_graph.get_edge("N1", "N2").is_open is False
    assert sample_graph.get_edge("N2", "N1").is_open is False
    assert sample_graph.route_exists("N1", "N3") is False

    # Unblock
    sample_graph.unblock_road("N1", "N2")
    assert sample_graph.get_edge("N1", "N2").is_open is True
    assert sample_graph.route_exists("N1", "N3") is True


def test_congestion_multiplier(sample_graph):
    sample_graph.set_congestion("N1", "N2", 2.0)
    edge = sample_graph.get_edge("N1", "N2")
    assert edge.effective_cost == 4.0
    assert edge.effective_time == 8.0

    with pytest.raises(ValidationError):
        sample_graph.set_congestion("N1", "N2", 0.5)


def test_graph_reset(sample_graph):
    sample_graph.block_road("N1", "N2")
    assert sample_graph.route_exists("N1", "N3") is False
    sample_graph.reset_to_initial()
    assert sample_graph.route_exists("N1", "N3") is True


def test_haversine_distance():
    # Distance between Islamabad Zero Point (33.6930, 73.0645) and Rawalpindi Saddar (33.5980, 73.0540)
    # Expected approx 10.6 km
    d = haversine_distance_km(33.6930, 73.0645, 33.5980, 73.0540)
    assert 9.0 <= d <= 12.0
