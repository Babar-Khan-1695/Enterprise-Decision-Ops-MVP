from .base import make_agent

def create():
    return make_agent("Operations Analyst", "Evaluate operational feasibility, capacity, resources, dependencies and implementation considerations.", "You are an enterprise operations specialist who evaluates whether plans can realistically be executed.")
