import streamlit as st
import pandas as pd
from memory.decision_memory import list_decisions, get_decision, update_decision_status
from config.settings import OUTPUT_DIR
from ui.continuation import render_continue_decision


def _ai_status(status):
    return {
        "Completed": "🟢 Analysis Completed",
        "Analyzing": "🔵 Analysis In Progress",
        "Failed": "🔴 Analysis Failed",
    }.get(status, status)


def _exec_status(row):
    return row["executive_status"] if "executive_status" in row.keys() else "Pending Executive Review"


def _report_bytes(row):
    path = OUTPUT_DIR / f"{row['decision_id']}.md"
    return path.read_bytes() if path.exists() else (row["report"] or "").encode("utf-8")


def render_dashboard():
    rows = list_decisions()
    completed = sum(r["status"] == "Completed" for r in rows)
    running = sum(r["status"] == "Analyzing" for r in rows)
    failed = sum(r["status"] == "Failed" for r in rows)
    pending = sum(_exec_status(r) == "Pending Executive Review" and r["status"] == "Completed" for r in rows)
    approved = sum(_exec_status(r) == "Approved by Executive" for r in rows)
    rejected = sum(_exec_status(r) == "Rejected by Executive" for r in rows)

    st.markdown("## Executive Dashboard")
    st.caption("Decision portfolio and executive review.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decision Cases", len(rows))
    c2.metric("Analysis Completed", completed)
    c3.metric("Pending Review", pending)
    c4.metric("Approved", approved)

    st.markdown("### Decision Portfolio")
    if not rows:
        st.info("No decisions yet. Create your first Decision Case from New Decision.")
        return

    table = pd.DataFrame([
        {
            "Decision ID": r["decision_id"],
            "Decision": r["title"],
            "AI Analysis": _ai_status(r["status"]),
            "Executive Status": _exec_status(r),
            "Created": r["created_at"],
        } for r in rows[:30]
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

    labels = [f"{r['decision_id']} — {r['title']}" for r in rows]
    mapping = {f"{r['decision_id']} — {r['title']}": r['decision_id'] for r in rows}
    selected_label = st.selectbox(
        "Select a decision to review", labels, index=None, placeholder="Nothing selected"
    )
    if not selected_label:
        st.caption("Select a decision to review to access its report or executive status actions.")
        return

    selected_id = mapping[selected_label]
    row, findings = get_decision(selected_id)

    action = st.radio(
        "What would you like to do?",
        ["Review / Search Decision", "Change Executive Decision Status"],
        horizontal=True,
        key=f"dashboard_action_{selected_id}",
    )

    if action == "Change Executive Decision Status":
        current = _exec_status(row)
        st.info(f"Current Executive Status: **{current}**")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⏳ Keep Pending Review", key=f"pending_{selected_id}", use_container_width=True):
                update_decision_status(selected_id, executive_status="Pending Executive Review")
                st.rerun()
        with c2:
            if st.button("✅ Approve Decision", key=f"approve_{selected_id}", use_container_width=True):
                update_decision_status(selected_id, executive_status="Approved by Executive")
                st.rerun()
        with c3:
            if st.button("❌ Reject Decision", key=f"reject_{selected_id}", use_container_width=True):
                update_decision_status(selected_id, executive_status="Rejected by Executive")
                st.rerun()
        return

    if row["status"] == "Failed":
        st.error("This decision failed during AI analysis.")
        if row["error_message"]:
            st.code(row["error_message"], language="text")
        return
    if row["status"] == "Analyzing":
        st.info("This decision is still being analyzed.")
        return

    st.markdown(f"### {row['title']}")
    st.caption(f"{row['decision_id']} · AI Analysis: {_ai_status(row['status'])} · Executive: {_exec_status(row)}")
    tabs = st.tabs(["Executive Brief", "Agent Findings", "Continue Decision", "Download Report"])
    with tabs[0]:
        st.markdown(row["report"] or "No report was saved.")
    with tabs[1]:
        if not findings:
            st.warning("No individual findings were saved.")
        for f in findings:
            with st.expander(f["agent_name"], expanded=False):
                st.write(f["finding"] or "No finding returned.")
    with tabs[2]:
        render_continue_decision(row)
    with tabs[3]:
        st.download_button(
            "⬇️ Download Executive Decision Brief",
            data=_report_bytes(row),
            file_name=f"{row['decision_id']}_Executive_Decision_Brief.md",
            mime="text/markdown", use_container_width=True,
        )
    if st.button("🔎 Open full Decision Room", key=f"room_{selected_id}", use_container_width=True):
        st.session_state["selected_decision"] = selected_id
        st.session_state["workspace_page"] = "Decision Room"
        st.rerun()
