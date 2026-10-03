from dataclasses import dataclass

@dataclass
class DecisionRecord:
    decision_id: str
    title: str
    objective: str
    status: str
    created_at: str
    report: str = ""
