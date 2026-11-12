from datetime import UTC, date, datetime


def check_not_past(value: date | None) -> date | None:
    if value is not None and value < datetime.now(UTC).date():
        raise ValueError("due_date cannot be in the past")
    return value
