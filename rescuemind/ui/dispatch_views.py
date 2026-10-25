"""Dispatch Center view: multi-incident coordination, CSP solver, B&B optimization, and replan diffs."""
import pandas as pd
import streamlit as st
from rescuemind.services.simulation_service import SimulationService


def render_dispatch_view(sim: SimulationService):
    st.subheader("Autonomous Dispatch Intelligence & Coordination")
    st.caption("Coordinate prioritized emergency response missions using CSP constraint satisfaction and Branch-and-Bound optimization.")

    # Control Bar
    with st.container():
        c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4 = st.columns([1.2, 1.2, 1.2, 1.4])
        with c_ctrl1:
            algorithm_mode = st.radio(
                "Dispatch Engine",
                ["CSP Backtracking (MRV + Forward Check)", "Branch-and-Bound (Cost Optimal)"],
                help="CSP finds a constraint-satisfying assignment. Branch-and-Bound optimizes global travel cost.",
            )
        with c_ctrl2:
            routing_choice = st.selectbox(
                "Routing Algorithm",
                ["A*", "UCS (Uniform Cost)", "BFS (Fewest Hops)", "Greedy Best-First"],
                help="Algorithm used to compute travel routes for dispatched teams.",
            )
        with c_ctrl3:
            horizon = st.slider(
                "Planning Horizon (Incidents)",
                min_value=1,
                max_value=10,
                value=sim.dispatch_service.planning_horizon,
                help="Batch size of highest-priority incidents evaluated in each coordination cycle.",
            )
            sim.dispatch_service.planning_horizon = horizon
        with c_ctrl4:
            st.write("")
            st.write("")
            use_opt = "Branch-and-Bound" in algorithm_mode
            if st.button("Generate Dispatch Plan", type="primary", use_container_width=True):
                plan = sim.dispatch_service.run_dispatch_cycle(
                    use_optimization=use_opt,
                    routing_algo=routing_choice,
                )
                st.success(f"Plan {plan.plan_id} generated successfully!")
                st.rerun()

    st.markdown("---")

    plan = sim.dispatch_service.current_plan

    if not plan:
        st.info("No dispatch plan generated yet. Click 'Generate Dispatch Plan' to execute the coordination cycle.")
        return

    # Plan Summary Header
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Plan ID", plan.plan_id)
    p2.metric("Teams Dispatched", len(plan.assignments))
    p3.metric("Unassigned Cases", len(plan.unassigned_incidents))
    p4.metric("Total Travel Cost", f"{plan.total_cost:.1f} km")

    tabs = st.tabs(["Active Dispatches & Routes", "Unassigned Analysis", "Hard Constraint Auditing", "Before-and-After Replan Comparison"])

    # TAB 1: ACTIVE DISPATCHES
    with tabs[0]:
        st.markdown("##### Assigned Response Missions")
        if not plan.assignments:
            st.warning("No incidents could be assigned under current constraints and team availability.")
        else:
            rows = []
            for a in plan.assignments:
                inc = sim.incident_service.get_incident(a.incident_id)
                team = sim.dispatch_service.get_team(a.team_id)
                route = a.route
                rows.append({
                    "Incident ID": a.incident_id,
                    "Title": inc.title if inc else "Unknown",
                    "Assigned Team": team.name if team else a.team_id,
                    "From Node": team.current_location_id if team else "N/A",
                    "To Node": inc.location_id if inc else "N/A",
                    "Optimal Route": " -> ".join(route.path) if route and route.success else "Failed",
                    "Cost (km)": f"{route.cost:.1f}" if route else "N/A",
                    "Est. Time": f"{route.travel_time:.1f} min" if route else "N/A",
                    "Hops": route.edge_count if route else 0,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.markdown("##### Operational Explanations & Decision Rationale")
        for expl in plan.explanations:
            st.markdown(f"- {expl}")

    # TAB 2: UNASSIGNED CASES
    with tabs[1]:
        st.markdown("##### Unassigned Incidents in Planning Batch")
        st.caption("Transparent reporting of cases awaiting resources and the exact constraint reason.")

        if not plan.unassigned_incidents:
            st.success("All evaluated incidents in the current planning window have been assigned to teams!")
        else:
            unassigned_rows = []
            for inc_id, reason in plan.unassigned_incidents.items():
                inc = sim.incident_service.get_incident(inc_id)
                unassigned_rows.append({
                    "Incident ID": inc_id,
                    "Title": inc.title if inc else "Unknown",
                    "Priority Score": f"{inc.priority_score:.1f}" if inc else "N/A",
                    "Urgency": f"{inc.urgency}/5" if inc else "N/A",
                    "Skills Required": ", ".join(inc.required_skills) if inc and inc.required_skills else "General",
                    "Bottleneck / Rejection Reason": reason,
                })
            st.dataframe(pd.DataFrame(unassigned_rows), use_container_width=True)

    # TAB 3: CONSTRAINT AUDITING
    with tabs[2]:
        st.markdown("##### CSP Operational Constraints Audited")
        st.markdown("""
        Every candidate team evaluation is validated against six deterministic hard constraints:
        1. **Team Availability:** Team status must be available and current active assignments < capacity.
        2. **Skill Coverage:** Team must possess all mandatory skills required by the emergency call.
        3. **Category Support:** Team profile must explicitly support the animal species category.
        4. **Capacity Threshold:** Dispatches cannot exceed simultaneous vehicle capacity.
        5. **Incident Exclusivity:** An incident can be assigned to at most one rescue team.
        6. **Graph Reachability:** An open, unblocked route must connect the team location to the incident.
        """)

        st.markdown("###### Candidate Team Rejections Log")
        # Extract candidate rejections from CSP
        active = sim.incident_service.get_active_incidents()[:sim.dispatch_service.planning_horizon]
        from rescuemind.algorithms.assignment import RescueTeamCSP
        csp_auditor = RescueTeamCSP(active, sim.dispatch_service.get_all_teams(), sim.routing_service.graph)
        csp_auditor.solve([i.incident_id for i in active])

        if csp_auditor.rejections:
            rej_data = []
            for r in csp_auditor.rejections[:20]:
                rej_data.append({
                    "Incident ID": r.incident_id,
                    "Team ID": r.team_id,
                    "Failed Constraint": r.failed_constraint,
                    "Diagnostic Explanation": r.explanation,
                })
            st.dataframe(pd.DataFrame(rej_data), use_container_width=True, height=260)
        else:
            st.info("No candidates rejected during this planning cycle.")

    # TAB 4: REPLAN COMPARISON
    with tabs[3]:
        st.markdown("##### Before-and-After Plan Comparison")
        st.caption("Inspect changes between consecutive dispatch cycles or following simulated road network disruptions.")

        prev_plan = sim.dispatch_service.previous_plan
        curr_plan = sim.dispatch_service.current_plan

        if not prev_plan:
            st.info("No previous plan stored yet. Trigger another dispatch cycle or simulate a disruption to inspect differences.")
        else:
            c_prev, c_curr = st.columns(2)
            with c_prev:
                st.markdown(f"###### Previous Plan ({prev_plan.plan_id})")
                st.metric("Previous Cost", f"{prev_plan.total_cost:.1f} km")
                st.write(f"**Dispatched Missions:** {len(prev_plan.assignments)}")
                prev_routes = {a.incident_id: " -> ".join(a.route.path) if a.route else "None" for a in prev_plan.assignments}
                for inc_id, p in prev_routes.items():
                    st.text(f"{inc_id}: {p}")

            with c_curr:
                st.markdown(f"###### Current Plan ({curr_plan.plan_id})")
                cost_diff = round(curr_plan.total_cost - prev_plan.total_cost, 2)
                st.metric("Current Cost", f"{curr_plan.total_cost:.1f} km", delta=f"{cost_diff:+.1f} km", delta_color="inverse")
                st.write(f"**Dispatched Missions:** {len(curr_plan.assignments)}")
                curr_routes = {a.incident_id: " -> ".join(a.route.path) if a.route else "None" for a in curr_plan.assignments}
                for inc_id, p in curr_routes.items():
                    st.text(f"{inc_id}: {p}")
