from .base import make_agent

def create():
    return make_agent("Executive Decision Synthesizer", "Synthesize all specialist findings into a balanced, evidence-grounded executive decision brief with alternatives, risks, assumptions and next steps.", "You are a senior strategy executive. You do not hide disagreement or uncertainty and you never claim certainty unsupported by evidence.")
