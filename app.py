"""RescueMind: Twin Cities Animal Rescue Intelligence and Dispatch Simulator.
Main application entry point.
"""
from pathlib import Path
import streamlit as st
from rescuemind.services.simulation_service import SimulationService
from rescuemind.ui.analytics_views import render_analytics_view
from rescuemind.ui.dashboard import render_dashboard_view
from rescuemind.ui.dispatch_views import render_dispatch_view
from rescuemind.ui.incident_views import render_incidents_view
from rescuemind.ui.map_view import render_operations_map
from rescuemind.ui.settings_view import render_settings_view

# Page Configuration
st.set_page_config(
    page_title="RescueMind | Twin Cities Animal Rescue Intelligence",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Emergency Operations CSS
st.markdown("""
<style>
    .main-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-weight: 700;
        color: #1A237E;
        margin-bottom: 0px;
    }
    .status-badge {
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 13px;
        display: inline-block;
    }
    .status-active { background-color: #E8F5E9; color: #2E7D32; }
    .status-disrupted { background-color: #FFEBEE; color: #C62828; }
</style>
""", unsafe_allow_html=True)


def get_simulation_service() -> SimulationService:
    """Initialize or retrieve singleton SimulationService in Streamlit session state."""
    if "sim_service" not in st.session_state:
        data_dir = Path(__file__).resolve().parent / "rescuemind" / "data"
        st.session_state["sim_service"] = SimulationService(data_dir)
        # Run initial dispatch cycle so user immediately sees a live operational plan
        st.session_state["sim_service"].dispatch_service.run_dispatch_cycle()
    return st.session_state["sim_service"]


def main():
    sim = get_simulation_service()

    # Sidebar Navigation & Controls
    with st.sidebar:
        st.markdown("### 🐾 RescueMind")
        st.caption("Twin Cities Rescue Intelligence")
        st.markdown("---")

        # Telemetry Status Widget
        active_cnt = len(sim.incident_service.get_active_incidents())
        unassigned_cnt = len(sim.incident_service.get_unassigned_incidents())
        sim_time = f"+{sim.simulation_time_minutes:.0f} min"

        st.markdown(
            f"**Clock:** `{sim_time}` | **Queue:** `{active_cnt}` calls\n\n"
            f"**Scenario:** `{sim.active_scenario_id}`"
        )
        st.markdown("---")

        menu = st.radio(
            "Operations Navigation",
            [
                "Operations Overview",
                "Live Operations Map",
                "Incident Registry & Intake",
                "Dispatch Center",
                "AI Lab & Search Arena",
                "Analytics & KPI Evaluation",
                "Settings & Scenarios",
            ],
            index=0,
        )

        st.markdown("---")
        st.caption("⚡ Quick Simulation Controls")
        if st.button("Advance Clock (+15m)", use_container_width=True):
            sim.advance_time(15.0)
            st.toast("Simulation advanced by 15 minutes.")
            st.rerun()

        if st.button("Trigger Autonomous Replan", use_container_width=True):
            sim.dispatch_service.run_dispatch_cycle()
            st.toast("Dispatch coordination cycle executed.")
            st.rerun()

        st.markdown("---")
        st.caption("Educational AI Research Simulator.\nIslamabad-Rawalpindi Synthetic Grid.")

    # Page Routing
    if menu == "Operations Overview":
        render_dashboard_view(sim)
    elif menu == "Live Operations Map":
        st.subheader("Twin Cities Live Operations Map")
        st.caption("Real-time geographic depiction of incidents, road networks, rescue teams, and active routes.")

        c_f1, c_f2 = st.columns([2, 1])
        with c_f1:
            all_incidents = sim.incident_service.get_active_incidents()
            inc_options = ["-- None --"] + [f"{i.incident_id}: {i.title}" for i in all_incidents]
            selected_inc_str = st.selectbox("Focus on Incident", inc_options)
            sel_id = selected_inc_str.split(":")[0] if selected_inc_str != "-- None --" else None

        render_operations_map(
            graph=sim.routing_service.graph,
            incidents=sim.incident_service.get_all_incidents(),
            teams=sim.dispatch_service.get_all_teams(),
            active_plan=sim.dispatch_service.current_plan,
            selected_incident_id=sel_id,
            height=600,
        )

    elif menu == "Incident Registry & Intake":
        render_incidents_view(sim)
    elif menu == "Dispatch Center":
        render_dispatch_view(sim)
    elif menu == "AI Lab & Search Arena":
        render_analytics_view(sim)
    elif menu == "Analytics & KPI Evaluation":
        render_analytics_view(sim)
    elif menu == "Settings & Scenarios":
        render_settings_view(sim)

    # Footer Disclaimer
    st.markdown("---")
    st.caption(
        "RescueMind Simulator © Academic AI Project | Synthetic telemetry modeling Islamabad & Rawalpindi. "
        "Does not dispatch real rescue personnel or provide medical/veterinary triage."
    )


if __name__ == "__main__":
    main()
