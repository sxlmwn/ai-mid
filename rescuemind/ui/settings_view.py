"""Settings and dynamic scenario simulation controls."""
import streamlit as st
from rescuemind.algorithms.priority import PriorityWeights
from rescuemind.services.simulation_service import SimulationService
from rescuemind.utils.constants import DISCLAIMER_TEXT


def render_settings_view(sim: SimulationService):
    st.subheader("Simulation Controls & System Settings")
    st.caption("Inject road disruptions, tune heuristic weights, switch scenarios, and audit simulation integrity.")

    s_tab1, s_tab2, s_tab3, s_tab4 = st.tabs(["Predefined Scenarios", "Road Disruption Controls", "Priority Scoring Weights", "Responsible AI & Ethics"])

    # TAB 1: SCENARIOS
    with s_tab1:
        st.markdown("##### Predefined Operational Scenarios")
        st.caption("Load structured scenarios designed for university presentation and viva demonstration.")

        scenarios = sim.scenarios_data
        sc_keys = list(scenarios.keys())

        chosen_sc_id = st.selectbox(
            "Select Scenario",
            sc_keys,
            format_func=lambda k: f"{scenarios[k]['name']} ({k})",
        )
        selected_sc = scenarios[chosen_sc_id]

        st.info(f"**Description:** {selected_sc['description']}")
        st.write(f"- **Blocked Roads:** {selected_sc.get('blocked_roads', []) or 'None'}")
        st.write(f"- **Congestions:** {selected_sc.get('congestions', []) or 'Normal traffic'}")

        c_sc1, c_sc2 = st.columns(2)
        with c_sc1:
            if st.button("Apply Selected Scenario", type="primary", use_container_width=True):
                sim.load_scenario(chosen_sc_id)
                st.success(f"Scenario '{selected_sc['name']}' loaded successfully.")
                st.rerun()
        with c_sc2:
            if st.button("Reset Simulation to Baseline", use_container_width=True):
                sim.reset_all()
                st.success("Simulation fully restored to baseline conditions.")
                st.rerun()

    # TAB 2: ROAD DISRUPTIONS
    with s_tab2:
        st.markdown("##### Dynamic Road Disruption Injector")
        st.caption("Simulate real-time road closures or severe weather congestion, triggering autonomous route replanning.")

        all_edges = sim.routing_service.get_all_edges()
        edge_options = [f"{e.start_node} <--> {e.end_node} ({e.road_name})" for e in all_edges]

        selected_edge_str = st.selectbox("Select Road Segment", edge_options)
        idx = edge_options.index(selected_edge_str)
        target_edge = all_edges[idx]

        st.write(
            f"**Segment Status:** {'CLOSED / BLOCKED' if not target_edge.is_open else 'OPEN'} | "
            f"**Base Cost:** {target_edge.cost} km | **Congestion:** {target_edge.congestion_multiplier:.1f}x"
        )

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            if target_edge.is_open:
                if st.button("Block This Road Segment", type="primary", use_container_width=True):
                    sim.routing_service.block_road(target_edge.start_node, target_edge.end_node)
                    # Trigger autonomous replan for any active routes passing through this edge!
                    replan_notes = sim.dispatch_service.replan_disrupted_routes(target_edge.start_node, target_edge.end_node)
                    st.warning(f"Road blocked between {target_edge.start_node} and {target_edge.end_node}!")
                    for note in replan_notes:
                        st.info(note)
                    st.rerun()
            else:
                if st.button("Reopen This Road Segment", use_container_width=True):
                    sim.routing_service.unblock_road(target_edge.start_node, target_edge.end_node)
                    st.success(f"Road reopened between {target_edge.start_node} and {target_edge.end_node}.")
                    st.rerun()

        with c_d2:
            new_cong = st.slider("Simulated Congestion Multiplier", 1.0, 4.0, float(target_edge.congestion_multiplier), step=0.5)
            if st.button("Apply Congestion Multiplier", use_container_width=True):
                sim.routing_service.set_congestion(target_edge.start_node, target_edge.end_node, new_cong)
                st.success(f"Congestion updated to {new_cong}x.")
                st.rerun()

        st.markdown("---")
        st.markdown("###### Road Disruption Event Log")
        if sim.routing_service.disruption_history:
            for item in reversed(sim.routing_service.disruption_history[-10:]):
                st.text(f"• {item}")
        else:
            st.info("No road disruptions recorded.")

    # TAB 3: WEIGHT ADJUSTER
    with s_tab3:
        st.markdown("##### Multi-Factor Priority Scoring Policy")
        st.caption("Adjust weight contributions for the priority queue scoring function without touching source code.")

        current_w = sim.incident_service.priority_weights
        c_w1, c_w2, c_w3 = st.columns(3)
        with c_w1:
            w_urg = st.slider("Urgency Weight", 0.0, 1.0, float(current_w.weight_urgency), 0.05)
        with c_w2:
            w_wait = st.slider("Waiting Time Weight", 0.0, 1.0, float(current_w.weight_waiting), 0.05)
        with c_w3:
            w_vuln = st.slider("Vulnerability Weight", 0.0, 1.0, float(current_w.weight_vulnerability), 0.05)

        if st.button("Update Scoring Weights", type="primary", use_container_width=True):
            new_weights = PriorityWeights(
                weight_urgency=w_urg,
                weight_waiting=w_wait,
                weight_vulnerability=w_vuln,
            )
            sim.incident_service.set_priority_weights(new_weights)
            st.success("Priority weights updated and incident queue recalculated.")
            st.rerun()

    # TAB 4: ETHICS & NOTICE
    with s_tab4:
        st.markdown("##### Research & Educational Disclaimer")
        st.warning(DISCLAIMER_TEXT)

        st.markdown("""
        ### Ethical Considerations & Responsible AI Design
        1. **Simulation Scope:** All coordinates, animal cases, transit costs, and rescuer teams represent a synthetic demonstration environment in the Twin Cities.
        2. **Human-in-the-Loop:** Automated AI plans recommend dispatch pairings, but operational confirmation remains in human hands.
        3. **Transparency over Black-Boxes:** Decisions rely on verifiable AI algorithms (A*, UCS, Backtracking CSP, and Branch-and-Bound) with explicit mathematical traces.
        4. **Non-Clinical Triage:** The multi-factor priority score is an operational dispatch scheduling model, not a certified veterinary triage diagnosis.
        """)
