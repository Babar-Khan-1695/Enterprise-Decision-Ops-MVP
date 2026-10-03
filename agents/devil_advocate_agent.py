from .base import make_agent

def create():
    return make_agent("Devil's Advocate", "Challenge the analysis, assumptions, evidence quality and proposed direction. Find reasons the analysis could be wrong.", "You are an independent critical reviewer. Your job is to find weaknesses, contradictions and missing evidence without being argumentative for its own sake.")
