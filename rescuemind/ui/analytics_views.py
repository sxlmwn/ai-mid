"""AI Lab and Operations Analytics view."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from rescuemind.algorithms.comparison import run_all_search_algorithms, summarize_comparison
from rescuemind.services.simulation_service import SimulationService
from rescuemind.ui.map_view import render_operations_map


def render_analytics_view(sim: SimulationService):
    st.subheader("AI Lab & Algorithmic Evaluation")
    st.caption("Interactive experimentation laboratory comparing graph search, priority queues, CSP, and Branch-and-Bound.")

    tab_lab, tab_csp_opt, tab_charts = st.tabs(["Search Algorithm Lab", "CSP vs Branch-and-Bound", "Operations Analytics"])

    # TAB 1: SEARCH ALGORITHM LAB
    with tab_lab:
        st.markdown("##### Route Search Algorithm Comparative Arena")
        st.caption("Run BFS, DFS, UCS, A*, and Greedy Best-First Search on identical graph topologies and compare their performance.")

        nodes = sim.routing_service.get_all_nodes()
        node_keys = sorted(nodes.keys())

        c1, c2, c3 = st.columns([1.5, 1.5, 1.0])
        with c1:
            start_node = st.selectbox("Start Node", node_keys, index=node_keys.index("F6_SUPER") if "F6_SUPER" in node_keys else 0)
        with c2:
            default_goal = "ZERO_POINT" if "ZERO_POINT" in node_keys else node_keys[-1]
            goal_node = st.selectbox("Destination Node", node_keys, index=node_keys.index(default_goal))
        with c3:
            st.write("")
            st.write("")
            run_btn = st.button("Run Comparison", type="primary", use_container_width=True)

        if run_btn or "lab_results" not in st.session_state:
            results = run_all_search_algorithms(sim.routing_service.graph, start_node, goal_node)
            st.session_state["lab_results"] = results
            st.session_state["lab_start"] = start_node
            st.session_state["lab_goal"] = goal_node

        results = st.session_state.get("lab_results", {})
        summary = summarize_comparison(results)
        df_summary = pd.DataFrame(summary)

        st.markdown("###### Comparative Performance Metrics")
        st.dataframe(df_summary, use_container_width=True)

        # Highlight Route on Map
        st.markdown("###### Visual Route Inspection on Map")
        algo_to_display = st.selectbox("Select Algorithm Route to Highlight", list(results.keys()), index=list(results.keys()).index("A*") if "A*" in results else 0)
        highlighted = results.get(algo_to_display)

        col_map, col_trace = st.columns([1.2, 1.0])
        with col_map:
            if highlighted:
                render_operations_map(
                    graph=sim.routing_service.graph,
                    incidents=[],
                    teams=[],
                    highlight_route=highlighted,
                    height=450,
                )
        with col_trace:
            st.markdown(f"###### {highlighted.algorithm_name} Step Trace")
            st.caption(highlighted.explanation)
            if highlighted.step_trace:
                df_trace = pd.DataFrame(highlighted.step_trace)
                st.dataframe(df_trace, use_container_width=True, height=350)
            else:
                st.info("No step trace recorded for trivial or empty route.")

        # Educational takeaway
        st.info(
            "**Key AI Concept Takeaway:** Notice that BFS minimizes edge count (hops) but does not consider weights. "
            "Uniform Cost Search (UCS) guarantees minimum weighted travel cost. A* incorporates an admissible Haversine "
            "distance heuristic to prune the search space towards the goal while preserving mathematical optimality. "
            "Greedy Best-First Search explores aggressively by heuristic alone, but sacrifices cost optimality."
        )

    # TAB 2: CSP VS BRANCH-AND-BOUND
    with tab_csp_opt:
        st.markdown("##### Constraint Satisfaction vs Branch-and-Bound Optimization")
        st.caption("Demonstrates the distinction between finding ANY feasible assignment (CSP) versus finding the COST-OPTIMAL assignment (Branch-and-Bound).")

        cmp_data = sim.metrics_service.compare_csp_vs_optimization()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("CSP Feasible", "Yes" if cmp_data["csp_feasible"] else "No")
        m2.metric("CSP Travel Cost", f"{cmp_data['csp_total_cost']:.1f} km")
        m3.metric("B&B Travel Cost", f"{cmp_data['opt_total_cost']:.1f} km", delta=f"-{cmp_data['cost_reduction_km']:.1f} km" if cmp_data['cost_reduction_km'] > 0 else "0.0 km")
        m4.metric("Branches Pruned", cmp_data["opt_branches_pruned"])

        c_csp, c_opt = st.columns(2)
        with c_csp:
            st.markdown("###### CSP Assignment (MRV + Forward Checking)")
            st.write(f"**Explored States:** {cmp_data['csp_nodes_explored']}")
            for inc_id, team_id in cmp_data["csp_assignments"].items():
                st.markdown(f"- Incident `{inc_id}` -> Team `{team_id}`")

        with c_opt:
            st.markdown("###### Branch-and-Bound Assignment (Global Minimum Cost)")
            st.write(f"**Explored States:** {cmp_data['opt_nodes_explored']} | **Subtrees Pruned:** {cmp_data['opt_branches_pruned']}")
            for inc_id, team_id in cmp_data["opt_assignments"].items():
                st.markdown(f"- Incident `{inc_id}` -> Team `{team_id}`")

        st.markdown("---")
        st.markdown("###### Why does Branch-and-Bound outperform basic CSP for route travel cost?")
        st.markdown("""
        - **Standard CSP** searches for *any* assignment satisfying all hard constraints (availability, skills, capacity). It stops at the first valid leaf found by MRV backtracking.
        - **Branch-and-Bound (B&B)** searches the space of feasible assignments to minimize total route kilometers. It computes an admissible lower bound on the remaining unassigned incidents. If the accumulated travel cost plus lower bound exceeds the best complete solution found so far, the entire branch is pruned!
        """)

    # TAB 3: CHARTS & OPERATIONAL METRICS
    with tab_charts:
        st.markdown("##### Telemetry & Evaluation Charts")

        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            st.markdown("###### Active Incident Urgency Distribution")
            p_dist = sim.metrics_service.get_priority_distribution()
            urg_df = pd.DataFrame([
                {"Urgency Level": f"Level {k}", "Count": v}
                for k, v in p_dist["urgency_counts"].items()
            ])
            fig_urg = px.bar(urg_df, x="Urgency Level", y="Count", color="Urgency Level", title="Incident Urgency Breakdown")
            st.plotly_chart(fig_urg, use_container_width=True)

        with col_ch2:
            st.markdown("###### Search Algorithm Nodes Explored Comparison")
            if "lab_results" in st.session_state:
                res_dict = st.session_state["lab_results"]
                algo_names = [r.algorithm_name for r in res_dict.values()]
                nodes_exp = [r.explored_nodes for r in res_dict.values()]
                costs = [r.cost for r in res_dict.values()]

                fig_comp = go.Figure()
                fig_comp.add_trace(go.Bar(x=algo_names, y=nodes_exp, name="Nodes Explored", marker_color="#1E88E5"))
                fig_comp.add_trace(go.Bar(x=algo_names, y=costs, name="Total Route Cost (km)", marker_color="#E53935"))
                fig_comp.update_layout(barmode="group", title="Nodes Explored vs Route Cost")
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("Run the Search Algorithm Lab to generate live benchmark comparisons.")
