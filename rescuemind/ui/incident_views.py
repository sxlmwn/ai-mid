"""Incident management view: registration, editing, status transitions, and NL intake."""
import pandas as pd
import streamlit as st
from rescuemind.models.incident import IncidentStatus, AnimalCategory
from rescuemind.services.simulation_service import SimulationService
from rescuemind.utils.constants import ALL_SKILLS


def render_incidents_view(sim: SimulationService):
    st.subheader("Incident Registry & Intake Center")
    st.caption("Manage reported animal emergencies, inspect multi-factor priority scores, and log new calls.")

    tab1, tab2, tab3 = st.tabs(["Active Registry", "New Incident Registration", "Natural Language Intake"])

    # TAB 1: REGISTRY & EDITING
    with tab1:
        col_filters1, col_filters2, col_filters3 = st.columns(3)
        with col_filters1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All Active", "All", "reported", "assessed", "assigned", "resolved", "cancelled"],
            )
        with col_filters2:
            category_filter = st.selectbox(
                "Filter by Animal Category",
                ["All"] + [c.value for c in AnimalCategory],
            )
        with col_filters3:
            search_query = st.text_input("Search Title / Description", "")

        incidents = sim.incident_service.get_all_incidents()
        if status_filter == "All Active":
            incidents = [i for i in incidents if i.is_active()]
        elif status_filter != "All":
            incidents = [i for i in incidents if i.status.value == status_filter]

        if category_filter != "All":
            incidents = [i for i in incidents if i.animal_category.value == category_filter]

        if search_query:
            q = search_query.lower()
            incidents = [i for i in incidents if q in i.title.lower() or q in i.description.lower() or q in i.incident_id.lower()]

        # Display table
        table_rows = []
        for inc in incidents:
            table_rows.append({
                "ID": inc.incident_id,
                "Title": inc.title,
                "Animal": inc.animal_category.value.capitalize(),
                "Location": inc.location_id,
                "Urgency": inc.urgency,
                "Priority Score": f"{inc.priority_score:.1f}",
                "Wait (min)": f"{inc.waiting_time:.0f}",
                "Vulnerable": "Yes" if inc.is_vulnerable else "No",
                "Skills Needed": ", ".join(inc.required_skills) if inc.required_skills else "General",
                "Status": inc.status.value.upper(),
                "Assigned Team": inc.assigned_team_id or "Unassigned",
            })

        if table_rows:
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=260)
        else:
            st.info("No incidents match current filter criteria.")

        st.markdown("---")
        st.markdown("##### Incident Inspection & Status Actions")

        all_ids = [i.incident_id for i in sim.incident_service.get_all_incidents()]
        selected_id = st.selectbox("Select Incident to Inspect or Modify", all_ids)
        selected_inc = sim.incident_service.get_incident(selected_id)

        if selected_inc:
            c_info, c_action = st.columns([1.2, 1.0])
            with c_info:
                st.markdown(f"**{selected_inc.incident_id}: {selected_inc.title}**")
                st.write(selected_inc.description)
                st.markdown(
                    f"- **Location Node:** `{selected_inc.location_id}` ({selected_inc.latitude:.4f}, {selected_inc.longitude:.4f})\n"
                    f"- **Animal Category:** `{selected_inc.animal_category.value.capitalize()}`\n"
                    f"- **Current Status:** `{selected_inc.status.value.upper()}`\n"
                    f"- **Assigned Team:** `{selected_inc.assigned_team_id or 'None'}`\n"
                    f"- **Operator Notes:** {selected_inc.operator_notes or 'None'}"
                )

                # Transparent priority breakdown
                bd = selected_inc.priority_breakdown
                st.markdown("###### Multi-Factor Priority Breakdown")
                b1, b2, b3 = st.columns(3)
                b1.metric("Urgency Pts", f"{bd.get('urgency_contribution', 0.0):.1f}")
                b2.metric("Waiting Pts", f"{bd.get('waiting_contribution', 0.0):.1f}")
                b3.metric("Vulnerability Pts", f"{bd.get('vulnerability_contribution', 0.0):.1f}")

            with c_action:
                st.markdown("###### Status Transition")
                target_status = st.selectbox(
                    "Update Status",
                    [s.value for s in IncidentStatus],
                    index=[s.value for s in IncidentStatus].index(selected_inc.status.value),
                )
                action_notes = st.text_input("Operational Note for Log", "")

                if st.button("Apply Status Transition", use_container_width=True):
                    try:
                        sim.incident_service.update_status(
                            selected_inc.incident_id,
                            IncidentStatus(target_status),
                            action_notes,
                        )
                        st.success(f"Incident {selected_inc.incident_id} transitioned to '{target_status}'.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Transition error: {e}")

                st.markdown("###### Edit Urgency & Skills")
                new_urgency = st.slider("Urgency (1 to 5)", 1, 5, selected_inc.urgency)
                new_vuln = st.checkbox("Vulnerability Flag", value=selected_inc.is_vulnerable)
                new_skills = st.multiselect("Required Skills", ALL_SKILLS, default=selected_inc.required_skills)

                if st.button("Save Attribute Changes", use_container_width=True):
                    sim.incident_service.update_incident(
                        selected_inc.incident_id,
                        urgency=new_urgency,
                        is_vulnerable=new_vuln,
                        required_skills=new_skills,
                    )
                    st.success("Incident updated and priority queue recomputed.")
                    st.rerun()

    # TAB 2: MANUAL REGISTRATION
    with tab2:
        st.markdown("##### Manual Incident Entry")
        st.caption("Register a new simulated incident within the Twin Cities metropolitan road network.")

        col_form1, col_form2 = st.columns(2)
        with col_form1:
            new_title = st.text_input("Incident Title", "Injured Stray Dog near Commercial Hub")
            new_desc = st.text_area("Detailed Description", "Distressed animal reported with limb injury, requiring assistance.")
            new_cat = st.selectbox("Animal Category", [c.value for c in AnimalCategory])
            nodes = sim.routing_service.get_all_nodes()
            node_options = list(nodes.keys())
            new_loc_id = st.selectbox("Location Node in Road Network", node_options)
            chosen_node = nodes[new_loc_id]

        with col_form2:
            new_urgency = st.slider("Reported Urgency (1: Low to 5: Life-Threatening)", 1, 5, 3)
            new_vuln = st.checkbox("Vulnerability Flag (e.g. trapped, extreme weather, juvenile)")
            new_skills = st.multiselect("Mandatory Team Skills Required", ALL_SKILLS, default=["veterinary_care"])
            new_notes = st.text_input("Operator Field Notes", "Simulated intake call.")

        if st.button("Register Simulated Incident", type="primary", use_container_width=True):
            try:
                inc = sim.incident_service.add_incident(
                    title=new_title,
                    description=new_desc,
                    location_id=new_loc_id,
                    latitude=chosen_node.latitude,
                    longitude=chosen_node.longitude,
                    animal_category=AnimalCategory(new_cat),
                    urgency=new_urgency,
                    is_vulnerable=new_vuln,
                    required_skills=new_skills,
                    operator_notes=new_notes,
                )
                st.success(f"Registered Incident {inc.incident_id} successfully! Priority Score: {inc.priority_score:.1f} pts.")
                st.rerun()
            except Exception as e:
                st.error(f"Registration validation failed: {e}")

    # TAB 3: OPTIONAL NATURAL LANGUAGE INTAKE
    with tab3:
        st.markdown("##### Natural Language Incident Intake Assistant")
        st.caption(
            "Converts raw written operator reports into a structured draft incident form. "
            "Rule-based, offline, and transparent. The operator MUST review and confirm all fields before saving."
        )

        sample_prompts = [
            "A critical dog was hit by a car near F-7 Jinnah Super Market and is bleeding heavily. Needs immediate surgery and transport.",
            "Park rangers at Rawal Lake report an injured pelican trapped in discarded netting on the shore. Needs water rescue gear.",
            "Security guard at I-9 Industrial Zone found a young calf stuck in a concrete drainage ditch. Heavy lifting needed.",
            "Shopkeeper in Saddar Rawalpindi spotted an aggressive injured cat in an alleyway.",
        ]
        chosen_sample = st.selectbox("Or choose a pre-filled sample report:", ["-- Select Sample --"] + sample_prompts)

        default_text = chosen_sample if chosen_sample != "-- Select Sample --" else ""
        report_text = st.text_area(
            "Raw Operator Incident Dispatch Log / Caller Transcript:",
            value=default_text,
            height=120,
            placeholder="e.g. 'A cat was reported near F-8 Markaz. The caller says it has a broken leg and is stuck in a fence...'",
        )

        if st.button("Extract Structured Fields", type="primary"):
            if not report_text.strip():
                st.warning("Please enter caller report text.")
            else:
                draft = sim.parse_natural_language_report(report_text)
                st.session_state["nl_draft"] = draft
                st.success("Draft fields extracted! Please review and confirm below before registering.")

        if "nl_draft" in st.session_state:
            draft = st.session_state["nl_draft"]
            st.markdown("---")
            st.markdown("###### Operator Review & Confirmation (Human-in-the-Loop)")
            st.info("AI extraction suggestions are populated below. You can adjust any field before submitting.")

            ec1, ec2 = st.columns(2)
            with ec1:
                c_title = st.text_input("Extracted Title", value=draft["title"])
                c_desc = st.text_area("Extracted Description", value=draft["description"])
                c_cat = st.selectbox(
                    "Extracted Animal Category",
                    [c.value for c in AnimalCategory],
                    index=[c.value for c in AnimalCategory].index(draft["animal_category"]),
                )
                nodes = sim.routing_service.get_all_nodes()
                default_idx = list(nodes.keys()).index(draft["suggested_location_id"]) if draft["suggested_location_id"] in nodes else 0
                c_loc = st.selectbox("Assigned Graph Node", list(nodes.keys()), index=default_idx)

            with ec2:
                c_urgency = st.slider("Extracted Urgency (1 to 5)", 1, 5, value=draft["urgency"])
                c_vuln = st.checkbox("Vulnerability Flag", value=draft["is_vulnerable"])
                c_skills = st.multiselect("Mandatory Skills", ALL_SKILLS, default=draft["required_skills"])

            if st.button("Confirm & Register Incident into System", type="primary", use_container_width=True):
                target_node = nodes[c_loc]
                inc = sim.incident_service.add_incident(
                    title=c_title,
                    description=c_desc,
                    location_id=c_loc,
                    latitude=target_node.latitude,
                    longitude=target_node.longitude,
                    animal_category=AnimalCategory(c_cat),
                    urgency=c_urgency,
                    is_vulnerable=c_vuln,
                    required_skills=c_skills,
                    operator_notes="Extracted via Natural Language Intake Assistant, operator verified.",
                )
                del st.session_state["nl_draft"]
                st.success(f"Incident {inc.incident_id} successfully registered from transcript!")
                st.rerun()
