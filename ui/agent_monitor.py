import streamlit as st
from config.agent_config import AGENT_NAMES


def render_agent_monitor(statuses=None, compact=False):
    statuses = statuses or [{"name": n, "status": "complete"} for n in AGENT_NAMES]
    st.markdown("### Agent Control Center")
    cols = st.columns(3)
    for i, item in enumerate(statuses):
        status = item.get("status", "pending")
        if status == "complete":
            label, icon = "Complete", "✅"
        elif status == "working":
            label, icon = "Working now", "🔄"
        elif status == "error":
            label, icon = "Error", "❌"
        else:
            label, icon = "Waiting", "⏳"
        with cols[i % 3]:
            st.container(border=True)
            st.markdown(f"**{item['name']} Agent**")
            st.caption(f"{icon} {label}")
