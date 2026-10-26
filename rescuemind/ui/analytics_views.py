"""AI Lab view: educational algorithm comparisons, search traces, and optimization analysis."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from rescuemind.algorithms.comparison import run_all_search_algorithms
from rescuemind.services.simulation_service import SimulationService
from rescuemind.ui.map_view import render_operations_map


def render_analytics_view(sim: SimulationService):
    st.markdown('<div class="page-title">AI Laboratory & Algorithm Evaluation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-caption">Explore and compare how Artificial Intelligence algorithms solve routing, team assignment, and optimization problems.</div>',
        unsafe_allow_html=True,
    )

    tab_search, tab_csp_opt = st.tabs(["Route Search Comparison", "CSP vs Branch-and-Bound Optimization"])

    # TAB 1: ROUTE SEARCH COMPARISON
    with tab_search:
        st.markdown("#### Compare Pathfinding Algorithms")
        st.markdown(
            "Select a starting point and a destination in the Twin Cities network to see how five genuinely different "
            "search algorithms find paths across the road network."
        )

        nodes = sim.routing_service.get_all_nodes()
        node_keys = sorted(nodes.keys())

        c1, c2, c3 = st.columns([1.5, 1.5, 1.0])
        with c1:
            start_node = st.selectbox(
                "Starting Point",
                node_keys,
                index=node_keys.index("F6_SUPER") if "F6_SUPER" in node_keys else 0,
                help="Starting base or rescue location",
            )
        with c2:
            default_goal = "ZERO_POINT" if "ZERO_POINT" in node_keys else node_keys[-1]
            goal_node = st.selectbox(
                "Destination",
                node_keys,
                index=node_keys.index(default_goal),
                help="Target incident location",
            )
        with c3:
            st.write("")
            st.write("")
            compare_btn = st.button("Compare Routes", type="primary", use_container_width=True)

        if compare_btn or "lab_results" not in st.session_state:
            results = run_all_search_algorithms(sim.routing_service.graph, start_node, goal_node)
            st.session_state["lab_results"] = results
            st.session_state["lab_start"] = start_node
            st.session_state["lab_goal"] = goal_node

        results = st.session_state.get("lab_results", {})

        # Beginner-friendly algorithm explanations banner
        with st.expander("Learn about these 5 algorithms in plain English", expanded=False):
            st.markdown("""
            - **Breadth-First Search (BFS):** Explores outward level-by-level. It finds the route with the **fewest road turns (hops)**, but ignores road distance and tolls.
            - **Depth-First Search (DFS):** Plunges down one road as far as possible before backtracking. Fast in some mazes, but often produces very long and winding detours.
            - **Uniform Cost Search (UCS):** Explores by lowest accumulated travel cost. It mathematically guarantees the **shortest total travel distance**.
            - **A* Search:** Guided by straight-line distance to the target ($f = g + h$). It finds the **optimal shortest route** while exploring far fewer unnecessary locations.
            - **Greedy Best-First Search:** Always picks whichever road points closest toward the goal. Very quick, but can be tricked by dead ends and obstacles.
            """)

        # Readable Comparison Table / Cards
        table_rows = []
        for key, res in results.items():
            table_rows.append({
                "Algorithm": res.algorithm_name,
                "Route Found": "Yes" if res.success else "No",
                "Total Route Cost": f"{res.cost:.1f} km",
                "Travel Time": f"{res.travel_time:.1f} min",
                "Route Hops": res.edge_count,
                "Locations Explored": res.explored_nodes,
                "Compute Time": f"{res.runtime_ms:.2f} ms",
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        # Map Visualization & Advanced Traces
        st.markdown("#### Visual Route on Map")
        c_sel, _ = st.columns([1.5, 2.0])
        with c_sel:
            algo_view = st.selectbox("Select Route to Highlight on Map", list(results.keys()), index=list(results.keys()).index("A*") if "A*" in results else 0)

        highlighted = results.get(algo_view)
        if highlighted:
            col_m, col_info = st.columns([1.3, 1.0])
            with col_m:
                render_operations_map(
                    graph=sim.routing_service.graph,
                    incidents=[],
                    teams=[],
                    highlight_route=highlighted,
                    height=420,
                )
            with col_info:
                st.markdown(f"**{highlighted.algorithm_name} Details**")
                st.write(f"- **Path:** `{' -> '.join(highlighted.path)}`")
                st.write(f"- **Total Distance:** {highlighted.cost:.1f} km")
                st.write(f"- **Number of Road Segments:** {highlighted.edge_count}")
                st.write(f"- **Locations Explored:** {highlighted.explored_nodes}")
                st.caption(highlighted.explanation)

                # Advanced step trace inside a tidy expander
                if highlighted.step_trace:
                    with st.expander(f"View Step-by-Step Search Trace ({len(highlighted.step_trace)} steps)", expanded=False):
                        st.dataframe(pd.DataFrame(highlighted.step_trace), use_container_width=True, height=260, hide_index=True)

    # TAB 2: CSP VS BRANCH-AND-BOUND
    with tab_csp_opt:
        st.markdown("#### Team Assignment: Feasible Matching vs Optimal Matching")
        st.markdown(
            "Comparing how standard **Constraint Satisfaction (CSP)** matches teams to calls versus how **Branch-and-Bound** "
            "finds the globally optimal allocation to minimize fleet fuel and travel distance."
        )

        cmp_data = sim.metrics_service.compare_csp_vs_optimization()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Feasible Solution Found", "Yes" if cmp_data["csp_feasible"] else "No")
        k2.metric("Standard CSP Distance", f"{cmp_data['csp_total_cost']:.1f} km")
        savings = cmp_data["cost_reduction_km"]
        k3.metric("Optimized Distance (B&B)", f"{cmp_data['opt_total_cost']:.1f} km", delta=f"-{savings:.1f} km" if savings > 0 else "0.0 km")
        k4.metric("Subtrees Pruned", cmp_data["opt_branches_pruned"])

        c_csp, c_opt = st.columns(2)
        with c_csp:
            st.markdown("##### Standard CSP Matching (MRV + Forward Checking)")
            st.caption("Finds a valid assignment satisfying all rules. Stops at the first complete leaf.")
            st.write(f"Search states checked: **{cmp_data['csp_nodes_explored']}**")
            for inc_id, t_id in cmp_data["csp_assignments"].items():
                st.markdown(f"• Request `{inc_id}` $\\to$ Team `{t_id}`")

        with c_opt:
            st.markdown("##### Branch-and-Bound Cost Optimization")
            st.caption("Searches across valid combinations to minimize total kilometers driven.")
            st.write(f"Search states checked: **{cmp_data['opt_nodes_explored']}** | Subtrees safely pruned: **{cmp_data['opt_branches_pruned']}**")
            for inc_id, t_id in cmp_data["opt_assignments"].items():
                st.markdown(f"• Request `{inc_id}` $\\to$ Team `{t_id}`")

        with st.expander("Why does Branch-and-Bound save kilometers?", expanded=False):
            st.markdown("""
            **The Lower-Bound Pruning Principle:**
            When evaluating teams for multiple emergencies, Branch-and-Bound calculates an admissible lower bound: 
            the theoretical minimum remaining travel distance for all unassigned animals.
            
            If the kilometers driven so far **plus** the lower bound is already greater than the best complete solution found, 
            the algorithm immediately **prunes** that entire path from memory. This guarantees mathematical optimality without checking every single combination.
            """)
