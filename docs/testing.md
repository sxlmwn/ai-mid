# RescueMind Automated Testing Strategy & Execution Report

This document details the test methodology, test matrix, and empirical test results for **RescueMind**.

---

## 1. Test Architecture & Principles

All tests are written using `pytest` and execute without dependencies on external web services, map tile downloads, or live LLM APIs.

### Key Testing Principles:
1. **Isolated Execution:** Core search, priority, CSP, and optimization algorithms are decoupled from Streamlit and tested via pure Python unit tests.
2. **Determinism:** Tests verify deterministic tie-breaking, invariant outcomes, and reproducible states.
3. **Mathematical Correctness:** Search and optimization algorithms are validated against known theoretical benchmarks (e.g., A* vs UCS, and Branch-and-Bound vs brute-force exhaustive enumeration).
4. **Resilience & Graceful Degradation:** Disconnected graphs, unreachable targets, blocked segments, and empty candidate domains are tested to ensure clean failure modes.

---

## 2. Test Matrix Overview

| Test Module | Coverage Area | Key Verification Scenarios | Test Count | Status |
| :--- | :--- | :--- | :--- | :--- |
| `tests/test_graph.py` | Graph Topology & Road Weights | Node/edge validation, negative cost rejection, road blocking/unblocking, congestion multipliers, reset, and Haversine formula. | 7 | **PASSED** |
| `tests/test_search.py` | Search Algorithms | BFS, DFS, UCS, A*, and Greedy. Start=Goal, missing nodes, unreachable nodes, and **essential BFS vs UCS cost-contrast test**. | 7 | **PASSED** |
| `tests/test_priority.py` | Priority Queue & Scoring | Multi-factor score breakdown, queue ordering, equal-score tie-breaking, status filtering, and dynamic wait-time escalation. | 5 | **PASSED** |
| `tests/test_assignment.py` | CSP Backtracking Solver | Valid assignment, skill deficit rejection, capacity limits, multi-capacity support, and species category restrictions. | 5 | **PASSED** |
| `tests/test_optimization.py` | Branch-and-Bound Optimizer | Global cost minimization, **optimality verified against exhaustive brute force**, and infeasible handling. | 2 | **PASSED** |
| `tests/test_simulation.py` | Simulation Lifecycle | Time advance, scenario loading (Faizabad blockage), reset to baseline, and natural language intake parsing. | 4 | **PASSED** |
| `tests/test_integration.py` | End-to-End Workflow | Full dispatch cycle, dynamic incident registration, road blockage and autonomous route replanning. | 3 | **PASSED** |
| **Total** | | | **33** | **100% PASS** |

---

## 3. Deep-Dive on Critical Algorithmic Tests

### A. The Essential BFS vs UCS Contrast Test (`test_bfs_vs_ucs_essential_contrast`)
- **Graph Setup:**
  - Path 1: $A \to \text{HIGHWAY\_HOP} \to D$ (2 edges, edge costs: $10.0 + 10.0 = 20.0\text{ km}$).
  - Path 2: $A \to B \to C \to D$ (3 edges, edge costs: $2.0 + 2.0 + 2.0 = 6.0\text{ km}$).
- **Result:**
  - BFS returns Path 1: 2 hops, cost = $20.0$.
  - UCS returns Path 2: 3 hops, cost = $6.0$.
  - Proves conclusively that BFS minimizes edge count, while UCS minimizes travel cost.

### B. Optimality of Branch-and-Bound (`test_branch_and_bound_optimality_matches_exhaustive`)
- Compares Branch-and-Bound with an independent brute-force generator (`itertools.product`).
- In all tested permutations, Branch-and-Bound produces the identical assignment and identical optimal cost ($5.0\text{ km}$) while pruning redundant subtrees.

---

## 4. Execution Command & Outcome

### Windows PowerShell Execution Command:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### Actual Terminal Execution Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.1, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\alifo\Downloads\AI Lab Mid
collected 33 items

tests/test_assignment.py::test_csp_valid_assignment PASSED               [  3%]
tests/test_assignment.py::test_csp_missing_skills_rejection PASSED       [  6%]
tests/test_assignment.py::test_csp_capacity_constraint PASSED            [  9%]
tests/test_assignment.py::test_csp_higher_capacity_allows_multiple PASSED [ 12%]
tests/test_assignment.py::test_csp_category_restriction PASSED           [ 15%]
tests/test_graph.py::test_add_node_duplicate PASSED                      [ 18%]
tests/test_graph.py::test_add_edge_missing_node PASSED                   [ 21%]
tests/test_graph.py::test_edge_negative_cost PASSED                      [ 24%]
tests/test_graph.py::test_road_blocking_and_unblocking PASSED            [ 27%]
tests/test_graph.py::test_congestion_multiplier PASSED                   [ 30%]
tests/test_graph.py::test_graph_reset PASSED                             [ 33%]
tests/test_graph.py::test_haversine_distance PASSED                      [ 36%]
tests/test_integration.py::test_full_dispatch_cycle_execution PASSED     [ 39%]
tests/test_integration.py::test_dynamic_incident_registration_and_dispatch PASSED [ 42%]
tests/test_integration.py::test_road_blockage_and_route_replanning PASSED [ 45%]
tests/test_optimization.py::test_branch_and_bound_optimality_matches_exhaustive PASSED [ 48%]
tests/test_optimization.py::test_branch_and_bound_infeasible PASSED      [ 51%]
tests/test_priority.py::test_score_calculation_breakdown PASSED          [ 54%]
tests/test_priority.py::test_priority_ordering PASSED                    [ 57%]
tests/test_priority.py::test_equal_score_tie_breaking PASSED             [ 60%]
tests/test_priority.py::test_resolved_and_cancelled_filtering PASSED     [ 63%]
tests/test_priority.py::test_waiting_time_dynamic_boost PASSED           [ 66%]
tests/test_search.py::test_bfs_vs_ucs_essential_contrast PASSED          [ 69%]
tests/test_search.py::test_a_star_optimality_matches_ucs PASSED          [ 72%]
tests/test_search.py::test_greedy_best_first_search PASSED               [ 75%]
tests/test_search.py::test_dfs_deterministic_traversal PASSED            [ 78%]
tests/test_search.py::test_search_start_equals_goal PASSED               [ 81%]
tests/test_search.py::test_search_unreachable_node PASSED                [ 84%]
tests/test_search.py::test_search_missing_node PASSED                    [ 87%]
tests/test_simulation.py::test_advance_time PASSED                       [ 90%]
tests/test_simulation.py::test_load_scenario_faizabad_closure PASSED     [ 93%]
tests/test_simulation.py::test_reset_all PASSED                          [ 96%]
tests/test_simulation.py::test_natural_language_intake_extraction PASSED [100%]

============================= 33 passed in 0.34s ==============================
```
