
import json

import pytest

from tools.repair_history import log_repair_event


def test_creates_history_file(tmp_path):
    history_file = tmp_path / "logs" / "repair_history.json"

    record = log_repair_event(
        filename="test_example.py",
        event="repair_proposed",
        status="success",
        history_file=history_file,
    )

    assert history_file.exists()

    history = json.loads(history_file.read_text(encoding="utf-8"))
    assert len(history) == 1
    assert history[0] == record
    assert record["filename"] == "test_example.py"
    assert record["event"] == "repair_proposed"
    assert record["status"] == "success"
    assert record["timestamp"]


def test_appends_multiple_events(tmp_path):
    history_file = tmp_path / "repair_history.json"

    log_repair_event(
        "test_example.py",
        "repair_proposed",
        "success",
        history_file=history_file,
    )

    log_repair_event(
        "test_example.py",
        "repair_approved",
        "approved",
        warnings=["Reduced assertion count"],
        details={"attempt": 1},
        history_file=history_file,
    )

    history = json.loads(history_file.read_text(encoding="utf-8"))

    assert len(history) == 2
    assert history[1]["warnings"] == ["Reduced assertion count"]
    assert history[1]["details"]["attempt"] == 1


@pytest.mark.parametrize(
    "filename,event,status",
    [
        ("", "repair_proposed", "success"),
        ("test_example.py", "", "success"),
        ("test_example.py", "repair_proposed", ""),
    ],
)
def test_rejects_empty_required_fields(tmp_path, filename, event, status):
    history_file = tmp_path / "repair_history.json"

    with pytest.raises(ValueError):
        log_repair_event(
            filename,
            event,
            status,
            history_file=history_file,
        )

    assert not history_file.exists()


def test_rejects_invalid_warnings(tmp_path):
    with pytest.raises(ValueError, match="Warnings"):
        log_repair_event(
            "test_example.py",
            "repair_proposed",
            "success",
            warnings="not a list",
            history_file=tmp_path / "history.json",
        )


def test_rejects_invalid_details(tmp_path):
    with pytest.raises(ValueError, match="Details"):
        log_repair_event(
            "test_example.py",
            "repair_proposed",
            "success",
            details="invalid",
            history_file=tmp_path / "history.json",
        )


def test_rejects_invalid_history_format(tmp_path):
    history_file = tmp_path / "repair_history.json"
    history_file.write_text('{"unexpected": "object"}', encoding="utf-8")

    with pytest.raises(ValueError, match="JSON list"):
        log_repair_event(
            "test_example.py",
            "repair_proposed",
            "success",
            history_file=history_file,
        )
