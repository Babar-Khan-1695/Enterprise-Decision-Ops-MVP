import os
import time
import streamlit as st
from groq import Groq
from memory.database import update_decision_status, save_conversation, list_conversations
from config.settings import OUTPUT_DIR, MAX_CONTEXT_CHARS
from utils.helpers import now_iso


def _to_dict(row):
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {key: row[key] for key in row.keys()}


def _compact_text(value, limit):
    text = str(value or '').strip()
    return text if len(text) <= limit else text[:limit].rstrip() + '\n...[content shortened]...'


def _get_client():
    api_key = os.getenv('GROQ_API_KEY', '').strip()
    if not api_key:
        raise RuntimeError('GROQ_API_KEY is not configured. Add it to Streamlit Secrets.')
    return Groq(api_key=api_key)


def _call_followup_model(prompt):
    client = _get_client()
    last_error = None
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model='openai/gpt-oss-120b',
                messages=[
                    {'role': 'system', 'content': (
                        'You are the Enterprise DecisionOps executive follow-up analyst. '
                        'Answer only from the supplied decision context. Do not invent '
                        'company facts. Distinguish facts, assumptions, and evidence gaps. '
                        'Be concise and executive-friendly.'
                    )},
                    {'role': 'user', 'content': prompt},
                ],
                max_completion_tokens=500,
                reasoning_effort='low',
                include_reasoning=False,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
            raise RuntimeError('The follow-up model returned an empty response.')
        except Exception as exc:
            last_error = exc
            low = str(exc).lower()
            rate_limited = any(x in low for x in ('rate limit', 'tpm', 'tokens per minute', '429'))
            if rate_limited and attempt == 0:
                time.sleep(65)
                continue
            raise
    raise last_error or RuntimeError('Follow-up analysis failed.')


def render_continue_decision(row):
    row = _to_dict(row)
    decision_id = row.get('decision_id', '')
    title = _compact_text(row.get('title', 'Enterprise Decision'), 300)
    objective = _compact_text(row.get('objective', ''), 2500)
    constraints = _compact_text(row.get('constraints', ''), 2200)
    report = _compact_text(row.get('report', ''), 4500)

    st.markdown('### Continue Decision')
    st.caption('Ask a follow-up about this existing decision without re-running the full 9-agent workflow.')

    previous = list_conversations(decision_id)
    if previous:
        with st.expander(f'Previous follow-up conversation ({len(previous)})', expanded=False):
            for turn in previous:
                speaker = str(turn['speaker']).strip().lower()
                label = 'Executive / User' if speaker == 'executive' else 'DecisionOps Analysis' if speaker == 'system' else str(turn['speaker'])
                st.markdown(f'**{label}**')
                st.markdown(turn['message'] or '')
                st.divider()

    with st.expander('Decision Context', expanded=False):
        st.markdown(f'**Decision:** {title}')
        if objective:
            st.markdown('**Objective**')
            st.markdown(objective)
        if constraints:
            st.markdown('**Constraints**')
            st.markdown(constraints)

    question = st.text_area(
        'Follow-up question or instruction',
        height=110,
        placeholder='Example: What happens if the initial investment increases by 20%?',
        key=f'followup_{decision_id}',
    )

    if not st.button('▶ Continue Analysis', key=f'continue_{decision_id}', use_container_width=True):
        return
    if not question.strip():
        st.warning('Enter a follow-up question first.')
        return

    prompt = _compact_text(f'''Existing Enterprise Decision

Decision Title:
{title}

Original Objective:
{objective}

Original Constraints:
{constraints or 'Not specified'}

Existing Executive Decision Brief:
{report or 'No previous executive brief is available.'}

Follow-up Question:
{question.strip()}

Instructions:
- Answer the follow-up question directly.
- Use the existing decision context.
- Do not invent company-specific facts.
- Distinguish confirmed information from assumptions.
- Identify evidence gaps when required information is unavailable.
- Keep the answer concise and suitable for an executive decision-maker.
''', MAX_CONTEXT_CHARS * 3)

    save_conversation(decision_id, 'executive', question.strip(), now_iso())
    update_decision_status(decision_id, status='Analyzing', error_message='', executive_status='Pending Executive Review')

    with st.spinner('DecisionOps is analyzing the follow-up question...'):
        try:
            answer = _call_followup_model(prompt)
            save_conversation(decision_id, 'system', answer, now_iso())
            existing_report = row.get('report', '') or ''
            updated_report = existing_report + f"\n\n## Follow-up Analysis\n\n**Question:** {question.strip()}\n\n{answer}\n"
            update_decision_status(
                decision_id,
                status='Completed',
                report=updated_report,
                error_message='',
                executive_status='Pending Executive Review',
            )
            (OUTPUT_DIR / f'{decision_id}.md').write_text(updated_report, encoding='utf-8')
            st.success('Follow-up analysis completed.')
            st.markdown('### Follow-up Analysis')
            with st.container(border=True):
                st.markdown(answer)
            st.caption('This follow-up used the existing decision context and did not re-run the full 9-agent analysis.')
        except Exception as exc:
            update_decision_status(decision_id, status='Failed', error_message=str(exc), executive_status='Pending Executive Review')
            st.error('The follow-up analysis failed.')
            st.code(str(exc), language='text')
