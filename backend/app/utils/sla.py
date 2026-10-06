from datetime import datetime, timedelta, timezone


SLA_HOURS = {
    "critical": 1,
    "high": 4,
    "medium": 12,
    "low": 24
}


def calculate_sla_deadline(priority: str):
    hours = SLA_HOURS.get(priority)

    if hours is None:
        return None

    return datetime.now(timezone.utc) + timedelta(
        hours=hours
    )