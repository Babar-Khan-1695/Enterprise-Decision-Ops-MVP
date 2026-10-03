import os
from crewai import Agent, LLM
from config.settings import GROQ_MODEL


def get_llm():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to Streamlit Secrets or your environment.")
    return LLM(model=GROQ_MODEL, api_key=key, temperature=0.2)


def make_agent(role, goal, backstory):
    return Agent(role=role, goal=goal, backstory=backstory, llm=get_llm(), verbose=False, allow_delegation=False)
