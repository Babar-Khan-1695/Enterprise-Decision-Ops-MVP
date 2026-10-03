import streamlit as st
from ui.agent_monitor import render_agent_monitor
from ui.scenario_viewer import render_scenario_viewer
from ui.evidence_viewer import render_evidence


def render_decision_room(decision_id, title, report, findings):
    st.markdown(f"## Decision Room · {title}")
    st.caption(decision_id)
    render_agent_monitor(True)

    tabs = st.tabs(["Executive Brief", "Agent Findings", "Scenarios", "Evidence"])
    with tabs[0]:
        st.markdown(report)
        st.success("Decision analysis completed. Final business decisions remain under human governance.")
    with tabs[1]:
        for f in findings:
            with st.expander(f["agent_name"]):
                st.write(f["finding"])
    with tabs[2]:
        render_scenario_viewer(report)
    with tabs[3]:
        query = st.text_input("Search enterprise evidence", placeholder="e.g. What policy applies to capital expenditure?")
        if st.button("Search Evidence"):
            render_evidence(query)
