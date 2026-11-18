
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = PROJECT_ROOT / "logs" / "repair_history.json"


def log_repair_event(
    filename,
    event,
    status,
    warnings=None,
    details=None,
    history_file=None,
):
    """Append an AI repair event to a local JSON history file."""

    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("A valid filename is required.")

    if not isinstance(event, str) or not event.strip():
        raise ValueError("A valid event is required.")

    if not isinstance(status, str) or not status.strip():
        raise ValueError("A valid status is required.")

    if warnings is None:
        warnings = []

    if not isinstance(warnings, list) or not all(
        isinstance(warning, str) for warning in warnings
    ):
        raise ValueError("Warnings must be a list of strings.")

    if details is not None and not isinstance(details, dict):
        raise ValueError("Details must be a dictionary.")

    path = Path(history_file) if history_file is not None else HISTORY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with path.open("r", encoding="utf-8") as file:
            history = json.load(file)

        if not isinstance(history, list):
            raise ValueError("Repair history must contain a JSON list.")
    else:
        history = []

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filename": filename,
        "event": event,
        "status": status,
        "warnings": warnings,
        "details": details or {},
    }

    history.append(record)

    with path.open("w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

    return record
