import streamlit as st
from config.settings import GROQ_MODEL, AGENT_MAX_TOKENS, SYNTHESIZER_MAX_TOKENS, AGENT_DELAY_SECONDS
from rag.vector_store import has_index
from memory.database import DB_PATH


def render_system_health(load_secret):
    st.markdown("## System Health")
    st.caption("Technical readiness and runtime configuration. These details are intentionally kept out of the executive dashboard.")

    groq_ready = bool(load_secret())
    faiss_ready = has_index()
    sqlite_ready = DB_PATH.exists()

    c1, c2, c3 = st.columns(3)
    c1.metric("Groq API", "Ready" if groq_ready else "Missing")
    c2.metric("Knowledge Base", "Ready" if faiss_ready else "Empty")
    c3.metric("Decision Memory", "SQLite" if sqlite_ready else "Initializing")

    st.markdown("### Runtime configuration")
    st.table([
        {"Component": "LLM", "Configuration": GROQ_MODEL},
        {"Component": "Specialist max output", "Configuration": f"{AGENT_MAX_TOKENS} tokens"},
        {"Component": "Synthesizer max output", "Configuration": f"{SYNTHESIZER_MAX_TOKENS} tokens"},
        {"Component": "Agent pacing", "Configuration": f"{AGENT_DELAY_SECONDS} seconds between sequential tasks"},
        {"Component": "Vector store", "Configuration": "FAISS"},
        {"Component": "Memory", "Configuration": "Local SQLite"},
    ])

    if groq_ready:
        st.success("Groq credentials are available to the application.")
    else:
        st.error("GROQ_API_KEY is missing from Streamlit Secrets.")
