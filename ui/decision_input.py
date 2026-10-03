import streamlit as st
from config.settings import UPLOAD_DIR
from rag.document_loader import load_uploaded_documents
from rag.vector_store import build_index
from utils.validators import validate_decision
from ui.agent_monitor import render_agent_monitor
from config.agent_config import AGENT_NAMES


def _status_badge(status):
    if status == "Completed":
        st.success("✅ Decision analysis completed")
    elif status == "Failed":
        st.error("❌ Decision analysis failed")
    elif status == "Analyzing":
        st.info("🔄 Decision analysis is running")


def render_input():
    st.markdown("## Create a Decision Case")
    st.caption("Submit a business decision and watch the specialist agents work through it sequentially.")

    with st.form("decision_form"):
        title = st.text_input("Decision title", placeholder="e.g. Lahore Distribution Center Expansion")
        objective = st.text_area("Business decision / objective", height=130, placeholder="What decision does management need to make, and why?")
        decision_type = st.selectbox("Decision type", ["Investment", "Expansion", "Vendor Selection", "Supplier Selection", "Market Entry", "Product Launch", "Make vs Buy", "Cost Reduction", "Technology", "Other"])
        constraints = st.text_area("Constraints and known facts", height=100, placeholder="Budget, deadline, minimum ROI, strategic constraints, etc.")
        files = st.file_uploader("Upload enterprise evidence (PDF)", type=["pdf"], accept_multiple_files=True)
        submitted = st.form_submit_button("🚀 Start Decision Analysis", use_container_width=True)

    if submitted:
        errors = validate_decision(title, objective)
        if errors:
            for error in errors:
                st.error(error)
            return
        saved_paths = []
        for file in files or []:
            path = UPLOAD_DIR / file.name
            path.write_bytes(file.getbuffer())
            saved_paths.append(path)
        if saved_paths:
            docs = load_uploaded_documents(saved_paths)
            if docs:
                build_index(docs)
                st.session_state["knowledge_ready"] = True
                st.success(f"Indexed {len(docs)} document chunks into the enterprise knowledge base.")
        st.session_state["pending_decision"] = {
            "title": title,
            "objective": objective,
            "decision_type": decision_type,
            "constraints": constraints,
        }
        st.session_state["run_analysis"] = True
        st.session_state["analysis_status"] = "Analyzing"
        st.session_state["agent_statuses"] = [{"name": n, "status": "pending"} for n in AGENT_NAMES]
        st.rerun()


def render_analysis_panel():
    status = st.session_state.get("analysis_status")
    decision_id = st.session_state.get("active_decision_id")
    if not status or not decision_id:
        return

    st.divider()
    st.markdown(f"### Decision Processing · `{decision_id}`")
    _status_badge(status)

    if status == "Analyzing":
        st.caption("Agents run sequentially with pacing to protect the Groq token-per-minute limit.")
    elif status == "Completed":
        st.success("Your Executive Decision Brief has been created and saved.")
        st.info("Go to **Executive Dashboard** to review the decision, inspect evidence and download the report.")
        if st.button("📊 Go to Executive Dashboard", key="goto_dashboard", use_container_width=True):
            st.session_state["workspace_page"] = "Executive Dashboard"
            st.rerun()
    elif status == "Failed":
        error = st.session_state.get("analysis_error", "Unknown error")
        st.error("The decision could not be completed.")
        st.code(error, language="text")
        if "rate limit" in error.lower() or "ratelimit" in error.lower() or "tokens per minute" in error.lower():
            st.warning("Groq token rate limit was reached. The workflow is intentionally paced, but this run still exceeded the account's current TPM allowance. Wait for the limit window to reset before retrying.")

    statuses = st.session_state.get("agent_statuses")
    if statuses:
        render_agent_monitor(statuses)
