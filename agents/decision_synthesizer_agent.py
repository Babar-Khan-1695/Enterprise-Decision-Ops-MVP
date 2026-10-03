from .base import make_agent
from config.settings import SYNTHESIZER_MAX_TOKENS


def create():
    return make_agent(
        "Executive Decision Synthesizer",
        "Synthesize specialist findings into a concise, balanced, evidence-grounded executive decision brief.",
        "You are a senior strategy executive. Preserve uncertainty and disagreement. Never invent missing facts.",
        max_tokens=SYNTHESIZER_MAX_TOKENS,
    )
