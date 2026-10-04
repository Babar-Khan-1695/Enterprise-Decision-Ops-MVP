import re
import streamlit as st

from ui.agent_monitor import render_agent_monitor
from ui.scenario_viewer import render_scenario_viewer
from ui.evidence_viewer import render_evidence

from config.agent_config import AGENT_NAMES
from config.settings import OUTPUT_DIR

from memory.database import (
    update_decision_status,
    list_sources,
)

from ui.continuation import render_continue_decision


# ============================================================
# Helpers
# ============================================================

def _clean_markdown(text):
    """
    Convert common Markdown formatting into clean readable text
    for the Decision Table.

    The original finding is preserved elsewhere in Agent Findings.
    """

    text = str(text or "").strip()

    if not text:
        return "No finding returned."

    # Remove markdown headings
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Bold / italic markers
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")

    # Inline code
    text = text.replace("`", "")

    # Markdown links -> visible text
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text,
    )

    # Horizontal rules
    text = re.sub(
        r"^\s*[-*_]{3,}\s*$",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Bullet markers
    text = re.sub(
        r"^\s*[-•]\s+",
        "• ",
        text,
        flags=re.MULTILINE,
    )

    # Excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def _short_finding(text, limit=650):
    cleaned = _clean_markdown(text)

    if len(cleaned) <= limit:
        return cleaned

    return cleaned[:limit].rstrip() + "..."


def _status_badge(index):
    if index == 0:
        return "🧭 Lead"

    return "✓ Complete"


# ============================================================
# Decision Room
# ============================================================

def render_decision_room(
    decision_id,
    title,
    report,
    findings,
    status="Completed",
    error_message="",
    row=None,
):

    st.markdown(f"## Decision Room · {title}")

    # --------------------------------------------------------
    # Convert sqlite3.Row into normal dictionary.
    # This also makes the function safer for future changes.
    # --------------------------------------------------------

    if row is not None:
        try:
            row = dict(row)
        except Exception:
            pass

    executive_status = (
        row.get("executive_status", "Pending Executive Review")
        if row is not None
        else "Pending Executive Review"
    )

    st.caption(
        f"{decision_id} · "
        f"AI Analysis: {status} · "
        f"Executive Status: {executive_status}"
    )

    # --------------------------------------------------------
    # Failed decision
    # --------------------------------------------------------

    if status == "Failed":
        st.error("This decision failed during AI analysis.")

        if error_message:
            st.code(
                error_message,
                language="text",
            )

        return

    # --------------------------------------------------------
    # Agent monitor
    # --------------------------------------------------------

    render_agent_monitor(
        [
            {
                "name": name,
                "status": "complete",
            }
            for name in AGENT_NAMES
        ]
    )

    # --------------------------------------------------------
    # Tabs
    # --------------------------------------------------------

    tabs = st.tabs(
        [
            "Executive Brief",
            "Decision Table",
            "Agent Findings",
            "Scenarios",
            "Evidence",
            "Sources & Evidence",
            "Continue Decision",
            "Download",
        ]
    )

    # ========================================================
    # 1. Executive Brief
    # ========================================================

    with tabs[0]:

        st.markdown(
            report or "No executive report is available."
        )

        st.markdown("### Executive Decision Status")

        if executive_status == "Approved by Executive":
            st.success(
                "✅ Current status: **Approved by Executive**"
            )

        elif executive_status == "Rejected by Executive":
            st.error(
                "❌ Current status: **Rejected by Executive**"
            )

        else:
            st.info(
                "⏳ Current status: **Pending Executive Review**"
            )

        st.markdown("")

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button(
                "⏳ Pending Review",
                key=f"pending_room_{decision_id}",
                use_container_width=True,
            ):
                update_decision_status(
                    decision_id,
                    executive_status="Pending Executive Review",
                )
                st.rerun()

        with c2:
            if st.button(
                "✅ Approve Decision",
                key=f"approve_room_{decision_id}",
                use_container_width=True,
            ):
                update_decision_status(
                    decision_id,
                    executive_status="Approved by Executive",
                )
                st.rerun()

        with c3:
            if st.button(
                "❌ Reject Decision",
                key=f"reject_room_{decision_id}",
                use_container_width=True,
            ):
                update_decision_status(
                    decision_id,
                    executive_status="Rejected by Executive",
                )
                st.rerun()

    # ========================================================
    # 2. Decision Table
    # ========================================================

    with tabs[1]:

        st.markdown("### Multi-Agent Decision Summary")

        st.caption(
            "A concise view of what each specialist contributed. "
            "Open Agent Findings for the complete analysis."
        )

        if not findings:

            st.warning(
                "No individual findings were saved for this decision."
            )

        else:

            # ------------------------------------------------
            # Attractive agent summary cards
            # ------------------------------------------------

            for index, finding in enumerate(findings):

                agent_name = finding["agent_name"]
                raw_finding = finding["finding"] or ""

                clean_finding = _short_finding(
                    raw_finding,
                    700,
                )

                with st.container(border=True):

                    header_col, status_col = st.columns(
                        [4, 1]
                    )

                    with header_col:
                        st.markdown(
                            f"### {agent_name}"
                        )

                    with status_col:
                        st.markdown(
                            f"**{_status_badge(index)}**"
                        )

                    st.markdown(
                        clean_finding
                    )

                    # Small footer
                    st.caption(
                        "Complete finding available in Agent Findings."
                    )

        # ----------------------------------------------------
        # Optional compact overview row
        # ----------------------------------------------------

        if findings:

            st.markdown("")

            total_agents = len(findings)
            completed_agents = len(findings)

            m1, m2, m3 = st.columns(3)

            with m1:
                st.metric(
                    "Specialist Agents",
                    total_agents,
                )

            with m2:
                st.metric(
                    "Completed",
                    completed_agents,
                )

            with m3:
                st.metric(
                    "Decision Status",
                    "Ready for Review",
                )

    # ========================================================
    # 3. Complete Agent Findings
    # ========================================================

    with tabs[2]:

        st.markdown("### Agent Findings")

        if not findings:

            st.warning(
                "No individual findings were saved for this decision."
            )

        else:

            for index, finding in enumerate(findings):

                agent_name = finding["agent_name"]
                agent_finding = (
                    finding["finding"]
                    or "No finding returned."
                )

                with st.expander(
                    f"{index + 1}. {agent_name}",
                    expanded=False,
                ):

                    # IMPORTANT:
                    # Use markdown here because the actual finding
                    # intentionally contains Markdown formatting.
                    st.markdown(agent_finding)

    # ========================================================
    # 4. Scenarios
    # ========================================================

    with tabs[3]:

        render_scenario_viewer(
            report
        )

    # ========================================================
    # 5. Evidence
    # ========================================================

    with tabs[4]:

        st.markdown("### Enterprise Evidence")

        query = st.text_input(
            "Search enterprise evidence",
            placeholder=(
                "e.g. What policy applies to capital expenditure?"
            ),
            key=f"evidence_q_{decision_id}",
        )

        if st.button(
            "🔎 Search Evidence",
            key=f"search_e_{decision_id}",
            use_container_width=True,
        ):

            if not query.strip():

                st.warning(
                    "Enter a search question first."
                )

            else:

                render_evidence(
                    query
                )

    # ========================================================
    # 6. Sources & Evidence
    # ========================================================

    with tabs[5]:

        st.markdown("### Sources & Evidence")

        sources = list_sources(
            decision_id
        )

        if not sources:

            st.info(
                "No source records were saved."
            )

        else:

            for index, source in enumerate(
                sources,
                1,
            ):

                with st.container(border=True):

                    st.markdown(
                        f"### {index}. {source['source_name']}"
                    )

                    st.caption(
                        source["source_type"]
                    )

                    if source["url"]:

                        st.markdown(
                            f"**Source:** {source['url']}"
                        )

                    if source["accessed_at"]:

                        st.caption(
                            f"Accessed: {source['accessed_at']}"
                        )

                    if source["details"]:

                        st.markdown(
                            source["details"]
                        )

    # ========================================================
    # 7. Continue Decision
    # ========================================================

    with tabs[6]:

        if row is not None:

            render_continue_decision(
                row
            )

        else:

            st.warning(
                "Decision context is unavailable."
            )

    # ========================================================
    # 8. Download
    # ========================================================

    with tabs[7]:

        st.markdown(
            "### Download Executive Decision Brief"
        )

        path = OUTPUT_DIR / f"{decision_id}.md"

        data = (
            path.read_bytes()
            if path.exists()
            else (report or "").encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Executive Decision Brief",
            data=data,
            file_name=(
                f"{decision_id}_Executive_Decision_Brief.md"
            ),
            mime="text/markdown",
            use_container_width=True,
        )
