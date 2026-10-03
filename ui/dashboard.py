import streamlit as st
from memory.decision_memory import list_decisions


def render_dashboard():
    rows = list_decisions()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decision Cases", len(rows))
    c2.metric("Awaiting Review", sum(r["status"] == "Ready for Review" for r in rows))
    c3.metric("Completed", sum(r["status"] == "Completed" for r in rows))
    c4.metric("Knowledge Base", "Active" if st.session_state.get("knowledge_ready") else "Empty")

    st.markdown("### Recent decision cases")
    if not rows:
        st.info("No decisions yet. Create your first Decision Case from the sidebar.")
        return
    for row in rows[:8]:
        with st.container(border=True):
            a, b, c = st.columns([4, 2, 1])
            a.markdown(f"**{row['title']}**")
            a.caption(f"{row['decision_id']} · {row['created_at']}")
            b.write(row["status"])
            if c.button("Open", key=f"open_{row['decision_id']}"):
                st.session_state["selected_decision"] = row["decision_id"]
                st.rerun()
