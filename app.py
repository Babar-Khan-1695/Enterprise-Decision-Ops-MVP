import os
import streamlit as st

from config.settings import OUTPUT_DIR
from utils.helpers import now_iso
from tools.decision_tools import new_decision_id
from memory.database import init_db, save_decision, save_finding, get_decision
from memory.decision_memory import list_decisions
from rag.vector_store import has_index
from rag.retriever import retrieve_context
from crews.decision_crew import run_decision
from ui.dashboard import render_dashboard
from ui.decision_input import render_input
from ui.decision_room import render_decision_room
from ui.history import render_history

st.set_page_config(page_title="Enterprise DecisionOps", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
init_db()


def load_secret():
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        return ""


if load_secret():
    os.environ["GROQ_API_KEY"] = load_secret()

st.markdown("""
<style>
:root { --ink:#122033; --muted:#64748b; --line:#e2e8f0; --accent:#2563eb; --soft:#f8fafc; }
.block-container { padding-top: 1.5rem; max-width: 1400px; }
.hero { padding: 1.6rem 1.8rem; border:1px solid #dbeafe; border-radius:22px; background:linear-gradient(135deg,#eff6ff,#ffffff 60%,#f8fafc); margin-bottom:1.2rem; }
.hero h1 { margin:0; color:var(--ink); font-size:2.2rem; letter-spacing:-.03em; }
.hero p { color:var(--muted); margin:.45rem 0 0; font-size:1.03rem; }
[data-testid="stMetric"] { border:1px solid var(--line); padding:12px; border-radius:14px; background:white; }
[data-testid="stSidebar"] { border-right:1px solid var(--line); }
.stButton button { border-radius:10px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>◈ Enterprise DecisionOps</h1>
<p>A governed multi-agent decision intelligence workspace for complex enterprise decisions.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## DecisionOps")
    st.caption("Multi-agent enterprise decision intelligence")
    st.divider()
    page = st.radio("Workspace", ["Executive Dashboard", "New Decision", "Decision Room", "Decision History"], index=0)
    st.divider()
    st.markdown("**System status**")
    st.success("Groq API ready" if load_secret() else "Groq API key missing")
    st.info("FAISS knowledge base ready" if has_index() else "FAISS knowledge base empty")
    st.caption("MVP memory: local SQLite")

if not load_secret():
    st.warning("Add `GROQ_API_KEY` to Streamlit Secrets before running an analysis.")

if page == "Executive Dashboard":
    render_dashboard()

elif page == "New Decision":
    render_input()

elif page == "Decision History":
    render_history()

elif page == "Decision Room":
    selected = st.session_state.get("selected_decision")
    if not selected:
        rows = list_decisions()
        if rows:
            options = {f"{r['decision_id']} — {r['title']}": r['decision_id'] for r in rows}
            selected = options[st.selectbox("Open decision", list(options))]
        else:
            st.info("Create a decision first.")
    if selected:
        row, findings = get_decision(selected)
        render_decision_room(row["decision_id"], row["title"], row["report"], findings)

if st.session_state.get("run_analysis") and page == "Executive Dashboard":
    st.session_state["run_analysis"] = False
    decision = st.session_state.pop("pending_decision", None)
    if decision:
        decision_id = new_decision_id()
        created = now_iso()
        save_decision(decision_id, decision["title"], decision["objective"], "Analyzing", created)
        st.markdown("---")
        st.markdown(f"### Running Decision Case `{decision_id}`")
        progress = st.progress(0, text="Preparing enterprise decision workflow…")
        try:
            evidence = retrieve_context(decision["objective"], 6)
            progress.progress(20, text="Preparing evidence and specialist agents…")
            report, outputs = run_decision(decision, evidence)
            progress.progress(90, text="Saving decision memory…")
            agent_names = ["Orchestrator", "Research", "Finance", "Operations", "Risk", "Compliance", "Scenario", "Devil's Advocate", "Decision Synthesizer"]
            for name, output in zip(agent_names, outputs):
                save_finding(decision_id, name, output, now_iso())
            save_decision(decision_id, decision["title"], decision["objective"], "Ready for Review", created, report)
            (OUTPUT_DIR / f"{decision_id}.md").write_text(report, encoding="utf-8")
            progress.progress(100, text="Decision analysis completed.")
            st.success("Decision analysis completed and saved to SQLite memory.")
            st.session_state["selected_decision"] = decision_id
            st.info("Open **Decision Room** from the sidebar to inspect the executive brief, agent findings and evidence.")
        except Exception as exc:
            save_decision(decision_id, decision["title"], decision["objective"], "Failed", created)
            st.error(f"The analysis could not complete: {exc}")
            st.caption("Check your Groq API key, package installation and deployment logs.")
