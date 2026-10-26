"""Insights & Settings view: operational analytics, scenarios, scoring weights, and ethics."""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from rescuemind.algorithms.priority import PriorityWeights
from rescuemind.services.simulation_service import SimulationService
from rescuemind.utils.constants import DISCLAIMER_TEXT


def render_settings_view(sim: SimulationService):
    st.markdown('<div class="page-title">Insights & Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-caption">Operational charts, simulation scenarios, priority policy configuration, and ethics standards.</div>', unsafe_allow_html=True)

    tab_insights, tab_scen, tab_weights, tab_ethics = st.tabs([
        "Operational Insights",
        "Simulation Scenarios",
        "Priority Policy Settings",
        "Responsible AI & Notice",
    ])

    # TAB 1: OPERATIONAL INSIGHTS
    with tab_insights:
        st.markdown("#### Real-Time Telemetry & Insights")

        ch_col1, ch_col2 = st.columns(2)
        with ch_col1:
            st.markdown("##### Request Urgency Distribution")
            p_dist = sim.metrics_service.get_priority_distribution()
            urg_data = [
                {"Urgency Level": f"Level {k}", "Count": v}
                for k, v in p_dist["urgency_counts"].items()
            ]
            fig_urg = px.bar(
                pd.DataFrame(urg_data),
                x="Urgency Level",
                y="Count",
                color="Urgency Level",
                color_discrete_sequence=["#A7D7C5", "#68B2A0", "#2C6975", "#E07A5F", "#D62828"],
            )
            fig_urg.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                showlegend=False,
            )
            st.plotly_chart(fig_urg, use_container_width=True)

        with ch_col2:
            st.markdown("##### Search Efficiency Comparison")
            if "lab_results" in st.session_state:
                res_dict = st.session_state["lab_results"]
                algo_names = [r.algorithm_name.split()[0] for r in res_dict.values()]
                nodes_exp = [r.explored_nodes for r in res_dict.values()]
                costs = [r.cost for r in res_dict.values()]

                fig_comp = go.Figure()
                fig_comp.add_trace(go.Bar(
                    x=algo_names,
                    y=nodes_exp,
                    name="Locations Explored",
                    marker_color="#1B4D3E",
                ))
                fig_comp.add_trace(go.Bar(
                    x=algo_names,
                    y=costs,
                    name="Route Distance (km)",
                    marker_color="#D97706",
                ))
                fig_comp.update_layout(
                    barmode="group",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=260,
                    legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("Run the AI Lab route comparison to view live algorithm benchmark charts here.")

    # TAB 2: SIMULATION SCENARIOS
    with tab_scen:
        st.markdown("#### Operational Simulation Scenarios")
        st.caption("Switch between predefined situations to demonstrate dynamic routing and capacity resilience.")

        scenarios = sim.scenarios_data
        sc_keys = list(scenarios.keys())

        chosen_sc_id = st.selectbox(
            "Select Scenario",
            sc_keys,
            format_func=lambda k: f"{scenarios[k]['name']}",
        )
        selected_sc = scenarios[chosen_sc_id]

        st.info(f"**Scenario Description:** {selected_sc['description']}")

        c_sc1, c_sc2 = st.columns([1.2, 1.0])
        with c_sc1:
            if st.button("Apply Selected Scenario", type="primary", use_container_width=True):
                sim.load_scenario(chosen_sc_id)
                st.success(f"Loaded scenario: {selected_sc['name']}")
                st.rerun()
        with c_sc2:
            if st.button("Reset Simulation to Baseline", use_container_width=True):
                sim.reset_all()
                st.success("Simulation fully restored to pristine baseline.")
                st.rerun()

    # TAB 3: PRIORITY POLICY SETTINGS
    with tab_weights:
        st.markdown("#### Priority Queue Weighting Policy")
        st.caption("Adjust how the system balances medical urgency, waiting duration, and special vulnerability.")

        current_w = sim.incident_service.priority_weights
        c_w1, c_w2, c_w3 = st.columns(3)
        with c_w1:
            w_urg = st.slider("Urgency Weight", 0.0, 1.0, float(current_w.weight_urgency), 0.05)
        with c_w2:
            w_wait = st.slider("Waiting Time Weight", 0.0, 1.0, float(current_w.weight_waiting), 0.05)
        with c_w3:
            w_vuln = st.slider("Vulnerability Weight", 0.0, 1.0, float(current_w.weight_vulnerability), 0.05)

        if st.button("Save Policy Weights", type="primary"):
            new_weights = PriorityWeights(
                weight_urgency=w_urg,
                weight_waiting=w_wait,
                weight_vulnerability=w_vuln,
            )
            sim.incident_service.set_priority_weights(new_weights)
            st.success("Priority weights saved! All requests in queue have been recalculated.")
            st.rerun()

    # TAB 4: RESPONSIBLE AI & ETHICS
    with tab_ethics:
        st.markdown("#### Responsible AI & Educational Transparency")
        st.warning(DISCLAIMER_TEXT)

        st.markdown("""
        ##### Core Ethical Principles in RescueMind
        1. **Human-in-the-Loop Oversight:** The AI system acts as a recommendation assistant. Human operators review and confirm all dispatch actions.
        2. **Explainable AI:** Every team assignment, rejection, and route choice is accompanied by an evidence-based explanation derived directly from hard constraints and mathematical costs.
        3. **Deterministic Fairness:** Tie-breaking is deterministic (using creation sequence numbers), preventing arbitrary favoritism.
        4. **Transparent Boundaries:** The system does not claim veterinary medical diagnosis, and uses clearly marked synthetic telemetry.
        """)
