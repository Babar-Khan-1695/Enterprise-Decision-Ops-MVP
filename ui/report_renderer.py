import re
import streamlit as st


def _clean_inline_markdown(text: str) -> str:
    text = str(text or "").strip()
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("`", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _find_alternatives_section(report: str):
    if not report:
        return None

    heading_pattern = re.compile(
        r"(?im)^\s*#{1,6}\s*(?:\d+\.\s*)?alternatives\s*$"
    )
    match = heading_pattern.search(report)
    if not match:
        return None

    start = match.end()
    next_heading = re.search(r"(?im)^\s*#{1,6}\s+", report[start:])
    end = start + next_heading.start() if next_heading else len(report)

    return {
        "start": match.start(),
        "content_start": start,
        "end": end,
        "heading": match.group(0).strip(),
        "body": report[start:end].strip(),
    }


def _parse_alternatives(body: str):
    alternatives = []

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        line = re.sub(r"^[-*•]\s+", "", line).strip()
        line = re.sub(r"^#{1,6}\s*", "", line).strip()
        line = _clean_inline_markdown(line)

        # Expected forms:
        # A. Proceed with ...
        # A) Proceed with ...
        # 1. Proceed with ...
        match = re.match(r"^([A-Z]|\d+)[.)]\s+(.+)$", line)
        if not match:
            continue

        option = match.group(1).upper()
        description = match.group(2).strip()

        # If the model writes a title followed by a dash, split it cleanly.
        if " — " in description:
            title, detail = description.split(" — ", 1)
        elif " - " in description:
            title, detail = description.split(" - ", 1)
        else:
            title, detail = description, ""

        alternatives.append({
            "Option": option,
            "Alternative": title.strip(),
            "Key consideration": detail.strip(),
        })

    return alternatives


def render_report_with_tables(report: str):
    """
    Render an executive report while converting the Alternatives section
    into a structured Streamlit table instead of displaying raw Markdown.
    """
    if not report:
        st.info("No executive report is available.")
        return

    section = _find_alternatives_section(report)

    if not section:
        st.markdown(report)
        return

    before = report[:section["start"]].strip()
    after = report[section["end"]:].strip()
    alternatives = _parse_alternatives(section["body"])

    if before:
        st.markdown(before)

    st.markdown("### Alternatives")

    if alternatives:
        st.dataframe(
            alternatives,
            column_config={
                "Option": st.column_config.TextColumn(
                    "Option",
                    width="small",
                ),
                "Alternative": st.column_config.TextColumn(
                    "Alternative",
                    width="medium",
                ),
                "Key consideration": st.column_config.TextColumn(
                    "Key consideration",
                    width="large",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No structured alternatives were identified in this decision brief.")

    if after:
        st.markdown(after)


def render_status_card(status: str):
    """Render the complete executive status without metric truncation."""
    status = str(status or "Pending Executive Review")

    if status == "Approved by Executive":
        background = "#ecfdf5"
        border = "#86efac"
        text = "#166534"
        icon = "✅"
    elif status == "Rejected by Executive":
        background = "#fef2f2"
        border = "#fca5a5"
        text = "#991b1b"
        icon = "❌"
    else:
        background = "#eff6ff"
        border = "#93c5fd"
        text = "#1d4ed8"
        icon = "⏳"

    st.markdown(
        f"""
        <div style="
            border:1px solid {border};
            background:{background};
            border-radius:14px;
            padding:14px 18px;
            margin:8px 0 16px 0;
        ">
            <div style="font-size:0.82rem;color:#64748b;margin-bottom:4px;">
                EXECUTIVE DECISION STATUS
            </div>
            <div style="font-size:1.15rem;font-weight:700;color:{text};">
                {icon}&nbsp; {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
