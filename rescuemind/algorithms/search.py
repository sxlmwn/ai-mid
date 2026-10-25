"""Manual implementations of core AI search algorithms for route optimization.

Algorithms implemented:
1. Breadth-First Search (BFS) - finds path with fewest edges (unweighted shortest path)
2. Depth-First Search (DFS) - explores deep paths first, deterministic neighbor order
3. Uniform Cost Search (UCS) - finds minimum-cost path using priority queue
4. A* Search - finds minimum-cost path guided by admissible heuristic f(n) = g(n) + h(n)
5. Greedy Best-First Search - heuristic-only exploration prioritizing h(n)
"""
from __future__ import annotations
import collections
import heapq
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.models.dispatch import RouteResult


def _compute_path_metrics(graph: RoadGraph, path: List[str]) -> Tuple[float, float]:
    """Compute total cost and estimated travel time along path."""
    total_cost = 0.0
    total_time = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge = graph.get_edge(u, v)
        if edge:
            total_cost += edge.effective_cost
            total_time += edge.effective_time
    return round(total_cost, 3), round(total_time, 3)


def bfs_search(graph: RoadGraph, start: str, goal: str, max_steps: int = 2000) -> RouteResult:
    """Breadth-First Search (BFS).
    Explores level by level using a FIFO queue.
    Guarantees finding the route with the fewest edges (hop count).
    Does NOT guarantee minimum travel cost on weighted graphs.
    """
    t0 = time.perf_counter()

    if start not in graph.nodes or goal not in graph.nodes:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Breadth-First Search (BFS)",
            path=[],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=0,
            generated_nodes=0,
            runtime_ms=runtime_ms,
            success=False,
            explanation=f"Error: Start '{start}' or Goal '{goal}' not found in graph.",
        )

    if start == goal:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Breadth-First Search (BFS)",
            path=[start],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=1,
            generated_nodes=1,
            runtime_ms=runtime_ms,
            success=True,
            explanation="Start and goal nodes are identical (trivial path).",
        )

    queue = collections.deque([(start, [start])])
    visited: Set[str] = {start}
    explored_count = 0
    generated_count = 1
    step_trace: List[Dict[str, Any]] = []

    while queue and explored_count < max_steps:
        current, path = queue.popleft()
        explored_count += 1

        step_trace.append({
            "step": explored_count,
            "current_node": current,
            "path_so_far": list(path),
            "queue_size": len(queue),
            "action": f"Expanded node {current} at depth {len(path) - 1}",
        })

        if current == goal:
            cost, travel_time = _compute_path_metrics(graph, path)
            runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
            return RouteResult(
                algorithm_name="Breadth-First Search (BFS)",
                path=path,
                cost=cost,
                travel_time=travel_time,
                explored_nodes=explored_count,
                generated_nodes=generated_count,
                runtime_ms=runtime_ms,
                success=True,
                explanation=(
                    f"BFS reached destination '{goal}' through {len(path)-1} edges. "
                    f"BFS guarantees minimum edge count, exploring level-by-level in FIFO order. "
                    f"Total route cost is {cost}."
                ),
                step_trace=step_trace,
            )

        for neighbor, edge in graph.get_neighbors(current):
            if edge.is_open and neighbor not in visited:
                visited.add(neighbor)
                generated_count += 1
                queue.append((neighbor, path + [neighbor]))

    runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
    return RouteResult(
        algorithm_name="Breadth-First Search (BFS)",
        path=[],
        cost=0.0,
        travel_time=0.0,
        explored_nodes=explored_count,
        generated_nodes=generated_count,
        runtime_ms=runtime_ms,
        success=False,
        explanation=f"No open path found between '{start}' and '{goal}' via BFS.",
        step_trace=step_trace,
    )


