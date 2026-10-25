"""Operations Overview dashboard view."""
import pandas as pd
import streamlit as st
from rescuemind.services.simulation_service import SimulationService
from rescuemind.ui.map_view import render_operations_map


def render_dashboard_view(sim: SimulationService):
    st.subheader("Twin Cities Operations Overview")
    st.caption("Real-time telemetry and dispatch intelligence for Islamabad and Rawalpindi rescue operations.")

    kpis = sim.metrics_service.get_summary_kpis()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            label="Active Incidents",
            value=kpis["active_incidents"],
            help="Incidents currently requiring response or in progress.",
        )
    with col2:
        st.metric(
            label="Unassigned Queue",
            value=kpis["unassigned_incidents"],
            delta=f"{kpis['unassigned_incidents']} awaiting team" if kpis['unassigned_incidents'] > 0 else "All covered",
            delta_color="inverse",
            help="High-priority incidents not yet matched to an available rescue team.",
        )
    with col3:
        st.metric(
            label="Coverage Rate",
            value=f"{kpis['coverage_rate_pct']}%",
            help="Percentage of active incidents assigned to qualified teams.",
        )
    with col4:
        st.metric(
            label="Available Teams",
            value=f"{kpis['available_teams']}/{kpis['total_teams']}",
            help="Rescue teams with uncommitted capacity and available status.",
        )
    with col5:
        st.metric(
            label="Disrupted Corridors",
            value=kpis["blocked_roads"],
            delta="Closed segments" if kpis["blocked_roads"] > 0 else "All roads open",
            delta_color="inverse",
            help="Number of blocked or impassable road segments in the metropolitan network.",
        )

    st.markdown("---")

    # Map and Queue side by side
    map_col, queue_col = st.columns([1.3, 1.0])

    with map_col:
        st.markdown("##### Metropolitan Road Network & Live Units")
        render_operations_map(
            graph=sim.routing_service.graph,
            incidents=sim.incident_service.get_all_incidents(),
            teams=sim.dispatch_service.get_all_teams(),
            active_plan=sim.dispatch_service.current_plan,
            height=480,
        )

    with queue_col:
        st.markdown("##### Priority Dispatch Queue")
        ranked = sim.incident_service.recompute_priorities()

        if not ranked:
            st.info("No active incidents currently reported.")
        else:
            queue_data = []
            for inc in ranked:
                queue_data.append({
                    "ID": inc.incident_id,
                    "Title": inc.title[:28] + "...",
                    "Animal": inc.animal_category.value.capitalize(),
                    "Score": f"{inc.priority_score:.1f}",
                    "Urgency": f"{inc.urgency}/5",
                    "Wait (min)": f"{inc.waiting_time:.0f}",
                    "Status": inc.status.value.upper(),
                    "Assigned": inc.assigned_team_id or "Unassigned",
                })
            df = pd.DataFrame(queue_data)
            st.dataframe(df, use_container_width=True, height=260)

        # Quick Dispatch Action
        st.markdown("##### Autonomous Dispatch Action")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run CSP Dispatch Cycle", use_container_width=True, type="primary"):
                plan = sim.dispatch_service.run_dispatch_cycle(use_optimization=False)
                st.success(f"Plan executed: {len(plan.assignments)} teams deployed.")
                st.rerun()
        with c2:
            if st.button("Advance Time (+15 min)", use_container_width=True):
                sim.advance_time(15.0)
                st.toast("Simulation clock advanced by 15 minutes. Waiting times and priorities updated.")
                st.rerun()

        # Latest Planning Rationale
        current_plan = sim.dispatch_service.current_plan
        if current_plan and current_plan.explanations:
            with st.expander("Latest Dispatch Intelligence & Rationale", expanded=True):
                st.caption(f"**Algorithm:** {current_plan.algorithm_used} | **Total Travel Cost:** {current_plan.total_cost:.1f} km")
                for exp in current_plan.explanations[:4]:
                    st.markdown(f"- {exp}")
