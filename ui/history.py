import streamlit as st
import pandas as pd
from memory.decision_memory import list_decisions, get_decision
from ui.continuation import render_continue_decision
from ui.report_renderer import render_report_with_tables, render_status_card


def render_history():
    st.markdown("## Decision History")
    rows = list_decisions(100)
    if not rows:
        st.info("No saved decisions.")
        return

    table = pd.DataFrame([
        {
            "Decision ID": r["decision_id"],
            "Decision": r["title"],
            "AI Analysis": r["status"],
            "Executive Status": r["executive_status"] if "executive_status" in r.keys() else "Pending Executive Review",
            "Created": r["created_at"],
        }
        for r in rows
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

    options = {
        f"{r['decision_id']} — {r['title']}": r['decision_id']
        for r in rows
    }
    label = st.selectbox(
        "Open a decision",
        list(options),
        index=None,
        placeholder="Nothing selected",
    )
    if not label:
        return

    row, findings = get_decision(options[label])

    st.markdown(f"### {row['title']}")
    st.caption(f"{row['decision_id']} · AI Analysis: {row['status']}")
    render_status_card(row["executive_status"])

    st.markdown("### Decision Objective")
    st.write(row["objective"])

    if row["error_message"]:
        st.error("Processing error")
        st.code(row["error_message"], language="text")

    if row["report"]:
        st.markdown("### Executive Decision Brief")
        render_report_with_tables(row["report"])

    st.markdown("### Agent Findings")
    for f in findings:
        with st.expander(f["agent_name"], expanded=False):
            st.markdown(f["finding"] or "No finding returned.")

    render_continue_decision(row)
