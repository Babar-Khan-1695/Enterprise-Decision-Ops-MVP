import os
import time
import streamlit as st

from groq import Groq

from memory.database import (
    update_decision_status,
    save_conversation,
    list_conversations,
)
from config.settings import OUTPUT_DIR, MAX_CONTEXT_CHARS
from utils.helpers import now_iso


# ============================================================
# Helpers
# ============================================================

def _to_dict(row):
    """
    Convert sqlite3.Row / dictionary-like objects into a normal
    Python dictionary.

    This prevents errors such as:
    AttributeError: 'sqlite3.Row' object has no attribute 'get'
    """
    if row is None:
        return {}

    if isinstance(row, dict):
        return row

    try:
        return dict(row)
    except Exception:
        return {
            key: row[key]
            for key in row.keys()
        }


def _compact_text(value, limit):
    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit].rstrip() + "\n...[content shortened]..."


def _get_groq_client():
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add the API key to Streamlit Secrets."
        )

    return Groq(api_key=api_key)


def _call_followup_model(prompt):
    """
    Lightweight follow-up call.

    IMPORTANT:
    This does NOT run the CrewAI 9-agent workflow again.
    It makes only one direct Groq request.
    """

    client = _get_groq_client()

    last_error = None

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are the Enterprise DecisionOps executive "
                            "follow-up analyst. Answer the user's follow-up "
                            "question using only the supplied decision context. "
                            "Do not invent company facts. Clearly distinguish "
                            "known facts, assumptions, and evidence gaps. "
                            "Be concise and executive-friendly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                max_completion_tokens=500,
                reasoning_effort="low",
                include_reasoning=False,
            )

            content = response.choices[0].message.content

            if content and content.strip():
                return content.strip()

            raise RuntimeError("The follow-up model returned an empty response.")

        except Exception as exc:
            last_error = exc

            error_text = str(exc).lower()

            rate_limited = (
                "rate limit" in error_text
                or "tpm" in error_text
                or "tokens per minute" in error_text
                or "429" in error_text
            )

            if rate_limited and attempt == 0:
                time.sleep(65)
                continue

            raise

    raise last_error or RuntimeError("Follow-up analysis failed.")


# ============================================================
# Main UI
# ============================================================

