import re
import time

from config.agent_config import AGENT_NAMES
from config.settings import AGENT_DELAY_SECONDS, MAX_RETRIES, RETRY_BASE_SECONDS


def task_statuses(completed_count):
    result = []
    for i, name in enumerate(AGENT_NAMES):
        if i < completed_count:
            status = "complete"
        elif i == completed_count:
            status = "working"
        else:
            status = "pending"
        result.append({"name": name, "status": status})
    return result


def is_rate_limit_error(exc):
    text = str(exc).lower()
    return any(term in text for term in ["ratelimit", "rate limit", "tokens per minute", "rate_limit_exceeded"])


def rate_limit_wait_seconds(exc, default=RETRY_BASE_SECONDS):
    match = re.search(r"try again in\s+([0-9]+(?:\.[0-9]+)?)s", str(exc), re.I)
    if match:
        return max(default, int(float(match.group(1))) + 2)
    return default


def paced_sleep(seconds=AGENT_DELAY_SECONDS):
    if seconds > 0:
        time.sleep(seconds)
