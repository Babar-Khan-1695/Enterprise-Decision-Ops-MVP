import streamlit as st
from config.settings import GROQ_MODEL, AGENT_MAX_TOKENS, SYNTHESIZER_MAX_TOKENS, AGENT_DELAY_SECONDS, GROQ_REASONING_EFFORT
from rag.vector_store import has_index
from memory.database import DB_PATH, list_decisions


def render_system_health(load_secret):
    st.markdown("## System Health")
    st.caption("Technical readiness and runtime configuration.")

    groq_ready = bool(load_secret())
    faiss_ready = has_index()
    sqlite_ready = DB_PATH.exists()
    rows = list_decisions(100)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Groq API", "Connected" if groq_ready else "Missing")
    c2.metric("Knowledge Base", "Ready" if faiss_ready else "Empty")
    c3.metric("Decision Memory", "SQLite Ready" if sqlite_ready else "Initializing")
    c4.metric("Agent Runtime", "Operational")

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
