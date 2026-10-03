import streamlit as st
from ui.agent_monitor import render_agent_monitor
from ui.scenario_viewer import render_scenario_viewer
from ui.evidence_viewer import render_evidence
from config.agent_config import AGENT_NAMES
from config.settings import OUTPUT_DIR
from memory.database import update_decision_status, list_sources
from ui.continuation import render_continue_decision


def render_decision_room(decision_id, title, report, findings, status="Completed", error_message="", row=None):
    st.markdown(f"## Decision Room · {title}")
    executive_status = row["executive_status"] if row is not None and "executive_status" in row.keys() else "Pending Executive Review"
    st.caption(f"{decision_id} · AI Analysis: {status} · Executive Status: {executive_status}")

    if status == "Failed":
        st.error("This decision failed during AI analysis.")
        if error_message:
            st.code(error_message, language="text")
        return

    render_agent_monitor([{"name": n, "status": "complete"} for n in AGENT_NAMES])
    tabs = st.tabs([
        "Executive Brief", "Decision Table", "Agent Findings", "Scenarios",
        "Evidence", "Sources & Evidence", "Continue Decision", "Download"
    ])
    with tabs[0]:
        st.markdown(report or "No executive report is available.")
        st.markdown("### Executive Decision Status")
        st.info(f"Current status: **{executive_status}**")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⏳ Pending Review", key=f"pending_room_{decision_id}", use_container_width=True):
                update_decision_status(decision_id, executive_status="Pending Executive Review")
                st.rerun()
        with c2:
            if st.button("✅ Approve Decision", key=f"approve_room_{decision_id}", use_container_width=True):
                update_decision_status(decision_id, executive_status="Approved by Executive")
                st.rerun()
        with c3:
            if st.button("❌ Reject Decision", key=f"reject_room_{decision_id}", use_container_width=True):
                update_decision_status(decision_id, executive_status="Rejected by Executive")
                st.rerun()
    with tabs[1]:
        data = [{"Agent": f["agent_name"], "Finding": f["finding"] or "No finding returned."} for f in findings]
        if not data:
            st.warning("No individual findings were saved for this decision.")
        else:
            st.dataframe(data, use_container_width=True, hide_index=True)
    with tabs[2]:
        if not findings:
            st.warning("No individual findings were saved for this decision.")
        for f in findings:
            with st.expander(f["agent_name"], expanded=False):
                st.write(f["finding"] or "No finding returned.")
    with tabs[3]:
        render_scenario_viewer(report)
    with tabs[4]:
        query = st.text_input(
            "Search enterprise evidence",
            placeholder="e.g. What policy applies to capital expenditure?",
            key=f"evidence_q_{decision_id}"
        )
        if st.button("Search Evidence", key=f"search_e_{decision_id}"):
            render_evidence(query)
    with tabs[5]:
        sources = list_sources(decision_id)
        if not sources:
            st.info("No source records were saved.")
        for s in sources:
            st.markdown(f"**{s['source_name']}** · {s['source_type']}")
            if s["url"]:
                st.write(s["url"])
            if s["accessed_at"]:
                st.caption(f"Accessed: {s['accessed_at']}")
            if s["details"]:
                st.caption(s["details"])
    with tabs[6]:
        if row is not None:
            render_continue_decision(row)
    with tabs[7]:
        path = OUTPUT_DIR / f"{decision_id}.md"
        data = path.read_bytes() if path.exists() else (report or "").encode("utf-8")
        st.download_button(
            "⬇️ Download Executive Decision Brief",
            data=data,
            file_name=f"{decision_id}_Executive_Decision_Brief.md",
            mime="text/markdown", use_container_width=True,
        )
