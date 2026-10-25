"""Routing service managing road graph topology, disruptions, and algorithm execution."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.algorithms.search import (
    bfs_search,
    dfs_search,
    ucs_search,
    a_star_search,
    greedy_best_first_search,
)
from rescuemind.models.dispatch import RouteResult
from rescuemind.models.road import GraphNode, RoadEdge
from rescuemind.utils.validators import ValidationError


class RoutingService:
    """Service managing road network state, route computation, and dynamic disruptions."""

    def __init__(self, data_path: Optional[Path] = None):
        self.graph = RoadGraph()
        self.disruption_history: List[str] = []
        if data_path:
            self.load_from_json(data_path)

    def load_from_json(self, file_path: Path):
        """Populate graph from roads JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.graph = RoadGraph()
        for node_data in data.get("nodes", []):
            node = GraphNode.from_dict(node_data)
            self.graph.add_node(node)

        for edge_data in data.get("edges", []):
            edge = RoadEdge.from_dict(edge_data)
            self.graph.add_edge(edge)

        self.graph.store_snapshot()

    def reset_to_initial(self):
        """Restore pristine road graph state."""
        self.graph.reset_to_initial()
        self.disruption_history.clear()

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self.graph.nodes.get(node_id)

    def get_all_nodes(self) -> Dict[str, GraphNode]:
        return self.graph.nodes

    def get_all_edges(self) -> List[RoadEdge]:
        return self.graph.get_all_edges()

    def block_road(self, u: str, v: str) -> bool:
        """Block road segment and record disruption."""
        success = self.graph.block_road(u, v)
        if success:
            self.disruption_history.append(f"Road blocked between '{u}' and '{v}'.")
        return success

    def unblock_road(self, u: str, v: str) -> bool:
        """Reopen road segment and record change."""
        success = self.graph.unblock_road(u, v)
        if success:
            self.disruption_history.append(f"Road reopened between '{u}' and '{v}'.")
        return success

    def set_congestion(self, u: str, v: str, multiplier: float) -> bool:
        """Update congestion multiplier."""
        success = self.graph.set_congestion(u, v, multiplier)
        if success:
            self.disruption_history.append(
                f"Congestion updated on '{u}'-'{v}' to {multiplier:.1f}x normal."
            )
        return success

    def calculate_route(self, start: str, goal: str, algorithm: str = "A*") -> RouteResult:
        """Calculate route using chosen algorithm."""
        algo_clean = algorithm.upper().replace(" ", "").replace("_", "")
        if "BFS" in algo_clean or "BREADTH" in algo_clean:
            return bfs_search(self.graph, start, goal)
        elif "DFS" in algo_clean or "DEPTH" in algo_clean:
            return dfs_search(self.graph, start, goal)
        elif "UCS" in algo_clean or "UNIFORM" in algo_clean or "DIJKSTRA" in algo_clean:
            return ucs_search(self.graph, start, goal)
        elif "GREEDY" in algo_clean:
            return greedy_best_first_search(self.graph, start, goal)
        else:
            # Default to A* search
            return a_star_search(self.graph, start, goal)

    def route_contains_edge(self, path: List[str], u: str, v: str) -> bool:
        """Check if path traverses the segment between u and v."""
        for i in range(len(path) - 1):
            p_u, p_v = path[i], path[i + 1]
            if (p_u == u and p_v == v) or (p_u == v and p_v == u):
                return True
        return False
