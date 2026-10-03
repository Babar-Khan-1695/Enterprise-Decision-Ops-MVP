# Enterprise DecisionOps

A modular multi-agent enterprise decision-intelligence MVP built with Streamlit, CrewAI, Groq GPT-OSS 120B, FAISS, Sentence Transformers and SQLite.

## What it does

A manager submits a complex business decision. Nine specialized agents analyze it sequentially from orchestration, research, finance, operations, risk, compliance, scenario and critical-review perspectives. A final synthesizer produces an Executive Decision Brief.

## Runtime behavior

- Agents execute **sequentially**, not concurrently.
- Specialist outputs are deliberately capped to reduce token consumption.
- A pacing delay is applied between agent tasks to reduce Groq TPM pressure.
- CrewAI `max_rpm=4` is used when supported by the installed CrewAI version.
- Groq rate-limit failures are shown to the user and stored with the failed decision.
- The New Decision page shows the **currently working agent** and the final Completed/Failed state.
- The Executive Dashboard focuses on business decisions, not technical system status.
- Technical status is available in **System Health**.
- Completed decisions have a Markdown report download button.

## Stack

- Python 3.11
- Streamlit 1.65.0
- CrewAI 1.15.22
- Groq 1.7.0
- GPT-OSS 120B through Groq
- FAISS CPU 1.15.1
- Sentence Transformers 6.1.0
- SQLite (Python standard library)
- Pandas 3.0.6
- Plotly 7.1.0

## Run locally

1. Install Python 3.11.
2. Create a virtual environment.
3. Install `requirements.txt`.
4. Create `.streamlit/secrets.toml` with:

```toml
GROQ_API_KEY = "your_key"
```

5. Run:

```bash
streamlit run app.py
```

## Streamlit Cloud

Upload the repository to GitHub, select `app.py` as the main file, and add `GROQ_API_KEY` in Streamlit Cloud Secrets.

## Important

The application uses local SQLite and a local FAISS index for this MVP. Streamlit Cloud local storage is not guaranteed across rebuilds/redeployments. The Groq API key is never stored in the repository.
