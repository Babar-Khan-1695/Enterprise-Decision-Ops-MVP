import streamlit as st
import pandas as pd
from pathlib import Path
from memory.decision_memory import list_decisions, get_decision
from config.settings import OUTPUT_DIR


def _status_icon(status):
    return {
        "Ready for Review": "🟢 Completed",
        "Completed": "🟢 Completed",
        "Analyzing": "🔵 Running",
        "Failed": "🔴 Failed",
    }.get(status, status)


def _report_bytes(row):
    path = OUTPUT_DIR / f"{row['decision_id']}.md"
    if path.exists():
        return path.read_bytes()
    return (row["report"] or "").encode("utf-8")


def render_dashboard():
    rows = list_decisions()
    completed = sum(r["status"] in ("Ready for Review", "Completed") for r in rows)
    running = sum(r["status"] == "Analyzing" for r in rows)
    failed = sum(r["status"] == "Failed" for r in rows)

    st.markdown("## Executive Dashboard")
    st.caption("Review completed enterprise decisions, compare case status and download executive reports.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decision Cases", len(rows))
    c2.metric("Completed", completed)
    c3.metric("Running", running)
    c4.metric("Failed", failed)

    st.markdown("### Decision portfolio")
    if not rows:
        st.info("No decisions yet. Create your first Decision Case from the sidebar.")
        return

    table = pd.DataFrame([
        {
            "Decision ID": r["decision_id"],
            "Decision": r["title"],
            "Status": _status_icon(r["status"]),
            "Created": r["created_at"],
        }
        for r in rows[:30]
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

    options = {f"{r['decision_id']} — {r['title']}": r['decision_id'] for r in rows}
    selected_label = st.selectbox("Select a decision to review", list(options))
    selected_id = options[selected_label]
    row, findings = get_decision(selected_id)

    st.markdown(f"### {row['title']}")
    st.caption(f"{row['decision_id']} · {_status_icon(row['status'])} · {row['created_at']}")

    if row["status"] == "Failed":
        st.error("This decision failed during processing.")
        if row["error_message"]:
            st.code(row["error_message"], language="text")
        return
    if row["status"] == "Analyzing":
        st.info("This decision is still running. Return to New Decision to see live processing for a newly submitted case.")
        return

    tabs = st.tabs(["Executive Brief", "Agent Findings", "Download Report"])
    with tabs[0]:
        st.markdown(row["report"] or "No report was saved.")
    with tabs[1]:
        for f in findings:
            with st.expander(f["agent_name"]):
                st.write(f["finding"])
    with tabs[2]:
        st.markdown("#### Executive report")
        st.download_button(
            "⬇️ Download Executive Decision Brief",
            data=_report_bytes(row),
            file_name=f"{row['decision_id']}_Executive_Decision_Brief.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.caption("The downloadable report is the same executive brief shown above.")

    if st.button("🔎 Open full Decision Room", use_container_width=True):
        st.session_state["selected_decision"] = selected_id
        st.session_state["workspace_page"] = "Decision Room"
        st.rerun()
