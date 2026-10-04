import streamlit as st
from ui.agent_monitor import render_agent_monitor
from ui.scenario_viewer import render_scenario_viewer
from ui.evidence_viewer import render_evidence
from ui.report_renderer import render_report_with_tables, render_status_card
from config.agent_config import AGENT_NAMES
from config.settings import OUTPUT_DIR
from memory.database import update_decision_status, list_sources
from ui.continuation import render_continue_decision


def render_decision_room(decision_id, title, report, findings, status="Completed", error_message="", row=None):
    st.markdown(f"## Decision Room · {title}")

    if row is not None:
        try:
            row_dict = dict(row)
        except Exception:
            row_dict = {}
    else:
        row_dict = {}

    executive_status = row_dict.get(
        "executive_status",
        "Pending Executive Review",
    )

    st.caption(
        f"{decision_id} · AI Analysis: {status}"
    )
    render_status_card(executive_status)

    if status == "Failed":
        st.error("This decision failed during AI analysis.")
        if error_message:
            st.code(error_message, language="text")
        return

    render_agent_monitor(
        [{"name": n, "status": "complete"} for n in AGENT_NAMES]
    )

    tabs = st.tabs([
        "Executive Brief",
        "Decision Table",
        "Agent Findings",
        "Scenarios",
        "Evidence",
        "Sources & Evidence",
        "Continue Decision",
        "Download",
    ])

    with tabs[0]:
        render_report_with_tables(
            report or "No executive report is available."
        )

        st.markdown("### Executive Decision Status")
        render_status_card(executive_status)

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

    with tabs[1]:
        st.markdown("### Multi-Agent Decision Summary")
        st.caption(
            "Clean summaries of each specialist finding. Open Agent Findings for the complete analysis."
        )

        if not findings:
            st.warning("No individual findings were saved for this decision.")
        else:
            for index, finding in enumerate(findings, 1):
                with st.container(border=True):
                    left, right = st.columns([5, 1])
                    with left:
                        st.markdown(
                            f"### {index}. {finding['agent_name']}"
                        )
                    with right:
                        st.success("Complete")

                    clean = str(
                        finding["finding"] or "No finding returned."
                    )
                    # Remove common markdown decoration from the compact table/card.
                    clean = clean.replace("**", "")
                    clean = clean.replace("###", "")
                    clean = clean.replace("##", "")

                    if len(clean) > 800:
                        clean = clean[:800].rstrip() + "..."

                    st.write(clean)

    with tabs[2]:
        st.markdown("### Agent Findings")
        if not findings:
            st.warning("No individual findings were saved for this decision.")
        else:
            for f in findings:
                with st.expander(f["agent_name"], expanded=False):
                    st.markdown(f["finding"] or "No finding returned.")

    with tabs[3]:
        render_scenario_viewer(report)

    with tabs[4]:
        query = st.text_input(
            "Search enterprise evidence",
            placeholder="e.g. What policy applies to capital expenditure?",
            key=f"evidence_q_{decision_id}",
        )
        if st.button(
            "Search Evidence",
            key=f"search_e_{decision_id}",
            use_container_width=True,
        ):
            if query.strip():
                render_evidence(query)
            else:
                st.warning("Enter a search question first.")

    with tabs[5]:
        st.markdown("### Sources & Evidence")
        sources = list_sources(decision_id)
        if not sources:
            st.info("No source records were saved.")
        else:
            for index, source in enumerate(sources, 1):
                with st.container(border=True):
                    st.markdown(
                        f"### {index}. {source['source_name']}"
                    )
                    st.caption(source["source_type"])
                    if source["url"]:
                        st.markdown(source["url"])
                    if source["accessed_at"]:
                        st.caption(
                            f"Accessed: {source['accessed_at']}"
                        )
                    if source["details"]:
                        st.write(source["details"])

    with tabs[6]:
        if row is not None:
            render_continue_decision(row)
        else:
            st.warning("Decision context is unavailable.")

    with tabs[7]:
        path = OUTPUT_DIR / f"{decision_id}.md"
        data = (
            path.read_bytes()
            if path.exists()
            else (report or "").encode("utf-8")
        )
        st.download_button(
            "⬇️ Download Executive Decision Brief",
            data=data,
            file_name=f"{decision_id}_Executive_Decision_Brief.md",
            mime="text/markdown",
            use_container_width=True,
        )
