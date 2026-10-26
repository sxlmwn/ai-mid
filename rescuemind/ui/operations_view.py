"""Rescue Operations view: interactive map, active plans, requests, fleet, and road controls."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from rescuemind.models.incident import AnimalCategory, IncidentStatus
from rescuemind.models.rescue_team import TeamStatus
from rescuemind.services.simulation_service import SimulationService
from rescuemind.ui.map_view import render_operations_map
from rescuemind.utils.constants import ALL_SKILLS


def render_rescue_operations_view(sim: SimulationService):
    st.markdown('<div class="page-title">Rescue Operations</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-caption">Coordinate active missions, manage distress calls, track rescue teams, and adapt to road conditions.</div>', unsafe_allow_html=True)

    if st.session_state.get("replan_alerts"):
        for alert in st.session_state["replan_alerts"]:
            st.warning(f"🚨 **Autonomous Replan Alert:** {alert}")
        if st.button("Dismiss Alert", key="dismiss_replan_alert"):
            st.session_state["replan_alerts"] = []
            st.rerun()

    # 1. Action & Mode Bar
    col_act1, col_act2, col_act3, col_act4 = st.columns([1.5, 1.2, 1.2, 1.1])
    with col_act1:
        assignment_strategy = st.selectbox(
            "Rescue Planning Strategy",
            ["Standard Operational Matching (CSP)", "Cost-Optimized Matching (Branch-and-Bound)"],
            help="Standard matching finds qualified teams satisfying all constraints. Cost-optimized minimizes total fleet distance.",
        )
    with col_act2:
        routing_algo = st.selectbox(
            "Routing Method",
            ["A*", "UCS (Uniform Cost)", "BFS (Fewest Hops)", "Greedy Best-First"],
            index=0,
            help="Pathfinding algorithm used to generate routes for teams.",
        )
    with col_act3:
        st.write("")
        st.write("")
        use_opt = "Branch-and-Bound" in assignment_strategy
        if st.button("Update Rescue Plan", type="primary", use_container_width=True):
            plan = sim.dispatch_service.run_dispatch_cycle(
                use_optimization=use_opt,
                routing_algo=routing_algo,
            )
            st.success(f"Rescue plan updated! {len(plan.assignments)} teams deployed.")
            st.rerun()
    with col_act4:
        st.write("")
        st.write("")
        if st.button("Advance (+15m)", use_container_width=True):
            sim.advance_time(15.0)
            st.toast("Time advanced by 15 minutes.")
            st.rerun()

    st.write("")

    # 2. Prominent Interactive Map
    with st.container():
        active_incidents = sim.incident_service.get_active_incidents()
        focus_options = ["-- Show All Incidents --"] + [f"{i.incident_id}: {i.title}" for i in active_incidents]
        c_focus1, _ = st.columns([2.0, 1.0])
        with c_focus1:
            sel_focus = st.selectbox("Focus Map View on Incident", focus_options, label_visibility="collapsed")
            focus_id = sel_focus.split(":")[0] if sel_focus != "-- Show All Incidents --" else None

        render_operations_map(
            graph=sim.routing_service.graph,
            incidents=sim.incident_service.get_all_incidents(),
            teams=sim.dispatch_service.get_all_teams(),
            active_plan=sim.dispatch_service.current_plan,
            selected_incident_id=focus_id,
            height=460,
        )

    st.write("")

    # 3. Operations Workflow Tabs
    op_tab1, op_tab2, op_tab3, op_tab4 = st.tabs([
        "Active Rescue Plan",
        "Requests Awaiting Attention",
        "Report Animal in Distress",
        "Rescue Fleet & Road Conditions",
    ])

    # TAB 1: ACTIVE RESCUE PLAN
    with op_tab1:
        plan = sim.dispatch_service.current_plan
        if not plan:
            st.info("No active rescue plan generated yet. Click 'Update Rescue Plan' above.")
        else:
            p_col1, p_col2, p_col3 = st.columns(3)
            p_col1.metric("Active Deployments", len(plan.assignments))
            p_col2.metric("Awaiting Teams", len(plan.unassigned_incidents))
            p_col3.metric("Total Route Distance", f"{plan.total_cost:.1f} km")

            st.markdown("##### Current Assignments & Routes")
            if not plan.assignments:
                st.warning("No suitable team available for current requests under active constraints.")
            else:
                rows = []
                for a in plan.assignments:
                    inc = sim.incident_service.get_incident(a.incident_id)
                    team = sim.dispatch_service.get_team(a.team_id)
                    route = a.route
                    rows.append({
                        "Request ID": a.incident_id,
                        "Title": inc.title if inc else "Unknown",
                        "Team Dispatched": team.name if team else a.team_id,
                        "Team Base": team.current_location_id if team else "N/A",
                        "Destination": inc.location_id if inc else "N/A",
                        "Route Taken": " -> ".join(route.path) if route and route.success else "Unavailable",
                        "Route Cost (km)": f"{route.cost:.1f}" if route else "N/A",
                        "Travel Time": f"{route.travel_time:.1f} min" if route else "N/A",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Assignment Explanations
            if plan.explanations:
                with st.expander("Why these rescue teams were chosen", expanded=False):
                    for expl in plan.explanations:
                        st.markdown(f"• {expl}")

            # Unassigned Cases
            if plan.unassigned_incidents:
                st.markdown("##### Requests Without Available Teams")
                unassigned_rows = []
                for inc_id, reason in plan.unassigned_incidents.items():
                    inc = sim.incident_service.get_incident(inc_id)
                    # Translate to simpler language
                    clean_reason = reason.replace("Domain empty", "No qualified team available").replace("Conflict with team capacity constraints", "All suitable teams currently at full capacity")
                    unassigned_rows.append({
                        "Request ID": inc_id,
                        "Animal": inc.animal_category.value.capitalize() if inc else "N/A",
                        "Priority": f"{inc.priority_score:.1f} pts" if inc else "N/A",
                        "Skills Needed": ", ".join(inc.required_skills) if inc and inc.required_skills else "General",
                        "Explanation": clean_reason,
                    })
                st.dataframe(pd.DataFrame(unassigned_rows), use_container_width=True, hide_index=True)

            # Candidate Team Rejections Audit Log
            with st.expander("Candidate Team Rejections Audit Log (Constraint Checks)", expanded=False):
                st.caption("Detailed record of candidate rescue teams rejected during Constraint Satisfaction Problem (CSP) solving.")
                from rescuemind.algorithms.assignment import RescueTeamCSP
                active = sim.incident_service.get_active_incidents()[:sim.dispatch_service.planning_horizon]
                csp_auditor = RescueTeamCSP(active, sim.dispatch_service.get_all_teams(), sim.routing_service.graph)
                csp_auditor.solve([i.incident_id for i in active])

                if csp_auditor.rejections:
                    rej_data = []
                    for r in csp_auditor.rejections[:25]:
                        rej_data.append({
                            "Request ID": r.incident_id,
                            "Team ID": r.team_id,
                            "Failed Constraint": r.failed_constraint,
                            "Diagnostic Reason": r.explanation,
                        })
                    st.dataframe(pd.DataFrame(rej_data), use_container_width=True, hide_index=True)
                else:
                    st.info("No candidates rejected during this planning cycle.")

            # Before-and-After Replan Comparison
            prev_plan = sim.dispatch_service.previous_plan
            if prev_plan:
                with st.expander("Compare with Previous Rescue Plan", expanded=False):
                    c_prv, c_cur = st.columns(2)
                    with c_prv:
                        st.markdown(f"**Previous Plan ({prev_plan.plan_id})**")
                        st.write(f"Total distance: {prev_plan.total_cost:.1f} km | Assignments: {len(prev_plan.assignments)}")
                        for a in prev_plan.assignments:
                            r_str = " -> ".join(a.route.path) if a.route else "None"
                            st.caption(f"• {a.incident_id} ({a.team_id}): {r_str}")
                    with c_cur:
                        diff = round(plan.total_cost - prev_plan.total_cost, 1)
                        diff_str = f"+{diff} km" if diff > 0 else f"{diff} km"
                        st.markdown(f"**Current Plan ({plan.plan_id})**")
                        st.write(f"Total distance: {plan.total_cost:.1f} km ({diff_str}) | Assignments: {len(plan.assignments)}")
                        for a in plan.assignments:
                            r_str = " -> ".join(a.route.path) if a.route else "None"
                            st.caption(f"• {a.incident_id} ({a.team_id}): {r_str}")

    # TAB 2: REQUESTS REGISTRY
    with op_tab2:
        st.markdown("##### All Reported Distress Calls")

        f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 2.0])
        with f_col1:
            st_filter = st.selectbox("Status Filter", ["Active Only", "All", "reported", "assessed", "assigned", "resolved", "cancelled"])
        with f_col2:
            cat_filter = st.selectbox("Animal Species", ["All"] + [c.value.capitalize() for c in AnimalCategory])
        with f_col3:
            search_txt = st.text_input("Search requests", placeholder="e.g. Dog, F-7, injured...")

        all_incidents = sim.incident_service.get_all_incidents()
        if st_filter == "Active Only":
            filtered = [i for i in all_incidents if i.is_active()]
        elif st_filter != "All":
            filtered = [i for i in all_incidents if i.status.value == st_filter]
        else:
            filtered = all_incidents

        if cat_filter != "All":
            filtered = [i for i in filtered if i.animal_category.value.lower() == cat_filter.lower()]

        if search_txt:
            q = search_txt.lower()
            filtered = [i for i in filtered if q in i.title.lower() or q in i.description.lower() or q in i.incident_id.lower()]

        grid_rows = []
        for inc in filtered:
            urgency_labels = {5: "Critical (5/5)", 4: "High (4/5)", 3: "Moderate (3/5)", 2: "Low (2/5)", 1: "Minor (1/5)"}
            grid_rows.append({
                "ID": inc.incident_id,
                "Request Title": inc.title,
                "Animal": inc.animal_category.value.capitalize(),
                "Location": inc.location_id,
                "Urgency": urgency_labels.get(inc.urgency, str(inc.urgency)),
                "Waiting Time": f"{inc.waiting_time:.0f} min",
                "Priority Score": f"{inc.priority_score:.1f}",
                "Status": inc.status.value.upper(),
                "Assigned Team": inc.assigned_team_id or "Awaiting team",
            })
        st.dataframe(pd.DataFrame(grid_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("##### Update Request Status")
        inc_ids = [i.incident_id for i in all_incidents]
        sel_inc_id = st.selectbox("Select Request to Update", inc_ids)
        target_inc = sim.incident_service.get_incident(sel_inc_id)

        if target_inc:
            u_col1, u_col2 = st.columns([1.5, 1.0])
            with u_col1:
                st.markdown(f"**{target_inc.incident_id}: {target_inc.title}**")
                st.caption(f"{target_inc.description} (Location: `{target_inc.location_id}`)")
                bd = target_inc.priority_breakdown
                st.caption(
                    f"Score Breakdown: Urgency {bd.get('urgency_contribution', 0.0):.1f} pts | "
                    f"Waiting Time {bd.get('waiting_contribution', 0.0):.1f} pts | "
                    f"Vulnerability {bd.get('vulnerability_contribution', 0.0):.1f} pts"
                )
            with u_col2:
                new_status = st.selectbox(
                    "Set New Status",
                    [s.value for s in IncidentStatus],
                    index=[s.value for s in IncidentStatus].index(target_inc.status.value),
                )
                if st.button("Save Status Change", use_container_width=True):
                    try:
                        sim.incident_service.update_status(target_inc.incident_id, IncidentStatus(new_status))
                        st.success(f"Status changed to {new_status.upper()}.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # TAB 3: REPORT ANIMAL IN DISTRESS
    with op_tab3:
        st.markdown("##### Log a New Animal Distress Call")
        st.caption("Enter details manually, or paste phone transcripts for automatic structured drafting.")

        form_subtab1, form_subtab2 = st.tabs(["Structured Form Entry", "Draft from Text Transcript"])

        with form_subtab1:
            with st.form("new_request_form", clear_on_submit=True):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    title_in = st.text_input("Request Summary", placeholder="e.g. Injured Dog near F-10 Markaz")
                    cat_in = st.selectbox("Animal Species", [c.value.capitalize() for c in AnimalCategory])
                    nodes_map = sim.routing_service.get_all_nodes()
                    loc_in = st.selectbox("Nearest Road Location", list(nodes_map.keys()))
                with r_col2:
                    urg_in = st.slider("Reported Urgency", 1, 5, 3, help="1: Low discomfort, 5: Immediate life-threat")
                    vuln_in = st.checkbox("Vulnerable animal (trapped, newborn, bad weather)")
                    skills_in = st.multiselect("Special Skills Needed", ALL_SKILLS, default=["veterinary_care"])

                desc_in = st.text_area("Detailed Situation Notes", placeholder="Describe animal condition, exact landmark, caller contact notes...")

                submitted = st.form_submit_button("Register Distress Call", type="primary", use_container_width=True)
                if submitted:
                    if not title_in.strip():
                        st.error("Please enter a request summary.")
                    else:
                        chosen_node = nodes_map[loc_in]
                        new_inc = sim.incident_service.add_incident(
                            title=title_in,
                            description=desc_in,
                            location_id=loc_in,
                            latitude=chosen_node.latitude,
                            longitude=chosen_node.longitude,
                            animal_category=AnimalCategory(cat_in.lower()),
                            urgency=urg_in,
                            is_vulnerable=vuln_in,
                            required_skills=skills_in,
                        )
                        st.success(f"Request {new_inc.incident_id} registered successfully! Priority: {new_inc.priority_score:.1f} pts.")

        with form_subtab2:
            st.caption("Paste an incoming text, caller transcript, or field message to extract structured fields.")
            sample_reports = [
                "A critical dog was hit by a car near F-7 Jinnah Super Market and is bleeding heavily. Needs immediate surgery and transport.",
                "Park rangers at Rawal Lake report an injured pelican trapped in discarded netting on the shore. Needs water rescue gear.",
                "Security guard at I-9 Industrial Zone found a young calf stuck in a concrete drainage ditch. Heavy lifting needed.",
            ]
            c_sample = st.selectbox("Try a sample report", ["-- Pick sample message --"] + sample_reports)
            prefill = c_sample if c_sample != "-- Pick sample message --" else ""

            transcript_input = st.text_area("Caller Message / Transcript", value=prefill, height=90)
            if st.button("Extract Draft Fields"):
                if transcript_input.strip():
                    extracted = sim.parse_natural_language_report(transcript_input)
                    st.session_state["nl_draft_ops"] = extracted
                    st.success("Draft fields extracted! Please review and confirm below.")

            if "nl_draft_ops" in st.session_state:
                draft = st.session_state["nl_draft_ops"]
                st.markdown("###### Review & Confirm Draft")
                d_c1, d_c2 = st.columns(2)
                with d_c1:
                    d_title = st.text_input("Title", value=draft["title"])
                    d_cat = st.selectbox("Species", [c.value.capitalize() for c in AnimalCategory], index=[c.value for c in AnimalCategory].index(draft["animal_category"]))
                    nodes_all = sim.routing_service.get_all_nodes()
                    node_idx = list(nodes_all.keys()).index(draft["suggested_location_id"]) if draft["suggested_location_id"] in nodes_all else 0
                    d_loc = st.selectbox("Location", list(nodes_all.keys()), index=node_idx)
                with d_c2:
                    d_urg = st.slider("Urgency", 1, 5, value=draft["urgency"])
                    d_vuln = st.checkbox("Vulnerable", value=draft["is_vulnerable"])
                    d_skills = st.multiselect("Skills", ALL_SKILLS, default=draft["required_skills"])

                d_notes = st.text_area("Description", value=draft["description"])

                if st.button("Save Draft as Official Request", type="primary"):
                    node_obj = nodes_all[d_loc]
                    inc_res = sim.incident_service.add_incident(
                        title=d_title,
                        description=d_notes,
                        location_id=d_loc,
                        latitude=node_obj.latitude,
                        longitude=node_obj.longitude,
                        animal_category=AnimalCategory(d_cat.lower()),
                        urgency=d_urg,
                        is_vulnerable=d_vuln,
                        required_skills=d_skills,
                    )
                    del st.session_state["nl_draft_ops"]
                    st.success(f"Request {inc_res.incident_id} registered!")
                    st.rerun()

    # TAB 4: FLEET & ROAD CONDITIONS
    with op_tab4:
        col_fl1, col_fl2 = st.columns([1.2, 1.0])
        with col_fl1:
            st.markdown("##### Rescue Teams Roster")
            teams_data = []
            for t in sim.dispatch_service.get_all_teams():
                teams_data.append({
                    "Team Name": t.name,
                    "Base": t.base_location_id,
                    "Current Location": t.current_location_id,
                    "Status": "Available" if t.is_available_for_dispatch() else t.status.value.capitalize(),
                    "Capacity": f"{len(t.current_assignments)}/{t.capacity}",
                    "Specialties": ", ".join(t.skills),
                })
            st.dataframe(pd.DataFrame(teams_data), use_container_width=True, hide_index=True)

        with col_fl2:
            st.markdown("##### Road Conditions & Disruption Controls")
            st.caption("Simulate road closures or congestion to test how the system recalculates detours.")

            all_roads = sim.routing_service.get_all_edges()
            road_opts = [f"{e.start_node} <--> {e.end_node} ({e.road_name})" for e in all_roads]
            selected_road_str = st.selectbox("Select Road Segment", road_opts)
            target_edge = all_roads[road_opts.index(selected_road_str)]

            st.write(f"Status: **{'BLOCKED' if not target_edge.is_open else 'Open'}** | Distance: **{target_edge.cost} km** | Congestion: **{target_edge.congestion_multiplier:.1f}x**")

            r_act1, r_act2 = st.columns(2)
            with r_act1:
                if target_edge.is_open:
                    if st.button("Block This Road", type="primary", use_container_width=True):
                        sim.routing_service.block_road(target_edge.start_node, target_edge.end_node)
                        notes = sim.dispatch_service.replan_disrupted_routes(target_edge.start_node, target_edge.end_node)
                        st.session_state["replan_alerts"] = notes
                        st.toast(f"Road closed between {target_edge.start_node} and {target_edge.end_node}!")
                        st.rerun()
                else:
                    if st.button("Reopen Road", use_container_width=True):
                        sim.routing_service.unblock_road(target_edge.start_node, target_edge.end_node)
                        st.success(f"Road reopened!")
                        st.rerun()

            with r_act2:
                cong_slider = st.slider("Congestion Multiplier", 1.0, 3.5, float(target_edge.congestion_multiplier), step=0.5)
                if st.button("Apply Congestion", use_container_width=True):
                    sim.routing_service.set_congestion(target_edge.start_node, target_edge.end_node, cong_slider)
                    st.success(f"Congestion updated to {cong_slider:.1f}x")
                    st.rerun()