def dfs_search(graph: RoadGraph, start: str, goal: str, max_steps: int = 2000) -> RouteResult:
    """Depth-First Search (DFS).
    Explores along each branch as deeply as possible before backtracking using a LIFO stack.
    Educational comparison: Does NOT guarantee shortest path nor minimum cost.
    """
    t0 = time.perf_counter()

    if start not in graph.nodes or goal not in graph.nodes:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Depth-First Search (DFS)",
            path=[],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=0,
            generated_nodes=0,
            runtime_ms=runtime_ms,
            success=False,
            explanation=f"Error: Start '{start}' or Goal '{goal}' not found in graph.",
        )

    if start == goal:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Depth-First Search (DFS)",
            path=[start],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=1,
            generated_nodes=1,
            runtime_ms=runtime_ms,
            success=True,
            explanation="Start and goal nodes are identical.",
        )

    stack = [(start, [start])]
    visited: Set[str] = set()
    explored_count = 0
    generated_count = 1
    step_trace: List[Dict[str, Any]] = []

    while stack and explored_count < max_steps:
        current, path = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        explored_count += 1

        step_trace.append({
            "step": explored_count,
            "current_node": current,
            "path_so_far": list(path),
            "stack_size": len(stack),
            "action": f"Popped {current} from DFS stack at depth {len(path) - 1}",
        })

        if current == goal:
            cost, travel_time = _compute_path_metrics(graph, path)
            runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
            return RouteResult(
                algorithm_name="Depth-First Search (DFS)",
                path=path,
                cost=cost,
                travel_time=travel_time,
                explored_nodes=explored_count,
                generated_nodes=generated_count,
                runtime_ms=runtime_ms,
                success=True,
                explanation=(
                    f"DFS reached '{goal}' by plunging deeply into the graph. "
                    f"Route contains {len(path)-1} edges with cost {cost}. "
                    f"Notice DFS does NOT guarantee minimal edge count or minimal cost."
                ),
                step_trace=step_trace,
            )

        # Explore neighbors in reverse order so alphabetically first neighbor is popped first
        neighbors = graph.get_neighbors(current)
        for neighbor, edge in reversed(neighbors):
            if edge.is_open and neighbor not in visited:
                generated_count += 1
                stack.append((neighbor, path + [neighbor]))

    runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
    return RouteResult(
        algorithm_name="Depth-First Search (DFS)",
        path=[],
        cost=0.0,
        travel_time=0.0,
        explored_nodes=explored_count,
        generated_nodes=generated_count,
        runtime_ms=runtime_ms,
        success=False,
        explanation=f"DFS failed to find an open route from '{start}' to '{goal}'.",
        step_trace=step_trace,
    )


def ucs_search(graph: RoadGraph, start: str, goal: str) -> RouteResult:
    """Uniform Cost Search (UCS) / Dijkstra's Algorithm.
    Expands nodes in order of cumulative path cost g(n) using a min-priority queue.
    Guarantees finding the minimum-cost route with non-negative edge weights.
    """
    t0 = time.perf_counter()

    if start not in graph.nodes or goal not in graph.nodes:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Uniform Cost Search (UCS)",
            path=[],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=0,
            generated_nodes=0,
            runtime_ms=runtime_ms,
            success=False,
            explanation=f"Start '{start}' or Goal '{goal}' not found in graph.",
        )

    if start == goal:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Uniform Cost Search (UCS)",
            path=[start],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=1,
            generated_nodes=1,
            runtime_ms=runtime_ms,
            success=True,
            explanation="Start and goal nodes are identical.",
        )

    # Priority queue entry: (cumulative_cost, counter, current_node, path)
    counter = 0
    pq: List[Tuple[float, int, str, List[str]]] = [(0.0, counter, start, [start])]
    best_cost: Dict[str, float] = {start: 0.0}
    explored_nodes: Set[str] = set()
    explored_count = 0
    generated_count = 1
    step_trace: List[Dict[str, Any]] = []

    while pq:
        cost, _, current, path = heapq.heappop(pq)

        if current in explored_nodes:
            continue
        explored_nodes.add(current)
        explored_count += 1

        step_trace.append({
            "step": explored_count,
            "current_node": current,
            "cost_g": round(cost, 3),
            "path_so_far": list(path),
            "pq_size": len(pq),
            "action": f"Expanded node {current} with minimum cumulative cost g={round(cost, 3)}",
        })

        if current == goal:
            _, travel_time = _compute_path_metrics(graph, path)
            runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
            return RouteResult(
                algorithm_name="Uniform Cost Search (UCS)",
                path=path,
                cost=round(cost, 3),
                travel_time=travel_time,
                explored_nodes=explored_count,
                generated_nodes=generated_count,
                runtime_ms=runtime_ms,
                success=True,
                explanation=(
                    f"UCS found the mathematically optimal minimum-cost route to '{goal}' "
                    f"with total cost {round(cost, 3)} across {len(path)-1} edges. "
                    f"Expanded {explored_count} nodes ordered strictly by cumulative cost g(n)."
                ),
                step_trace=step_trace,
            )

        for neighbor, edge in graph.get_neighbors(current):
            if not edge.is_open:
                continue
            new_cost = cost + edge.effective_cost
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                counter += 1
                generated_count += 1
                heapq.heappush(pq, (new_cost, counter, neighbor, path + [neighbor]))

    runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
    return RouteResult(
        algorithm_name="Uniform Cost Search (UCS)",
        path=[],
        cost=0.0,
        travel_time=0.0,
        explored_nodes=explored_count,
        generated_nodes=generated_count,
        runtime_ms=runtime_ms,
        success=False,
        explanation=f"UCS exhausted all reachable nodes; no open route exists to '{goal}'.",
        step_trace=step_trace,
    )


