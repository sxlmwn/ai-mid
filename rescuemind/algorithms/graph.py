"""Weighted road graph representation for rescue operations."""
from __future__ import annotations
import copy
import math
from typing import Dict, List, Optional, Set, Tuple
from rescuemind.models.road import GraphNode, RoadEdge
from rescuemind.utils.validators import ValidationError, validate_non_negative


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    radius_earth_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius_earth_km * c


class RoadGraph:
    """Weighted graph representing the metropolitan rescue road network."""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        # Adjacency: node_id -> dict of {neighbor_id: RoadEdge}
        self.adjacency: Dict[str, Dict[str, RoadEdge]] = {}
        # Keep an immutable record of initial edges for scenario reset
        self._initial_nodes: Dict[str, GraphNode] = {}
        self._initial_edges: List[RoadEdge] = []

    def add_node(self, node: GraphNode):
        """Add a verified node to the graph."""
        if node.node_id in self.nodes:
            raise ValidationError(f"Duplicate node ID: '{node.node_id}'.")
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = {}

    def add_edge(self, edge: RoadEdge):
        """Add a verified road edge to the graph."""
        if edge.start_node not in self.nodes:
            raise ValidationError(f"Start node '{edge.start_node}' does not exist in graph.")
        if edge.end_node not in self.nodes:
            raise ValidationError(f"End node '{edge.end_node}' does not exist in graph.")
        validate_non_negative(edge.cost, "Edge cost")

        self.adjacency[edge.start_node][edge.end_node] = edge
        if edge.is_bidirectional:
            # Create matching reverse edge if not already present
            reverse_edge = RoadEdge(
                start_node=edge.end_node,
                end_node=edge.start_node,
                cost=edge.cost,
                travel_time=edge.travel_time,
                is_open=edge.is_open,
                road_name=edge.road_name,
                road_type=edge.road_type,
                congestion_multiplier=edge.congestion_multiplier,
                is_bidirectional=True,
            )
            self.adjacency[edge.end_node][edge.start_node] = reverse_edge

    def store_snapshot(self):
        """Snapshot current topology as the baseline scenario state."""
        self._initial_nodes = copy.deepcopy(self.nodes)
        edges = []
        visited_pairs: Set[Tuple[str, str]] = set()
        for u, neighbors in self.adjacency.items():
            for v, edge in neighbors.items():
                pair = tuple(sorted([u, v])) if edge.is_bidirectional else (u, v)
                if pair not in visited_pairs:
                    visited_pairs.add(pair)
                    edges.append(copy.deepcopy(edge))
        self._initial_edges = edges

    def reset_to_initial(self):
        """Restore the graph to its initial scenario state."""
        self.nodes = copy.deepcopy(self._initial_nodes)
        self.adjacency = {node_id: {} for node_id in self.nodes}
        for edge in self._initial_edges:
            self.add_edge(copy.deepcopy(edge))

    def get_neighbors(self, node_id: str, include_blocked: bool = False) -> List[Tuple[str, RoadEdge]]:
        """Get neighboring nodes and connecting edges."""
        if node_id not in self.adjacency:
            return []
        result = []
        # Sort neighbors deterministically by node_id for reproducible AI search
        for neighbor_id in sorted(self.adjacency[node_id].keys()):
            edge = self.adjacency[node_id][neighbor_id]
            if include_blocked or edge.is_open:
                result.append((neighbor_id, edge))
        return result

    def get_edge(self, u: str, v: str) -> Optional[RoadEdge]:
        """Retrieve edge between u and v if present."""
        return self.adjacency.get(u, {}).get(v)

    def block_road(self, u: str, v: str) -> bool:
        """Block a road segment between nodes u and v."""
        found = False
        edge_uv = self.get_edge(u, v)
        if edge_uv:
            edge_uv.is_open = False
            found = True
        edge_vu = self.get_edge(v, u)
        if edge_vu and (edge_uv is None or edge_uv.is_bidirectional):
            edge_vu.is_open = False
            found = True
        return found

    def unblock_road(self, u: str, v: str) -> bool:
        """Reopen a blocked road segment."""
        found = False
        edge_uv = self.get_edge(u, v)
        if edge_uv:
            edge_uv.is_open = True
            found = True
        edge_vu = self.get_edge(v, u)
        if edge_vu and (edge_uv is None or edge_uv.is_bidirectional):
            edge_vu.is_open = True
            found = True
        return found

    def set_congestion(self, u: str, v: str, multiplier: float) -> bool:
        """Update simulated congestion multiplier on road segment."""
        if multiplier < 1.0:
            raise ValidationError("Congestion multiplier must be at least 1.0")
        found = False
        edge_uv = self.get_edge(u, v)
        if edge_uv:
            edge_uv.congestion_multiplier = multiplier
            found = True
        edge_vu = self.get_edge(v, u)
        if edge_vu and (edge_uv is None or edge_uv.is_bidirectional):
            edge_vu.congestion_multiplier = multiplier
            found = True
        return found

    def get_all_edges(self) -> List[RoadEdge]:
        """Return list of distinct edges."""
        seen = set()
        edges = []
        for u in self.adjacency:
            for v, edge in self.adjacency[u].items():
                pair = tuple(sorted([u, v])) if edge.is_bidirectional else (u, v)
                if pair not in seen:
                    seen.add(pair)
                    edges.append(edge)
        return edges

    def route_exists(self, start: str, goal: str) -> bool:
        """Fast check whether an open path exists between start and goal."""
        if start not in self.nodes or goal not in self.nodes:
            return False
        if start == goal:
            return True
        visited = {start}
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr == goal:
                return True
            for nxt, edge in self.get_neighbors(curr):
                if edge.is_open and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        return False

    def heuristic_distance(self, node_a: str, node_b: str) -> float:
        """Admissible Euclidean / Haversine distance heuristic in km."""
        if node_a not in self.nodes or node_b not in self.nodes:
            return 0.0
        n1 = self.nodes[node_a]
        n2 = self.nodes[node_b]
        # Haversine distance in km is strictly <= actual road route distance on ground
        # Making it a mathematically admissible and consistent heuristic for A*
        return round(haversine_distance_km(n1.latitude, n1.longitude, n2.latitude, n2.longitude), 3)
