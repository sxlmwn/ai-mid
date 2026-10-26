"""Overview screen: key metrics, map preview, urgent requests, and primary actions."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from rescuemind.models.incident import IncidentStatus
from rescuemind.services.simulation_service import SimulationService
from rescuemind.ui.map_view import render_operations_map


def render_dashboard_view(sim: SimulationService):
    st.markdown('<div class="page-title">Operations Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-caption">Twin Cities animal rescue coordination and operational status</div>', unsafe_allow_html=True)

    kpis = sim.metrics_service.get_summary_kpis()

    # 1. Four clean, well-spaced metric cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Requests</div>
            <div class="metric-value">{kpis['active_incidents']}</div>
            <div class="metric-sub">Total emergencies in progress</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        unassigned_sub = "All requests covered" if kpis['unassigned_incidents'] == 0 else f"{kpis['unassigned_incidents']} needing rescue teams"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Awaiting Assignment</div>
            <div class="metric-value" style="color: {'#B91C1C' if kpis['unassigned_incidents'] > 0 else '#1B4D3E'};">{kpis['unassigned_incidents']}</div>
            <div class="metric-sub">{unassigned_sub}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Available Teams</div>
            <div class="metric-value">{kpis['available_teams']} <span style="font-size: 16px; color: #64748B;">/ {kpis['total_teams']}</span></div>
            <div class="metric-sub">Ready for immediate dispatch</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        road_color = "#B91C1C" if kpis['blocked_roads'] > 0 else "#1B4D3E"
        road_sub = "All primary routes open" if kpis['blocked_roads'] == 0 else "Detours in effect"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Road Disruptions</div>
            <div class="metric-value" style="color: {road_color};">{kpis['blocked_roads']}</div>
            <div class="metric-sub">{road_sub}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 2. Main content: Map Preview (left) and Priority Requests & Action (right)
    col_map, col_queue = st.columns([1.35, 1.0])

    with col_map:
        st.markdown("#### Live Network & Active Rescues")
        render_operations_map(
            graph=sim.routing_service.graph,
            incidents=sim.incident_service.get_all_incidents(),
            teams=sim.dispatch_service.get_all_teams(),
            active_plan=sim.dispatch_service.current_plan,
            height=460,
        )

    with col_queue:
        st.markdown("#### Primary Actions")
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button("Generate Rescue Plan", type="primary", use_container_width=True):
                plan = sim.dispatch_service.run_dispatch_cycle()
                st.success(f"Rescue plan updated: {len(plan.assignments)} teams deployed.")
                st.rerun()
        with c_act2:
            if st.button("Advance Clock (+15m)", use_container_width=True):
                sim.advance_time(15.0)
                st.toast("Time advanced by 15 minutes. Waiting times and priorities recalculated.")
                st.rerun()

        st.markdown("#### Requests Awaiting Attention")
        ranked = sim.incident_service.recompute_priorities()
        unassigned_requests = [i for i in ranked if i.is_active() and not i.assigned_team_id]

        if not unassigned_requests:
            st.markdown("""
            <div style="background-color: #E8F5E9; border: 1px solid #C8E6C9; border-radius: 8px; padding: 14px; color: #2E7D32; font-size: 14px;">
                <strong>All requests covered.</strong> No pending distress calls are currently waiting for a team.
            </div>
            """, unsafe_allow_html=True)
        else:
            table_data = []
            for inc in unassigned_requests[:5]:
                urgency_badges = {
                    5: "🔴 Critical",
                    4: "🟠 High",
                    3: "🟡 Moderate",
                    2: "🟢 Low",
                    1: "⚪ Minor",
                }
                table_data.append({
                    "Request": inc.title,
                    "Animal": inc.animal_category.value.capitalize(),
                    "Urgency": urgency_badges.get(inc.urgency, str(inc.urgency)),
                    "Wait Time": f"{inc.waiting_time:.0f} min",
                    "Score": f"{inc.priority_score:.1f}",
                })
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, height=200, hide_index=True)

        # Current Rescue Plan Summary Card
        current_plan = sim.dispatch_service.current_plan
        if current_plan:
            st.markdown("#### Current Rescue Plan")
            assigned_count = len(current_plan.assignments)
            cost_text = f"{current_plan.total_cost:.1f} km"
            unassigned_count = len(current_plan.unassigned_incidents)

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8E4; border-radius: 8px; padding: 14px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #1E293B;">Plan ID: {current_plan.plan_id}</span>
                    <span style="color: #64748B; font-size: 13px;">Total Distance: <strong>{cost_text}</strong></span>
                </div>
                <div style="font-size: 13px; color: #475569; margin-bottom: 6px;">
                    Teams Assigned: <strong>{assigned_count}</strong> | Awaiting Assignment: <strong>{unassigned_count}</strong>
                </div>
                <div style="font-size: 12px; color: #64748B;">
                    Method: {current_plan.algorithm_used}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if current_plan.explanations:
                with st.expander("Why these assignments were chosen", expanded=False):
                    for expl in current_plan.explanations[:3]:
                        st.markdown(f"• {expl}")