def a_star_search(graph: RoadGraph, start: str, goal: str) -> RouteResult:
    """A* Search.
    Evaluates nodes by f(n) = g(n) + h(n), where:
    - g(n) is the exact cumulative cost from start to n.
    - h(n) is the admissible Haversine/Euclidean distance heuristic to goal.
    Guarantees optimal minimum-cost path when heuristic is admissible and consistent.
    """
    t0 = time.perf_counter()

    if start not in graph.nodes or goal not in graph.nodes:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="A* Search",
            path=[],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=0,
            generated_nodes=0,
            runtime_ms=runtime_ms,
            success=False,
            explanation=f"Start '{start}' or Goal '{goal}' not found in graph.",
        )

    if start == goal:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="A* Search",
            path=[start],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=1,
            generated_nodes=1,
            runtime_ms=runtime_ms,
            success=True,
            explanation="Start and goal nodes are identical.",
        )

    counter = 0
    start_h = graph.heuristic_distance(start, goal)
    # Entry: (f_score, h_score, counter, current_node, g_score, path)
    pq: List[Tuple[float, float, int, str, float, List[str]]] = [
        (start_h, start_h, counter, start, 0.0, [start])
    ]
    best_g: Dict[str, float] = {start: 0.0}
    closed_set: Set[str] = set()
    explored_count = 0
    generated_count = 1
    step_trace: List[Dict[str, Any]] = []

    while pq:
        f_score, h_score, _, current, g_score, path = heapq.heappop(pq)

        if current in closed_set:
            continue
        closed_set.add(current)
        explored_count += 1

        step_trace.append({
            "step": explored_count,
            "current_node": current,
            "cost_g": round(g_score, 3),
            "heuristic_h": round(h_score, 3),
            "total_f": round(f_score, 3),
            "path_so_far": list(path),
            "open_size": len(pq),
            "action": f"Expanded {current} with f={round(f_score, 3)} (g={round(g_score, 3)} + h={round(h_score, 3)})",
        })

        if current == goal:
            _, travel_time = _compute_path_metrics(graph, path)
            runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
            return RouteResult(
                algorithm_name="A* Search",
                path=path,
                cost=round(g_score, 3),
                travel_time=travel_time,
                explored_nodes=explored_count,
                generated_nodes=generated_count,
                runtime_ms=runtime_ms,
                success=True,
                explanation=(
                    f"A* found an optimal route to '{goal}' with cost {round(g_score, 3)} "
                    f"using f(n) = g(n) + h(n). Admissible Haversine heuristic guided search, "
                    f"expanding {explored_count} nodes."
                ),
                step_trace=step_trace,
            )

        for neighbor, edge in graph.get_neighbors(current):
            if not edge.is_open:
                continue
            tentative_g = g_score + edge.effective_cost
            if neighbor not in best_g or tentative_g < best_g[neighbor]:
                best_g[neighbor] = tentative_g
                h = graph.heuristic_distance(neighbor, goal)
                f = tentative_g + h
                counter += 1
                generated_count += 1
                heapq.heappush(pq, (f, h, counter, neighbor, tentative_g, path + [neighbor]))

    runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
    return RouteResult(
        algorithm_name="A* Search",
        path=[],
        cost=0.0,
        travel_time=0.0,
        explored_nodes=explored_count,
        generated_nodes=generated_count,
        runtime_ms=runtime_ms,
        success=False,
        explanation=f"A* found no open path to '{goal}'.",
        step_trace=step_trace,
    )


