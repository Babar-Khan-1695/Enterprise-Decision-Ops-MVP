import streamlit as st
from config.settings import (
    GROQ_MODEL,
    AGENT_MAX_TOKENS,
    SYNTHESIZER_MAX_TOKENS,
    AGENT_DELAY_SECONDS,
    GROQ_REASONING_EFFORT,
    UPLOAD_DIR,
)
from rag.vector_store import get_index_stats
from memory.database import DB_PATH, list_decisions


def render_system_health(load_secret):
    st.markdown("## System Health")
    st.caption("Technical readiness and runtime configuration.")

    groq_ready = bool(load_secret())
    kb = get_index_stats()
    sqlite_ready = DB_PATH.exists()
    rows = list_decisions(100)

    uploaded_pdfs = list(UPLOAD_DIR.glob("*.pdf")) if UPLOAD_DIR.exists() else []

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Groq API",
        "Connected" if groq_ready else "Missing",
    )

    if kb["ready"]:
        kb_label = f"Ready · {kb['documents']} doc{'s' if kb['documents'] != 1 else ''}"
    elif uploaded_pdfs:
        kb_label = f"Needs indexing · {len(uploaded_pdfs)} PDF"
    else:
        kb_label = "No documents"

    c2.metric("Knowledge Base", kb_label)

    c3.metric(
        "Decision Memory",
        "SQLite Ready" if sqlite_ready else "Initializing",
    )

    c4.metric(
        "Agent Runtime",
        "Operational",
    )

    # --------------------------------------------------------
    # Knowledge Base detail
    # --------------------------------------------------------

    st.markdown("### Knowledge Base")

    kb1, kb2, kb3 = st.columns(3)
    kb1.metric("Indexed Documents", kb["documents"])
    kb2.metric("Indexed Chunks", kb["chunks"])
    kb3.metric("Uploaded PDFs", len(uploaded_pdfs))

    if kb["ready"]:
        st.success(
            f"Knowledge base is ready. "
            f"{kb['documents']} document(s) and {kb['chunks']} indexed chunk(s) are available for RAG retrieval."
        )
    elif uploaded_pdfs:
        st.warning(
            "PDF evidence exists in the upload directory, but no usable FAISS index is currently available."
        )
    else:
        st.info(
            "No enterprise PDF evidence has been indexed yet. "
            "Upload a PDF from New Decision to populate the RAG knowledge base."
        )

    st.markdown("### Runtime Configuration")
    st.table([
        {"Component": "LLM", "Configuration": GROQ_MODEL},
        {"Component": "Reasoning effort", "Configuration": GROQ_REASONING_EFFORT},
        {"Component": "Specialist max output", "Configuration": f"{AGENT_MAX_TOKENS} tokens"},
        {"Component": "Synthesizer max output", "Configuration": f"{SYNTHESIZER_MAX_TOKENS} tokens"},
        {"Component": "Agent pacing", "Configuration": f"{AGENT_DELAY_SECONDS} seconds"},
        {"Component": "Vector store", "Configuration": "FAISS"},
        {"Component": "Memory", "Configuration": "Local SQLite"},
        {"Component": "Saved decisions", "Configuration": str(len(rows))},
    ])

    if groq_ready:
        st.success("Groq credentials are available to the application.")
    else:
        st.error("GROQ_API_KEY is missing from Streamlit Secrets.")
