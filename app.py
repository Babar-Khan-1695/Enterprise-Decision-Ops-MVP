import os
from pathlib import Path
import streamlit as st

from config.settings import OUTPUT_DIR, TOP_K
from config.agent_config import AGENT_NAMES
from utils.helpers import now_iso
from tools.decision_tools import new_decision_id
from memory.database import init_db, save_decision, save_finding, get_decision, update_decision_status
from memory.decision_memory import list_decisions
from rag.vector_store import has_index
from rag.retriever import retrieve_context
from crews.decision_crew import run_decision
from crews.task_manager import task_statuses, is_rate_limit_error, rate_limit_wait_seconds
from ui.dashboard import render_dashboard
from ui.decision_input import render_input, render_analysis_panel
from ui.decision_room import render_decision_room
from ui.history import render_history
from ui.system_health import render_system_health

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
.agent-working { border:1px solid #93c5fd; background:#eff6ff; border-radius:12px; padding:12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>◈ Enterprise DecisionOps</h1>
<p>A governed multi-agent decision intelligence workspace for complex enterprise decisions.</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.get("run_analysis"):
    default_page = "New Decision"
else:
    default_page = st.session_state.get("workspace_page", "Executive Dashboard")

pages = ["Executive Dashboard", "New Decision", "Decision Room", "Decision History", "System Health"]
with st.sidebar:
    st.markdown("## DecisionOps")
    st.caption("Multi-agent enterprise decision intelligence")
    st.divider()
    page = st.radio("Workspace", pages, index=pages.index(default_page))
    if page != default_page:
        st.session_state["workspace_page"] = page
    st.divider()
    st.caption("Use System Health for technical/runtime status.")

if not load_secret() and page in ("New Decision", "System Health"):
    st.warning("Add `GROQ_API_KEY` to Streamlit Secrets before running an analysis.")

if page == "Executive Dashboard":
    render_dashboard()

elif page == "New Decision":
    render_input()
    if not st.session_state.get("run_analysis"):
        render_analysis_panel()

elif page == "Decision History":
    render_history()

elif page == "System Health":
    render_system_health(load_secret)

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
        render_decision_room(
            row["decision_id"],
            row["title"],
            row["report"],
            findings,
            row["status"],
            row["error_message"],
        )


def update_agent_ui(completed_count, error_index=None):
    statuses = task_statuses(completed_count)
    if error_index is not None and 0 <= error_index < len(statuses):
        statuses[error_index]["status"] = "error"
    st.session_state["agent_statuses"] = statuses
    if completed_count < len(AGENT_NAMES) and error_index is None:
        st.session_state["active_agent"] = AGENT_NAMES[completed_count]
    else:
        st.session_state["active_agent"] = None


def run_pending_analysis():
    decision = st.session_state.pop("pending_decision", None)
    if not decision:
        return

    decision_id = new_decision_id()
    created = now_iso()
    st.session_state["active_decision_id"] = decision_id
    st.session_state["analysis_status"] = "Analyzing"
    st.session_state["analysis_error"] = ""
    update_agent_ui(0)
    save_decision(decision_id, decision["title"], decision["objective"], "Analyzing", created)

    st.markdown("---")
    st.markdown(f"### Live Decision Processing · `{decision_id}`")
    progress = st.progress(0, text="Preparing evidence and specialist agents…")
    status_box = st.empty()
    agent_box = st.empty()
    note_box = st.empty()

    def render_live(completed_count, current=None, error_index=None):
        statuses = task_statuses(completed_count)
        if error_index is not None and 0 <= error_index < len(statuses):
            statuses[error_index]["status"] = "error"
        with agent_box.container():
            st.markdown("#### Agent activity")
            cols = st.columns(3)
            for i, item in enumerate(statuses):
                with cols[i % 3]:
                    if item["status"] == "complete":
                        st.success(f"✅ {item['name']} — complete")
                    elif item["status"] == "working":
                        st.info(f"🔄 {item['name']} — **working now**")
                    elif item["status"] == "error":
                        st.error(f"❌ {item['name']} — error")
                    else:
                        st.caption(f"⏳ {item['name']} — waiting")
        if current:
            status_box.info(f"🔄 **{current} Agent is working now**")
        elif error_index is not None:
            status_box.error("❌ The agent workflow stopped because of an error.")
        else:
            status_box.success("✅ All agents completed.")

    render_live(0, AGENT_NAMES[0])

    try:
        evidence = retrieve_context(decision["objective"], TOP_K)
        progress.progress(10, text="Evidence prepared. Starting specialist agents…")

        completed = {"count": 0}

        def on_task_complete(task):
            idx = min(completed["count"], len(AGENT_NAMES) - 1)
            output = getattr(getattr(task, "output", None), "raw", "") or str(getattr(task, "output", ""))
            agent_name = AGENT_NAMES[idx]
            save_finding(decision_id, agent_name, output, now_iso())
            completed["count"] += 1
            next_agent = AGENT_NAMES[completed["count"]] if completed["count"] < len(AGENT_NAMES) else None
            update_agent_ui(completed["count"])
            render_live(completed["count"], next_agent)
            pct = min(95, 10 + int((completed["count"] / len(AGENT_NAMES)) * 85))
            progress.progress(pct, text=f"Completed {agent_name}." + (f" Starting {next_agent}…" if next_agent else " Final brief complete."))

        report, outputs = run_decision(decision, evidence, on_task_complete=on_task_complete)
        progress.progress(98, text="Saving executive decision and report…")

        # The callback normally saves each finding. This fallback covers a
        # CrewAI implementation that does not invoke task_callback.
        saved_count = completed["count"]
        if saved_count == 0:
            for name, output in zip(AGENT_NAMES, outputs):
                save_finding(decision_id, name, output, now_iso())

        save_decision(decision_id, decision["title"], decision["objective"], "Completed", created, report, "")
        (OUTPUT_DIR / f"{decision_id}.md").write_text(report, encoding="utf-8")
        update_agent_ui(len(AGENT_NAMES))
        st.session_state["analysis_status"] = "Completed"
        st.session_state["analysis_error"] = ""
        st.session_state["workspace_page"] = "New Decision"
        render_live(len(AGENT_NAMES), None)
        progress.progress(100, text="Decision analysis completed and saved.")
        st.success("Decision analysis completed successfully. Review and download the Executive Decision Brief from the Executive Dashboard.")

    except Exception as exc:
        error_text = str(exc)
        if is_rate_limit_error(exc):
            wait = rate_limit_wait_seconds(exc)
            error_text = f"Groq token rate limit reached. Please wait about {wait} seconds before retrying.\n\nOriginal error:\n{exc}"
        save_decision(decision_id, decision["title"], decision["objective"], "Failed", created, "", error_text)
        st.session_state["analysis_status"] = "Failed"
        st.session_state["analysis_error"] = error_text
        current_index = min(completed["count"], len(AGENT_NAMES) - 1)
        update_agent_ui(completed["count"], current_index)
        render_live(completed["count"], None, current_index)
        progress.progress(100, text="Decision processing stopped.")
        st.error("The decision analysis failed. The exact error is shown below and has been saved with the decision.")
        st.code(error_text, language="text")


if st.session_state.get("run_analysis") and page == "New Decision":
    st.session_state["run_analysis"] = False
    run_pending_analysis()
    render_analysis_panel()
