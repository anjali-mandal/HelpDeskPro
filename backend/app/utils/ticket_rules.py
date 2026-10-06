VALID_STATUSES = [
    "open",
    "assigned",
    "in_progress",
    "resolved",
    "closed"
]


VALID_PRIORITIES = [
    "low",
    "medium",
    "high",
    "critical"
]


ALLOWED_STATUS_TRANSITIONS = {

    "open": [
        "assigned"
    ],

    "assigned": [
        "in_progress"
    ],

    "in_progress": [
        "resolved"
    ],

    "resolved": [
        "closed",
        "in_progress"
    ],

    "closed": []

}


def is_valid_status(status: str):

    return status in VALID_STATUSES


def is_valid_priority(priority: str):

    return priority in VALID_PRIORITIES


def can_change_status(
    current_status: str,
    new_status: str
):

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
        current_status,
        []
    )

    return new_status in allowed_statuses



