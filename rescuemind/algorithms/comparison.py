"""Harness for comparing search algorithms on identical graph topologies."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.algorithms.search import (
    bfs_search,
    dfs_search,
    ucs_search,
    a_star_search,
    greedy_best_first_search,
)
from rescuemind.models.dispatch import RouteResult


def run_all_search_algorithms(graph: RoadGraph, start: str, goal: str) -> Dict[str, RouteResult]:
    """Execute BFS, DFS, UCS, A*, and Greedy Best-First Search on identical inputs."""
    results: Dict[str, RouteResult] = {}
    results["BFS"] = bfs_search(graph, start, goal)
    results["DFS"] = dfs_search(graph, start, goal)
    results["UCS"] = ucs_search(graph, start, goal)
    results["A*"] = a_star_search(graph, start, goal)
    results["Greedy"] = greedy_best_first_search(graph, start, goal)
    return results


def summarize_comparison(results: Dict[str, RouteResult]) -> List[Dict[str, Any]]:
    """Format comparison results into clean tabular summary dictionaries."""
    summary = []
    for key, res in results.items():
        summary.append({
            "Algorithm": res.algorithm_name,
            "Success": "Yes" if res.success else "No",
            "Path": " -> ".join(res.path) if res.path else "None",
            "Total Cost": res.cost,
            "Est. Time (min)": res.travel_time,
            "Hops (Edges)": res.edge_count,
            "Nodes Explored": res.explored_nodes,
            "Nodes Generated": res.generated_nodes,
            "Runtime (ms)": res.runtime_ms,
        })
    return summary
