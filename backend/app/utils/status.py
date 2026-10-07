VALID_STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
}


ALLOWED_TRANSITIONS = {
    "OPEN": {
        "IN_PROGRESS",
    },
    "IN_PROGRESS": {
        "RESOLVED",
        "OPEN",
    },
    "RESOLVED": {
        "CLOSED",
        "OPEN",
    },
    "CLOSED": set(),
}


def validate_status_transition(
    current_status: str,
    new_status: str,
) -> None:

    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {new_status}"
        )

    if current_status == new_status:
        raise ValueError(
            "Ticket is already in this status"
        )

    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid status transition: "
            f"{current_status} → {new_status}"
        )