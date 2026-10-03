import os
import time

import streamlit as st
from groq import Groq

from memory.database import (
    update_decision_status,
    save_conversation,
    list_conversations,
)
from config.settings import OUTPUT_DIR
from utils.helpers import now_iso


# ---------------------------------------------------------
# Groq client
# ---------------------------------------------------------

def get_followup_client():
    """
    Create a direct Groq client for lightweight follow-up questions.

    IMPORTANT:
    Follow-up questions intentionally do NOT call the full
    9-agent CrewAI workflow. This keeps token usage low.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Please add GROQ_API_KEY to Streamlit Secrets."
        )

    return Groq(api_key=api_key)


# ---------------------------------------------------------
# Text limits
# ---------------------------------------------------------

def compact_text(text, max_chars):
    """
    Keep prompts small so follow-up questions do not consume
    unnecessary TPM.
    """

    text = str(text or "").strip()

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "\n\n[Previous content shortened to reduce token usage.]"
    )


# ---------------------------------------------------------
# Continue Decision UI
# ---------------------------------------------------------

def render_continue_decision(row):

    st.markdown("### Continue Decision")

    st.caption(
        "Ask a follow-up question about this completed decision. "
        "Follow-up analysis uses a lightweight single-model request "
        "instead of restarting the full multi-agent workflow."
    )

    # -----------------------------------------------------
    # Previous follow-up messages
    # -----------------------------------------------------

    previous_turns = list_conversations(row["decision_id"])

    if previous_turns:
        st.caption(
            f"Previous follow-up messages: {len(previous_turns)}"
        )

    # -----------------------------------------------------
    # Follow-up question
    # -----------------------------------------------------

    question = st.text_area(
        "Follow-up question or instruction",
        height=120,
        placeholder=(
            "Example: What happens if the initial investment "
            "increases from PKR 50 million to PKR 60 million?"
        ),
        key=f"followup_{row['decision_id']}",
    )

    # -----------------------------------------------------
    # Start button
    # -----------------------------------------------------

    if not st.button(
        "▶ Continue Analysis",
        key=f"continue_{row['decision_id']}",
        use_container_width=True,
    ):
        return

    # -----------------------------------------------------
    # Validate question
    # -----------------------------------------------------

    if not question.strip():
        st.warning("Please enter a follow-up question first.")
        return

    # -----------------------------------------------------
    # Prepare compact decision context
    # -----------------------------------------------------

    decision_title = compact_text(
        row.get("title", "Enterprise Decision"),
        500,
    )

    objective = compact_text(
        row.get("objective", ""),
        1800,
    )

    constraints = compact_text(
        row.get("constraints", "Not specified"),
        1800,
    )

    previous_report = compact_text(
        row.get("report", ""),
        5000,
    )

    followup_question = compact_text(
        question,
        1800,
    )

    # -----------------------------------------------------
    # Build lightweight follow-up prompt
    # -----------------------------------------------------

    prompt = f"""
You are continuing an existing enterprise decision analysis.

Do NOT restart the full multi-agent workflow.

Answer ONLY the follow-up question using the existing decision
context provided below.

DECISION:
{decision_title}

ORIGINAL OBJECTIVE:
{objective}

ORIGINAL CONSTRAINTS:
{constraints}

PREVIOUS EXECUTIVE BRIEF:
{previous_report}

FOLLOW-UP QUESTION:
{followup_question}

INSTRUCTIONS:

1. Answer the follow-up question directly.
2. Use only the information available in the decision context.
3. Do not invent company facts.
4. Do not invent company policies.
5. Do not invent prices, suppliers, financial results, regulations,
   property details, or other unavailable facts.