def render_continue_decision(row):
    """
    Render the lightweight Continue Decision experience.

    This function accepts both:
      - sqlite3.Row
      - normal dict

    Therefore it can safely be called from:
      - Decision Room
      - Decision History
    """

    # --------------------------------------------------------
    # IMPORTANT FIX:
    # sqlite3.Row does not provide .get()
    # Convert it to a normal dictionary first.
    # --------------------------------------------------------

    row = _to_dict(row)

    decision_id = row.get("decision_id", "")
    decision_title = _compact_text(
        row.get("title", "Enterprise Decision"),
        300,
    )

    objective = _compact_text(
        row.get("objective", ""),
        2500,
    )

    constraints = _compact_text(
        row.get("constraints", ""),
        2200,
    )

    report = _compact_text(
        row.get("report", ""),
        4500,
    )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    st.markdown("### Continue Decision")

    st.caption(
        "Ask a follow-up question about this decision without "
        "re-running the complete multi-agent workflow."
    )

    # --------------------------------------------------------
    # Previous conversation
    # --------------------------------------------------------

    previous_turns = list_conversations(decision_id)

    if previous_turns:
        st.markdown(
            f"**Previous follow-up messages:** {len(previous_turns)}"
        )

        with st.expander("View previous follow-up conversation", expanded=False):
            for turn in previous_turns:
                speaker = str(turn["speaker"]).strip().lower()
                message = turn["message"] or ""

                if speaker == "executive":
                    st.markdown("**Executive / User**")
                    st.markdown(message)

                elif speaker == "system":
                    st.markdown("**DecisionOps Analysis**")
                    st.markdown(message)

                else:
                    st.markdown(f"**{turn['speaker']}**")
                    st.markdown(message)

                st.divider()

    # --------------------------------------------------------
    # Decision context
    # --------------------------------------------------------

    with st.expander("Decision Context", expanded=False):
        st.markdown(f"**Decision:** {decision_title}")

        if objective:
            st.markdown("**Objective**")
            st.markdown(objective)

        if constraints:
            st.markdown("**Constraints**")
            st.markdown(constraints)

    # --------------------------------------------------------
    # Follow-up input
    # --------------------------------------------------------

    question = st.text_area(
        "Follow-up question or instruction",
        height=110,
        placeholder=(
            "Example: What happens if the initial investment "
            "increases by 20%?"
        ),
        key=f"followup_{decision_id}",
    )

    # --------------------------------------------------------
    # Continue button
    # --------------------------------------------------------

    if not st.button(
        "▶ Continue Analysis",
        key=f"continue_{decision_id}",
        use_container_width=True,
    ):
        return

    if not question.strip():
        st.warning("Enter a follow-up question first.")
        return

    # --------------------------------------------------------
    # Build compact follow-up prompt
    # --------------------------------------------------------

    prompt = f"""
Existing Enterprise Decision

Decision Title:
{decision_title}

Original Objective:
{objective}

Original Constraints:
{constraints or "Not specified"}

Existing Executive Decision Brief:
{report or "No previous executive brief is available."}

Follow-up Question:
{question.strip()}

Instructions:
- Answer the follow-up question directly.
- Use the existing decision context.
- Do not invent company-specific facts.
- Clearly distinguish confirmed information from assumptions.
- Identify an evidence gap if the answer requires unavailable information.
- Keep the response concise and suitable for an executive decision-maker.
"""

    prompt = _compact_text(
        prompt,
        MAX_CONTEXT_CHARS * 3,
    )

    # --------------------------------------------------------
    # Save user's question
    # --------------------------------------------------------

    save_conversation(
        decision_id,
        "executive",
        question.strip(),
        now_iso(),
    )

    update_decision_status(
        decision_id,
        status="Analyzing",
        error_message="",
        executive_status="Pending Executive Review",
    )

    # --------------------------------------------------------
    # Execute lightweight follow-up
    # --------------------------------------------------------

    with st.spinner("DecisionOps is analyzing the follow-up question..."):

        try:
            answer = _call_followup_model(prompt)

            # ------------------------------------------------
            # Save AI response
            # ------------------------------------------------

            save_conversation(
                decision_id,
                "system",
                answer,
                now_iso(),
            )

            # ------------------------------------------------
            # Preserve the original executive report.
            # Add the follow-up as a separate section.
            # ------------------------------------------------

            existing_report = row.get("report", "") or ""

            followup_section = (
                "\n\n"
                "## Follow-up Analysis\n\n"
                f"**Question:** {question.strip()}\n\n"
                f"{answer}\n"
            )

            updated_report = existing_report + followup_section

            # ------------------------------------------------
            # Save updated report
            # ------------------------------------------------

            update_decision_status(
                decision_id,
                status="Completed",
                report=updated_report,
                error_message="",
                executive_status="Pending Executive Review",
            )

            output_path = OUTPUT_DIR / f"{decision_id}.md"
            output_path.write_text(
                updated_report,
                encoding="utf-8",
            )

            # ------------------------------------------------
            # Display result
            # ------------------------------------------------

            st.success("Follow-up analysis completed.")

            st.markdown("### Follow-up Analysis")

            st.markdown(
                """
                <div style="
                    border:1px solid #dbeafe;
                    background:#f8fbff;
                    border-radius:14px;
                    padding:18px;
                    margin-top:8px;
                    margin-bottom:16px;
                ">
                """,
                unsafe_allow_html=True,
            )

            st.markdown(answer)

            st.markdown("</div>", unsafe_allow_html=True)

            st.caption(
                "This follow-up used the existing decision context "
                "and did not re-run the full 9-agent analysis."
            )

        except Exception as exc:

            error_text = str(exc)

            update_decision_status(
                decision_id,
                status="Failed",
                error_message=error_text,
                executive_status="Pending Executive Review",
            )

            st.error("The follow-up analysis failed.")

            st.code(
                error_text,
                language="text",
            )
