"""RescueMind: Twin Cities Animal Rescue Intelligence & Dispatch Simulator.
Modern, minimal, light-themed web interface for animal rescue coordination.
"""
from pathlib import Path
import streamlit as st
from rescuemind.services.simulation_service import SimulationService
from rescuemind.ui.analytics_views import render_analytics_view
from rescuemind.ui.dashboard import render_dashboard_view
from rescuemind.ui.operations_view import render_rescue_operations_view
from rescuemind.ui.settings_view import render_settings_view

# Page Configuration
st.set_page_config(
    page_title="RescueMind | Animal Rescue Intelligence",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Modern Animal Rescue Light Theme CSS
st.markdown("""
<style>
    /* Global styles and typography */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #1E293B;
    }

    /* Background overrides */
    .stApp {
        background-color: #F8FAF8;
    }

    /* Page title and headers */
    .page-title {
        font-size: 24px;
        font-weight: 700;
        color: #1B4D3E;
        letter-spacing: -0.02em;
        margin-bottom: 2px;
    }

    .page-caption {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 18px;
    }

    /* Metric cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8E4;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(27, 77, 62, 0.06);
    }
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748B;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #1B4D3E;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 9999px;
    }
    .badge-success { background-color: #E8F5E9; color: #2E7D32; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; }
    .badge-danger { background-color: #FEE2E2; color: #B91C1C; }
    .badge-info { background-color: #E0F2FE; color: #0369A1; }

    /* Button Enhancements */
    button[kind="primary"] {
        background-color: #1B4D3E !important;
        border-color: #1B4D3E !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.15s ease-in-out !important;
    }
    button[kind="primary"]:hover {
        background-color: #143D31 !important;
        border-color: #143D31 !important;
        box-shadow: 0 2px 6px rgba(20, 61, 49, 0.25) !important;
    }

    button[kind="secondary"] {
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #334155 !important;
        background-color: #FFFFFF !important;
    }
    button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #1E293B !important;
        border-radius: 8px !important;
    }

    /* Sidebar adjustments */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8E4;
    }

    /* Subtle dividers */
    hr {
        margin: 1.2rem 0 !important;
        border-color: #E2E8E4 !important;
    }
</style>
""", unsafe_allow_html=True)


def get_simulation_service() -> SimulationService:
    """Initialize or retrieve singleton SimulationService in Streamlit session state."""
    if "sim_service" not in st.session_state:
        data_dir = Path(__file__).resolve().parent / "rescuemind" / "data"
        st.session_state["sim_service"] = SimulationService(data_dir)
        # Execute an initial rescue plan so user immediately sees live operational data
        st.session_state["sim_service"].dispatch_service.run_dispatch_cycle()
    return st.session_state["sim_service"]


def main():
    sim = get_simulation_service()

    # Sidebar Navigation & Controls
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
            <span style="font-size: 24px;">🐾</span>
            <span style="font-size: 20px; font-weight: 700; color: #1B4D3E; letter-spacing: -0.02em;">RescueMind</span>
        </div>
        <div style="font-size: 13px; color: #64748B; margin-bottom: 16px;">Twin Cities Rescue Intelligence</div>
        """, unsafe_allow_html=True)

        # Telemetry Pill Card
        active_cnt = len(sim.incident_service.get_active_incidents())
        unassigned_cnt = len(sim.incident_service.get_unassigned_incidents())
        sim_time = f"+{sim.simulation_time_minutes:.0f} min"

        st.markdown(f"""
        <div style="background-color: #F1F6F3; border: 1px solid #DCE7E1; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #1B4D3E; margin-bottom: 4px;">System Status</div>
            <div style="font-size: 13px; color: #334155;"><strong>Clock:</strong> {sim_time}</div>
            <div style="font-size: 13px; color: #334155;"><strong>Active Requests:</strong> {active_cnt} ({unassigned_cnt} pending)</div>
            <div style="font-size: 12px; color: #64748B; margin-top: 4px;">Scenario: <em>{sim.active_scenario_id.replace('SCENARIO_', '')}</em></div>
        </div>
        """, unsafe_allow_html=True)

        # Simplified 4-Section Navigation
        menu = st.radio(
            "Navigation",
            [
                "Overview",
                "Rescue Operations",
                "AI Lab",
                "Insights & Settings",
            ],
            index=0,
            label_visibility="collapsed",
        )

        st.write("")
        st.markdown("---")
        st.markdown("<div style='font-size: 12px; font-weight: 600; color: #64748B; margin-bottom: 8px;'>QUICK ACTIONS</div>", unsafe_allow_html=True)

        if st.button("Update Rescue Plan", type="primary", use_container_width=True):
            sim.dispatch_service.run_dispatch_cycle()
            st.toast("Rescue plan calculated and deployed.")
            st.rerun()

        if st.button("Advance Clock (+15m)", use_container_width=True):
            sim.advance_time(15.0)
            st.toast("Simulation advanced by 15 minutes.")
            st.rerun()

        st.markdown("---")
        st.markdown("""
        <div style="font-size: 11px; color: #94A3B8; text-align: center;">
            Academic AI Decision Support System<br>
            Islamabad – Rawalpindi Network
        </div>
        """, unsafe_allow_html=True)

    # 4-Section Page Routing
    if menu == "Overview":
        render_dashboard_view(sim)
    elif menu == "Rescue Operations":
        render_rescue_operations_view(sim)
    elif menu == "AI Lab":
        render_analytics_view(sim)
    elif menu == "Insights & Settings":
        render_settings_view(sim)

    # Footer Disclaimer
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 12px; color: #94A3B8; text-align: center; padding-bottom: 20px;">
        RescueMind Simulator &bull; Educational AI Project &bull; Synthetic Islamabad & Rawalpindi Network &bull; 
        Does not dispatch real rescue personnel or provide certified veterinary medical triage.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
