import streamlit as st
from config.agent_config import AGENT_NAMES
from crews.decision_crew import run_decision
from memory.database import (
    update_decision_status, replace_findings, replace_sources,
    save_conversation, list_conversations
)
from rag.retriever import retrieve_context
from config.settings import TOP_K, OUTPUT_DIR
from utils.helpers import now_iso


def render_continue_decision(row):
    st.markdown("### Continue Decision")
    st.caption("Continue the selected decision using its existing context.")
    previous_turns = list_conversations(row["decision_id"])
    if previous_turns:
        st.caption(f"Previous follow-up messages: {len(previous_turns)}")
    question = st.text_area(
        "Follow-up question or instruction",
        height=110,
        placeholder="e.g. What changes if the investment increases by 20%?",
        key=f"followup_{row['decision_id']}",
    )
    if not st.button("▶ Continue Analysis", key=f"continue_{row['decision_id']}", use_container_width=True):
        return
    if not question.strip():
        st.warning("Enter a follow-up question first.")
        return

    prompt = f"""
Continue the existing enterprise decision.
Original objective: {row['objective']}
Original constraints: {row['constraints'] or 'Not specified'}
Previous executive brief:
{(row['report'] or '')[:7000]}

Follow-up question:
{question}
"""
    decision = {
        "title": row["title"],
        "objective": prompt,
        "decision_type": row["decision_type"] or "Follow-up",
        "constraints": row["constraints"] or "Use the original decision constraints and evidence.",
    }
    save_conversation(row["decision_id"], "executive", question, now_iso())
    update_decision_status(
        row["decision_id"], status="Analyzing",
        executive_status="Pending Executive Review", error_message=""
    )
    try:
        evidence = retrieve_context(prompt, TOP_K)
        report, outputs, sources = run_decision(decision, evidence)
        replace_findings(
            row["decision_id"],
            list(zip(AGENT_NAMES, outputs)),
            now_iso()
        )
        source_rows = [{
            "source_name": "Enterprise evidence / RAG",
            "source_type": "Internal",
            "details": "Enterprise evidence retrieved for the continued analysis.",
        }]
        source_rows += [{
            "source_name": s.get("title", "Web source"),
            "source_type": "External Web",
            "url": s.get("url", ""),
            "accessed_at": s.get("accessed_at", ""),
            "details": s.get("snippet", "External research used during continuation."),
        } for s in sources if s.get("url")]
        replace_sources(row["decision_id"], source_rows)
        update_decision_status(
            row["decision_id"], status="Completed", report=report,
            executive_status="Pending Executive Review", error_message=""
        )
        (OUTPUT_DIR / f"{row['decision_id']}.md").write_text(report, encoding="utf-8")
        save_conversation(row["decision_id"], "system", report, now_iso())
        st.success("Follow-up analysis completed. The existing decision has been updated.")
        st.rerun()
    except Exception as exc:
        update_decision_status(
            row["decision_id"], status="Failed",
            error_message=str(exc),
            executive_status="Pending Executive Review"
        )
        st.error("The follow-up analysis failed.")
        st.code(str(exc), language="text")