6. Clearly identify assumptions.
7. Clearly identify evidence gaps when information is missing.
8. Perform simple calculations when the required numbers are available.
9. Keep the answer concise and executive-friendly.
10. Do not provide hidden reasoning or chain-of-thought.
11. Do not restart the original 9-agent decision process.
"""

    # -----------------------------------------------------
    # Save user's follow-up question
    # -----------------------------------------------------

    save_conversation(
        row["decision_id"],
        "executive",
        followup_question,
        now_iso(),
    )

    # -----------------------------------------------------
    # Mark decision as analyzing
    # -----------------------------------------------------

    update_decision_status(
        row["decision_id"],
        status="Analyzing",
        executive_status="Pending Executive Review",
        error_message="",
    )

    st.info(
        "Running lightweight follow-up analysis using "
        "one GPT-OSS 120B request..."
    )

    # -----------------------------------------------------
    # Call Groq
    # -----------------------------------------------------

    try:

        client = get_followup_client()

        response = None
        last_error = None

        # -------------------------------------------------
        # Maximum TWO attempts
        # -------------------------------------------------

        for attempt in range(2):

            try:

                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",

                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],

                    temperature=0.2,

                    # Keep follow-up answers short.
                    max_completion_tokens=500,

                    # Reduce reasoning-token consumption.
                    reasoning_effort="low",

                    # Do not request visible reasoning.
                    include_reasoning=False,
                )

                break

            except Exception as exc:

                last_error = exc

                error_text = str(exc).lower()

                rate_limit_error = (
                    "rate limit" in error_text
                    or "429" in error_text
                    or "tpm" in error_text
                    or "too many requests" in error_text
                    or "tokens per minute" in error_text
                )

                # -----------------------------------------
                # If TPM limit is reached, wait once
                # -----------------------------------------

                if rate_limit_error and attempt == 0:

                    st.warning(
                        "The Groq token-per-minute limit was reached. "
                        "Waiting before retrying the follow-up request..."
                    )

                    # Give the TPM window time to recover.
                    time.sleep(65)

                else:
                    raise

        # -------------------------------------------------
        # Verify response
        # -------------------------------------------------

        if response is None:

            raise RuntimeError(
                f"Groq follow-up request failed: {last_error}"
            )

        # -------------------------------------------------
        # Extract answer
        # -------------------------------------------------

        answer = ""

        if response.choices:

            message = response.choices[0].message

            answer = getattr(
                message,
                "content",
                "",
            ) or ""

        answer = answer.strip()

        # -------------------------------------------------
        # Empty-response protection
        # -------------------------------------------------

        if not answer:

            raise RuntimeError(
                "Groq returned an empty response for the "
                "follow-up question."
            )

        # -------------------------------------------------
        # Keep original executive report
        # -------------------------------------------------

        existing_report = (
            row.get("report") or ""
        ).strip()

        # -------------------------------------------------
        # Append follow-up analysis
        # -------------------------------------------------

        updated_report = (
            existing_report
            + "\n\n"
            + "=" * 70
            + "\n"
            + "FOLLOW-UP ANALYSIS"
            + "\n"
            + "=" * 70
            + "\n\n"
            + "Question:\n"
            + followup_question
            + "\n\n"
            + "Analysis:\n"
            + answer
            + "\n"
        )

        # -------------------------------------------------
        # Save updated decision
        # -------------------------------------------------

        update_decision_status(
            row["decision_id"],
            status="Completed",
            report=updated_report,
            executive_status="Pending Executive Review",
            error_message="",
        )

        # -------------------------------------------------
        # Save report file
        # -------------------------------------------------

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path = (
            OUTPUT_DIR
            / f"{row['decision_id']}.md"
        )

        report_path.write_text(
            updated_report,
            encoding="utf-8",
        )

        # -------------------------------------------------
        # Save assistant response
        # -------------------------------------------------

        save_conversation(
            row["decision_id"],
            "system",
            answer,
            now_iso(),
        )

        # -------------------------------------------------
        # Display result
        # -------------------------------------------------

        st.success(
            "Follow-up analysis completed successfully."
        )

        st.markdown("### Follow-up Result")

        st.markdown(answer)

        # -------------------------------------------------
        # Refresh application
        # -------------------------------------------------

        st.rerun()

    # -----------------------------------------------------
    # Error handling
    # -----------------------------------------------------

    except Exception as exc:

        error_message = str(exc)

        update_decision_status(
            row["decision_id"],
            status="Failed",
            error_message=error_message,
            executive_status="Pending Executive Review",
        )

        st.error(
            "The follow-up analysis failed."
        )

        st.code(
            error_message,
            language="text",
        )
