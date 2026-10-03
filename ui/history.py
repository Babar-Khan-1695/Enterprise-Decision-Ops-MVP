import streamlit as st
from memory.decision_memory import list_decisions, get_decision


def render_history():
    st.markdown("## Decision History")
    rows = list_decisions(100)
    if not rows:
        st.info("No saved decisions.")
        return
    options = {f"{r['decision_id']} — {r['title']}": r['decision_id'] for r in rows}
    label = st.selectbox("Select a decision", list(options))
    row, findings = get_decision(options[label])
    st.markdown(f"### {row['title']}")
    st.caption(f"{row['decision_id']} · {row['created_at']} · {row['status']}")
    st.write(row['objective'])
    if row['report']:
        st.markdown("### Executive Decision Brief")
        st.markdown(row['report'])
    with st.expander("Agent findings"):
        for f in findings:
            st.markdown(f"**{f['agent_name']}**")
            st.write(f['finding'])
