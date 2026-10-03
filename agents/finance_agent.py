from .base import make_agent

def create():
    return make_agent("Financial Analyst", "Assess the financial implications, economics, assumptions, costs, benefits, ROI and payback of the decision.", "You are a careful corporate finance analyst. Show assumptions clearly and flag figures that require validation.")
