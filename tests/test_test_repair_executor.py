
from tools import test_repair_executor


def test_GivenNoApproval_WhenExecuting_ThenRejected():
    result = test_repair_executor.execute_approved_repair(
        "test_sample_repaired.py",
        "examples/calculator.py",
        approved=False,
    )

    assert result["status"] == "rejected"


def test_GivenInvalidFilename_WhenExecuting_ThenRejected():
    result = test_repair_executor.execute_approved_repair(
        "../test_sample_repaired.py",
        "examples/calculator.py",
        approved=True,
    )

    assert result["status"] == "error"


def test_GivenNonRepairFilename_WhenExecuting_ThenRejected():
    result = test_repair_executor.execute_approved_repair(
        "test_sample.py",
        "examples/calculator.py",
        approved=True,
    )

    assert result["status"] == "error"


def test_GivenMissingRepair_WhenExecuting_ThenRejected(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        test_repair_executor,
        "ALLOWED_TEST_DIR",
        tmp_path,
    )

    result = test_repair_executor.execute_approved_repair(
        "test_missing_repaired.py",
        "examples/calculator.py",
        approved=True,
    )

    assert result["status"] == "error"


def test_GivenValidRepair_WhenExecuting_ThenDockerRunnerCalled(
    tmp_path, monkeypatch
):
    test_file = tmp_path / "test_sample_repaired.py"
    test_file.write_text(
        "def test_example(): assert True",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        test_repair_executor,
        "ALLOWED_TEST_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        test_repair_executor,
        "validate_source_path",
        lambda path: tmp_path / "calculator.py",
    )

    calls = []

    def fake_runner(filename, approved, source_path):
        calls.append((filename, approved, source_path))
        return {
            "status": "passed",
            "output": "1 passed",
        }

    monkeypatch.setattr(
        test_repair_executor,
        "run_generated_tests",
        fake_runner,
    )

    result = test_repair_executor.execute_approved_repair(
        "test_sample_repaired.py",
        "examples/calculator.py",
        approved=True,
    )

    assert result["status"] == "passed"
    assert calls == [
        (
            "test_sample_repaired.py",
            True,
            "examples/calculator.py",
        )
    ]


def test_GivenInvalidSource_WhenExecuting_ThenRejected(
    tmp_path, monkeypatch
):
    test_file = tmp_path / "test_sample_repaired.py"
    test_file.write_text(
        "def test_example(): assert True",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        test_repair_executor,
        "ALLOWED_TEST_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        test_repair_executor,
        "validate_source_path",
        lambda path: None,
    )

    result = test_repair_executor.execute_approved_repair(
        "test_sample_repaired.py",
        "../outside.py",
        approved=True,
    )

    assert result["status"] == "error"
