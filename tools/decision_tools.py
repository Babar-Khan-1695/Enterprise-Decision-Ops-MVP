from datetime import datetime
import uuid


def new_decision_id():
    return "DEC-" + datetime.utcnow().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()
