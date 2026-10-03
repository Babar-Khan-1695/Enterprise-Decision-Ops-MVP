import streamlit as st
from ui.agent_monitor import render_agent_monitor
from ui.scenario_viewer import render_scenario_viewer
from ui.evidence_viewer import render_evidence
from config.agent_config import AGENT_NAMES
from config.settings import OUTPUT_DIR


def render_decision_room(decision_id, title, report, findings, status="Completed", error_message=""):
    st.markdown(f"## Decision Room · {title}")
    st.caption(f"{decision_id} · {status}")

    if status == "Failed":
        st.error("This decision failed during processing.")
        if error_message:
            st.code(error_message, language="text")
        return

    statuses = [{"name": n, "status": "complete"} for n in AGENT_NAMES]
    render_agent_monitor(statuses)

    tabs = st.tabs(["Executive Brief", "Decision Table", "Agent Findings", "Scenarios", "Evidence", "Download"])
    with tabs[0]:
        st.markdown(report or "No executive report is available.")
        st.success("Decision analysis completed. Final business decisions remain under human governance.")
    with tabs[1]:
        rows = []
        for f in findings:
            rows.append({"Agent": f["agent_name"], "Finding": f["finding"]})
        st.dataframe(rows, use_container_width=True, hide_index=True)
    with tabs[2]:
        for f in findings:
            with st.expander(f["agent_name"]):
                st.write(f["finding"])
    with tabs[3]:
        render_scenario_viewer(report)
    with tabs[4]:
        query = st.text_input("Search enterprise evidence", placeholder="e.g. What policy applies to capital expenditure?")
        if st.button("Search Evidence"):
            render_evidence(query)
    with tabs[5]:
        path = OUTPUT_DIR / f"{decision_id}.md"
        data = path.read_bytes() if path.exists() else (report or "").encode("utf-8")
        st.download_button(
            "⬇️ Download Executive Decision Brief",
            data=data,
            file_name=f"{decision_id}_Executive_Decision_Brief.md",
            mime="text/markdown",
            use_container_width=True,
        )