def greedy_best_first_search(graph: RoadGraph, start: str, goal: str) -> RouteResult:
    """Greedy Best-First Search.
    Prioritizes nodes purely by estimated heuristic distance h(n) to the goal.
    Very fast exploration towards target, but does NOT consider path cost g(n),
    so it does NOT guarantee minimum travel cost or shortest edge count.
    """
    t0 = time.perf_counter()

    if start not in graph.nodes or goal not in graph.nodes:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Greedy Best-First Search",
            path=[],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=0,
            generated_nodes=0,
            runtime_ms=runtime_ms,
            success=False,
            explanation=f"Start '{start}' or Goal '{goal}' not found in graph.",
        )

    if start == goal:
        runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
        return RouteResult(
            algorithm_name="Greedy Best-First Search",
            path=[start],
            cost=0.0,
            travel_time=0.0,
            explored_nodes=1,
            generated_nodes=1,
            runtime_ms=runtime_ms,
            success=True,
            explanation="Start and goal nodes are identical.",
        )

    counter = 0
    start_h = graph.heuristic_distance(start, goal)
    pq: List[Tuple[float, int, str, List[str]]] = [(start_h, counter, start, [start])]
    visited: Set[str] = set()
    explored_count = 0
    generated_count = 1
    step_trace: List[Dict[str, Any]] = []

    while pq:
        h_score, _, current, path = heapq.heappop(pq)

        if current in visited:
            continue
        visited.add(current)
        explored_count += 1

        step_trace.append({
            "step": explored_count,
            "current_node": current,
            "heuristic_h": round(h_score, 3),
            "path_so_far": list(path),
            "open_size": len(pq),
            "action": f"Expanded {current} greedily with smallest estimated h={round(h_score, 3)}",
        })

        if current == goal:
            cost, travel_time = _compute_path_metrics(graph, path)
            runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
            return RouteResult(
                algorithm_name="Greedy Best-First Search",
                path=path,
                cost=cost,
                travel_time=travel_time,
                explored_nodes=explored_count,
                generated_nodes=generated_count,
                runtime_ms=runtime_ms,
                success=True,
                explanation=(
                    f"Greedy Best-First Search reached '{goal}' quickly by prioritizing lowest h(n). "
                    f"Route cost is {cost} across {len(path)-1} edges. "
                    f"Greedy ignores accumulated path cost g(n), meaning the route might be sub-optimal."
                ),
                step_trace=step_trace,
            )

        for neighbor, edge in graph.get_neighbors(current):
            if edge.is_open and neighbor not in visited:
                h = graph.heuristic_distance(neighbor, goal)
                counter += 1
                generated_count += 1
                heapq.heappush(pq, (h, counter, neighbor, path + [neighbor]))

    runtime_ms = round((time.perf_counter() - t0) * 1000, 3)
    return RouteResult(
        algorithm_name="Greedy Best-First Search",
        path=[],
        cost=0.0,
        travel_time=0.0,
        explored_nodes=explored_count,
        generated_nodes=generated_count,
        runtime_ms=runtime_ms,
        success=False,
        explanation=f"Greedy search failed to find an open route to '{goal}'.",
        step_trace=step_trace,
    )
