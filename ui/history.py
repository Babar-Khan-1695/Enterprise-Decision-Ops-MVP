import streamlit as st
import pandas as pd
from memory.decision_memory import list_decisions, get_decision


def render_history():
    st.markdown("## Decision History")
    rows = list_decisions(100)
    if not rows:
        st.info("No saved decisions.")
        return

    table = pd.DataFrame([
        {"Decision ID": r["decision_id"], "Decision": r["title"], "Status": r["status"], "Created": r["created_at"]}
        for r in rows
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

    options = {f"{r['decision_id']} — {r['title']}": r['decision_id'] for r in rows}
    label = st.selectbox("Open a decision", list(options))
    row, findings = get_decision(options[label])
    st.markdown(f"### {row['title']}")
    st.caption(f"{row['decision_id']} · {row['created_at']} · {row['status']}")
    st.write(row['objective'])
    if row['error_message']:
        st.error("Processing error")
        st.code(row['error_message'], language="text")
    if row['report']:
        st.markdown("### Executive Decision Brief")
        st.markdown(row['report'])
    with st.expander("Agent findings"):
        for f in findings:
            st.markdown(f"**{f['agent_name']}**")
            st.write(f['finding'])
