import os

# CrewAI 1.15.x can inject the provider-specific `cache_breakpoint`
# field into messages sent through the LiteLLM path. Groq rejects that
# field, so disable the marker before creating any LLM instances.
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass

from crewai import Agent, LLM
from config.settings import (
    AGENT_MAX_TOKENS,
    AGENT_TEMPERATURE,
    GROQ_MODEL,
    SYNTHESIZER_MAX_TOKENS,
)


def get_llm(max_tokens=None):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to Streamlit Secrets or your environment.")
    return LLM(
        model=GROQ_MODEL,
        api_key=key,
        temperature=AGENT_TEMPERATURE,
        max_tokens=max_tokens or AGENT_MAX_TOKENS,
    )


def make_agent(role, goal, backstory, max_tokens=None):
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=get_llm(max_tokens=max_tokens),
        verbose=False,
        allow_delegation=False,
    )
