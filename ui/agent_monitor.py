import streamlit as st

AGENTS = [
    "Orchestrator", "Research", "Finance", "Operations", "Risk",
    "Compliance", "Scenario", "Devil's Advocate", "Decision Synthesizer"
]


def render_agent_monitor(completed=True):
    st.markdown("### Agent Control Center")
    cols = st.columns(3)
    for i, name in enumerate(AGENTS):
        status = "● Complete" if completed else "○ Pending"
        with cols[i % 3]:
            st.container(border=True)
            st.markdown(f"**{name} Agent**")
            st.caption(status)
