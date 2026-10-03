import json
import re
from datetime import datetime


def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_json(value):
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return {"raw": str(value)}
