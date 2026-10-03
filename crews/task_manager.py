def task_statuses(names, completed_count):
    return [{"name": name, "status": "complete" if i < completed_count else "pending"} for i, name in enumerate(names)]
