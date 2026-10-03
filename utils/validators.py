def validate_decision(title: str, objective: str):
    errors = []
    if not title.strip():
        errors.append("Decision title is required.")
    if len(objective.strip()) < 20:
        errors.append("Please provide a more detailed decision objective.")
    return errors
