"""Interactive Folium map view for Islamabad-Rawalpindi rescue operations."""
from __future__ import annotations
from typing import Dict, List, Optional
import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium
from rescuemind.algorithms.graph import RoadGraph
from rescuemind.models.dispatch import DispatchPlan, RouteResult
from rescuemind.models.incident import Incident
from rescuemind.models.rescue_team import RescueTeam
from rescuemind.utils.constants import DEFAULT_MAP_CENTER, DEFAULT_ZOOM_LEVEL


def render_operations_map(
    graph: RoadGraph,
    incidents: List[Incident],
    teams: List[RescueTeam],
    active_plan: Optional[DispatchPlan] = None,
    highlight_route: Optional[RouteResult] = None,
    selected_incident_id: Optional[str] = None,
    width: int = 800,
    height: int = 550,
):
    """Render interactive Folium map with road network, facilities, incidents, and routes."""
    m = folium.Map(
        location=DEFAULT_MAP_CENTER,
        zoom_start=DEFAULT_ZOOM_LEVEL,
        tiles="CartoDB positron",
        control_scale=True,
    )

    # 1. Render Road Network
    for edge in graph.get_all_edges():
        u_node = graph.nodes.get(edge.start_node)
        v_node = graph.nodes.get(edge.end_node)
        if not u_node or not v_node:
            continue

        coords = [[u_node.latitude, u_node.longitude], [v_node.latitude, v_node.longitude]]

        if not edge.is_open:
            color = "#D32F2F"  # Red for blocked
            dash_array = "8, 8"
            weight = 4
            status_text = "BLOCKED"
        elif edge.congestion_multiplier > 1.0:
            color = "#FB8C00"  # Orange for congested
            dash_array = None
            weight = 3.5
            status_text = f"Congested ({edge.congestion_multiplier:.1f}x)"
        else:
            color = "#78909C"  # Steel grey for normal
            dash_array = None
            weight = 2.5
            status_text = "Open"

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=weight,
            dash_array=dash_array,
            opacity=0.8,
            tooltip=f"{edge.road_name} ({edge.start_node} - {edge.end_node}): {status_text} | Cost: {edge.effective_cost}km",
        ).add_to(m)

    # 2. Render Graph Nodes (Facilities & Junctions)
    for node in graph.nodes.values():
        if node.node_type == "base":
            icon_color = "darkblue"
            icon_name = "home"
        elif node.node_type == "clinic":
            icon_color = "green"
            icon_name = "medkit"
        else:
            icon_color = "cadetblue"
            icon_name = "circle"

        folium.CircleMarker(
            location=[node.latitude, node.longitude],
            radius=6 if node.node_type != "base" else 9,
            color=icon_color,
            fill=True,
            fill_color=icon_color,
            fill_opacity=0.8,
            popup=folium.Popup(f"<b>{node.name}</b><br>ID: {node.node_id}<br>Type: {node.node_type.upper()}", max_width=250),
            tooltip=f"{node.name} ({node.node_id})",
        ).add_to(m)

    # 3. Render Active Incidents
    urgency_color_map = {
        5: "#D32F2F",  # Red (Life Threatening)
        4: "#E64A19",  # Deep Orange (Critical)
        3: "#FFA000",  # Amber (High)
        2: "#FBC02D",  # Yellow (Moderate)
        1: "#388E3C",  # Green (Low)
    }

    for inc in incidents:
        if not inc.is_active():
            continue

        color = urgency_color_map.get(inc.urgency, "#E64A19")
        is_selected = (inc.incident_id == selected_incident_id)
        radius = 12 if is_selected else 8

        popup_html = (
            f"<div style='font-family: sans-serif; font-size: 13px;'>"
            f"<b>{inc.incident_id}: {inc.title}</b><br>"
            f"<b>Category:</b> {inc.animal_category.value.upper()}<br>"
            f"<b>Urgency:</b> Level {inc.urgency}/5<br>"
            f"<b>Priority Score:</b> {inc.priority_score:.1f} pts<br>"
            f"<b>Waiting Time:</b> {inc.waiting_time:.0f} mins<br>"
            f"<b>Required Skills:</b> {', '.join(inc.required_skills) or 'General'}<br>"
            f"<b>Status:</b> {inc.status.value.upper()}<br>"
            f"<b>Assigned Team:</b> {inc.assigned_team_id or 'None'}"
            f"</div>"
        )

        folium.CircleMarker(
            location=[inc.latitude, inc.longitude],
            radius=radius,
            color="#212121" if is_selected else color,
            weight=3 if is_selected else 1,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Incident {inc.incident_id}: {inc.title} (Urgency {inc.urgency}/5)",
        ).add_to(m)

    # 4. Render Rescue Teams
    for team in teams:
        folium.Marker(
            location=[team.latitude, team.longitude],
            icon=folium.Icon(color="blue", icon="ambulance", prefix="fa"),
            tooltip=f"{team.name} ({team.team_id}) - Status: {team.status.value}",
            popup=f"<b>{team.name}</b><br>ID: {team.team_id}<br>Status: {team.status.value}<br>Capacity: {len(team.current_assignments)}/{team.capacity}<br>Skills: {', '.join(team.skills)}",
        ).add_to(m)

    # 5. Render Active Dispatched Routes
    if active_plan:
        for assignment in active_plan.assignments:
            route = assignment.route
            if route and route.success and len(route.path) >= 2:
                path_coords = []
                for node_id in route.path:
                    node = graph.nodes.get(node_id)
                    if node:
                        path_coords.append([node.latitude, node.longitude])

                folium.PolyLine(
                    locations=path_coords,
                    color="#2E7D32",  # Dark Green for active dispatch
                    weight=5,
                    opacity=0.85,
                    tooltip=f"Dispatch Route: {assignment.team_id} -> {assignment.incident_id} (Cost: {route.cost}km)",
                ).add_to(m)

    # 6. Highlight Specific Selected Algorithm Route
    if highlight_route and highlight_route.success and len(highlight_route.path) >= 2:
        high_coords = []
        for node_id in highlight_route.path:
            node = graph.nodes.get(node_id)
            if node:
                high_coords.append([node.latitude, node.longitude])

        folium.PolyLine(
            locations=high_coords,
            color="#9C27B0",  # Purple for AI search comparison highlight
            weight=6,
            dash_array="5, 10",
            opacity=0.95,
            tooltip=f"{highlight_route.algorithm_name}: {' -> '.join(highlight_route.path)} (Cost: {highlight_route.cost}km)",
        ).add_to(m)

    # Display map in Streamlit with error fallback
    try:
        st_folium(m, width="100%", height=height, returned_objects=[])
    except Exception as e:
        st.warning(f"Map interactive rendering fallback: {e}")
        st.info("Interactive map fallback active. Network topology and route nodes are listed below.")
