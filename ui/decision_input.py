import streamlit as st
from config.settings import UPLOAD_DIR
from rag.document_loader import load_uploaded_documents
from rag.vector_store import build_index
from utils.validators import validate_decision


def render_input():
    st.markdown("## Create a Decision Case")
    with st.form("decision_form"):
        title = st.text_input("Decision title", placeholder="e.g. Lahore Distribution Center Expansion")
        objective = st.text_area("Business decision / objective", height=130, placeholder="What decision does management need to make, and why?")
        decision_type = st.selectbox("Decision type", ["Investment", "Expansion", "Vendor Selection", "Market Entry", "Product Launch", "Make vs Buy", "Cost Reduction", "Technology", "Other"])
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
                st.success(f"Indexed {len(docs)} document chunks into FAISS.")
        st.session_state["pending_decision"] = {
            "title": title,
            "objective": objective,
            "decision_type": decision_type,
            "constraints": constraints,
        }
        st.session_state["run_analysis"] = True
        st.rerun()
