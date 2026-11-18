
from unittest.mock import patch

import app

import pytest


@pytest.fixture(autouse=True)
def isolate_repair_history():
    """Prevent integration tests from writing to real repair history."""
    with patch("app.record_repair_history"):
        yield


@pytest.fixture(autouse=True)
def isolated_generated_tests(tmp_path, monkeypatch):
    """Give repair tests safe, real files without touching the project."""
    monkeypatch.setattr(app, "PROJECT_ROOT", tmp_path)
    generated = tmp_path / "generated_tests"
    generated.mkdir()
    original = (
        "def test_example():\n"
        "    assert 1 == 1\n"
    )
    for name in (
        "test_ai_calculator.py",
        "test_example.py",
        "test_example_repaired.py",
    ):
        (generated / name).write_text(original, encoding="utf-8")


def test_GivenRepairDeclined_WhenHandlingFailure_ThenNoGeneration():
    with (
        patch("builtins.input", return_value="no"),
        patch("app.generate_test_repair") as generate,
        patch("app.save_approved_repair") as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_ai_calculator.py",
            "examples/calculator.py",
            "AssertionError",
        )

        generate.assert_not_called()
        save.assert_not_called()
        execute.assert_not_called()


def test_GivenSaveDeclined_WhenRepairValid_ThenNotSaved():
    with (
        patch("builtins.input", side_effect=["yes", "no"]),
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": "```python\ndef test_example(): assert True\n```",
            },
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": "def test_example(): assert True\n",
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old assertion\n+ new assertion",
            },
        ),
        patch("app.save_approved_repair") as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_ai_calculator.py",
            "examples/calculator.py",
            "AssertionError",
        )

        save.assert_not_called()
        execute.assert_not_called()


def test_GivenExecutionDeclined_WhenRepairSaved_ThenNotExecuted():
    with (
        patch("builtins.input", side_effect=["yes", "yes", "no"]),
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": "```python\ndef test_example(): assert True\n```",
            },
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": "def test_example(): assert True\n",
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old assertion\n+ new assertion",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "output": "Saved successfully",
                "filename": "test_ai_calculator_repaired.py",
            },
        ) as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_ai_calculator.py",
            "examples/calculator.py",
            "AssertionError",
        )

        save.assert_called_once()
        execute.assert_not_called()


def test_GivenAllApprovals_WhenRepairValid_ThenDockerExecuted():
    with (
        patch("builtins.input", side_effect=["yes", "yes", "yes"]),
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": "```python\ndef test_example(): assert True\n```",
            },
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": "def test_example(): assert True\n",
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old assertion\n+ new assertion",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "output": "Saved successfully",
                "filename": "test_ai_calculator_repaired.py",
            },
        ),
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "passed",
                "output": "1 passed",
            },
        ) as execute,
    ):
        app.handle_test_repair(
            "test_ai_calculator.py",
            "examples/calculator.py",
            "AssertionError",
        )

        execute.assert_called_once_with(
            "test_ai_calculator_repaired.py",
            "examples/calculator.py",
            approved=True,
        )

def test_GivenFirstRepairFails_WhenSecondRepairPasses_ThenStopRetrying():
    with (
        patch("builtins.input", side_effect=[
            "yes",  # Initial repair
            "yes",  # Save first repair
            "yes",  # Execute first repair
            "yes",  # Retry approval
            "yes",  # Save second repair
            "yes",  # Execute second repair
        ]) as approval,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": "```python\ndef test_example(): assert True\n```",
            },
        ) as generate,
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": "def test_example(): assert True\n",
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            side_effect=[
                {
                    "status": "success",
                    "filename": "test_example_repaired.py",
                },
                {
                    "status": "success",
                    "filename": "test_example_repaired_repaired.py",
                },
            ],
        ) as save,
        patch(
            "app.execute_approved_repair",
            side_effect=[
                {"status": "failed", "output": "First repair failed"},
                {"status": "passed", "output": "2 passed"},
            ],
        ) as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "Original failure",
        )

        assert generate.call_count == 2
        assert save.call_count == 2
        assert execute.call_count == 2
        assert approval.call_count == 6

        generate.assert_any_call(
            "examples/calculator.py",
            "test_example_repaired.py",
            "First repair failed",
        )

        execute.assert_any_call(
            "test_example_repaired_repaired.py",
            "examples/calculator.py",
            approved=True,
        )


def test_GivenBothRepairsFail_WhenLimitReached_ThenNoThirdAttempt():
    with (
        patch("builtins.input", side_effect=[
            "yes", "yes", "yes",
            "yes", "yes", "yes",
        ]) as approval,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": "```python\ndef test_example(): assert True\n```",
            },
        ) as generate,
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": "def test_example(): assert True\n",
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            side_effect=[
                {"status": "success", "filename": "test_example_repaired.py"},
                {"status": "success", "filename": "test_example_repaired_repaired.py"},
            ],
        ) as save,
        patch(
            "app.execute_approved_repair",
            side_effect=[
                {"status": "failed", "output": "Failure 1"},
                {"status": "failed", "output": "Failure 2"},
            ],
        ) as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "Original failure",
        )

        assert generate.call_count == 2
        assert save.call_count == 2
        assert execute.call_count == 2
        assert approval.call_count == 6


def test_GivenFirstRepairFails_WhenRetryDeclined_ThenStop():
    with (
        patch("builtins.input", side_effect=[
            "yes",  # Initial approval
            "yes",  # Save
            "yes",  # Execute
            "no",   # Decline second attempt
        ]),
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": "```python\ndef test_example(): assert True\n```",
            },
        ) as generate,
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": "def test_example(): assert True\n",
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "repair1.py",
            },
        ) as save,
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "failed",
                "output": "Still failing",
            },
        ) as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "Original failure",
        )

        generate.assert_called_once()
        save.assert_called_once()
        execute.assert_called_once()

def test_GivenWeakAIRepair_WhenQualityValidationRuns_ThenNotSavedOrExecuted(capsys):
    """Reject a meaningless assertion before any save or Docker execution."""
    weak_response = "```python\ndef test_example():\n    assert True\n```"

    with (
        patch("builtins.input", return_value="yes") as approval,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": weak_response},
        ) as generate,
        patch("app.generate_repair_diff") as diff,
        patch("app.save_approved_repair") as save,
        patch("app.execute_approved_repair") as execute,
    ):
        # Deliberately do NOT mock app.validate_test_repair.
        app.handle_test_repair(
            "test_example.py", "examples/calculator.py", "AssertionError"
        )

    output = capsys.readouterr().out
    assert "Repair validation failed." in output
    generate.assert_called_once()
    approval.assert_called_once()
    diff.assert_not_called()
    save.assert_not_called()
    execute.assert_not_called()


def test_GivenQualityWarningsDeclined_WhenRepairValid_ThenNotSavedOrExecuted(capsys):
    """A coverage warning requires separate explicit consent before saving."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"
    with (
        patch("builtins.input", side_effect=["yes", "no"]) as approval,
        patch("app.generate_test_repair", return_value={"status": "success", "output": repaired_code}),
        patch("app.validate_test_repair", return_value={
            "valid": True, "code": repaired_code, "errors": [],
            "warnings": ["Assertion count decreased"],
        }),
        patch("app.generate_repair_diff", return_value={
            "status": "success", "changed": True, "diff": "- old\n+ new",
        }) as diff,
        patch("app.save_approved_repair") as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair("test_example.py", "examples/calculator.py", "AssertionError")

    assert "Repair rejected due to quality warnings." in capsys.readouterr().out
    assert approval.call_count == 2
    assert "quality warnings" in approval.call_args_list[1].args[0]
    diff.assert_called_once()
    save.assert_not_called()
    execute.assert_not_called()


def test_GivenQualityWarningsAccepted_WhenAllApprovalsGiven_ThenDockerExecuted():
    """Warning acceptance is distinct from save and execution approvals."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"
    with (
        patch("builtins.input", side_effect=["yes", "yes", "yes", "yes"]) as approval,
        patch("app.generate_test_repair", return_value={"status": "success", "output": repaired_code}),
        patch("app.validate_test_repair", return_value={
            "valid": True, "code": repaired_code, "errors": [],
            "warnings": ["Assertion count decreased"],
        }),
        patch("app.generate_repair_diff", return_value={
            "status": "success", "changed": True, "diff": "- old\n+ new",
        }),
        patch("app.save_approved_repair", return_value={
            "status": "success", "output": "Saved successfully",
            "filename": "test_example_repaired.py",
        }) as save,
        patch("app.execute_approved_repair", return_value={
            "status": "passed", "output": "1 passed",
        }) as execute,
    ):
        app.handle_test_repair("test_example.py", "examples/calculator.py", "AssertionError")

    assert approval.call_count == 4
    assert "quality warnings" in approval.call_args_list[1].args[0]
    save.assert_called_once_with("test_example.py", repaired_code, approved=True)
    execute.assert_called_once_with(
        "test_example_repaired.py", "examples/calculator.py", approved=True
    )


def test_GivenNoQualityWarnings_WhenRepairValid_ThenNoExtraApproval():
    """The warning gate must not affect repairs with no quality warnings."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"
    with (
        patch("builtins.input", side_effect=["yes", "yes", "no"]) as approval,
        patch("app.generate_test_repair", return_value={"status": "success", "output": repaired_code}),
        patch("app.validate_test_repair", return_value={
            "valid": True, "code": repaired_code, "errors": [], "warnings": [],
        }),
        patch("app.generate_repair_diff", return_value={
            "status": "success", "changed": True, "diff": "- old\n+ new",
        }),
        patch("app.save_approved_repair", return_value={
            "status": "success", "output": "Saved successfully",
            "filename": "test_example_repaired.py",
        }) as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair("test_example.py", "examples/calculator.py", "AssertionError")

    assert approval.call_count == 3
    assert all("quality warnings" not in call.args[0] for call in approval.call_args_list)
    save.assert_called_once()
    execute.assert_not_called()


def test_GivenRepairStarted_WhenHandlingFailure_ThenHistoryRecorded():
    """Verify repair-start logging without writing to real history."""

    with (
        patch("builtins.input", side_effect=["yes"]),
        patch(
            "app.record_repair_history"
        ) as history,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "error",
                "output": "Simulated generation failure",
            },
        ),
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_called_once_with(
        filename="test_example.py",
        event="repair_attempt_started",
        status="started",
        details={
            "attempt": 1,
            "max_attempts": 2,
        },
    )

def test_GivenInvalidRepair_WhenValidationFails_ThenHistoryRecorded():
    """Verify failed repair validation is recorded in history."""

    repaired_code = "def test_example():\n    assert False\n"

    with (
        patch("builtins.input", side_effect=["yes"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": repaired_code,
            },
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": False,
                "code": None,
                "errors": ["Invalid assertion"],
                "warnings": [],
            },
        ),
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example.py",
        event="repair_validation",
        status="failed",
        warnings=[],
        details={
            "attempt": 1,
            "error_count": 1,
        },
    )

def test_GivenValidRepairWithWarnings_WhenValidated_ThenHistoryRecorded():
    """Verify successful validation and warnings are recorded."""

    repaired_code = "def test_example():\n    assert 2 == 2\n"
    warnings = ["Assertion count decreased"]

    with (
        patch("builtins.input", side_effect=["yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": repaired_code,
            },
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": warnings,
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example.py",
        event="repair_validation",
        status="passed",
        warnings=warnings,
        details={
            "attempt": 1,
            "error_count": 0,
        },
    )

def test_GivenQualityWarningsRejected_WhenRepairValid_ThenRejectionLogged():
    """Verify rejected quality warnings are recorded."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"
    warnings = ["Assertion count decreased"]

    with (
        patch("builtins.input", side_effect=["yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": warnings,
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch("app.save_approved_repair") as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example.py",
        event="quality_warning_approval",
        status="rejected",
        warnings=warnings,
        details={"attempt": 1},
    )
    save.assert_not_called()
    execute.assert_not_called()


def test_GivenQualityWarningsAccepted_WhenRepairValid_ThenAcceptanceLogged():
    """Verify accepted quality warnings are recorded."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"
    warnings = ["Assertion count decreased"]

    with (
        patch("builtins.input", side_effect=["yes", "yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": warnings,
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch("app.save_approved_repair") as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example.py",
        event="quality_warning_approval",
        status="accepted",
        warnings=warnings,
        details={"attempt": 1},
    )
    save.assert_not_called()
    execute.assert_not_called()

def test_GivenSaveRejected_WhenRepairValid_ThenRejectionLogged():
    """Verify declining to save a repair is recorded."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch("app.save_approved_repair") as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example.py",
        event="repair_save_approval",
        status="rejected",
        details={"attempt": 1},
    )
    save.assert_not_called()
    execute.assert_not_called()


def test_GivenSaveApproved_WhenRepairValid_ThenApprovalLogged():
    """Verify approving a repair save is recorded."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ) as save,
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example.py",
        event="repair_save_approval",
        status="approved",
        details={"attempt": 1},
    )
    save.assert_called_once_with(
        "test_example.py",
        repaired_code,
        approved=True,
    )
    execute.assert_not_called()

def test_GivenDockerRejected_WhenRepairSaved_ThenRejectionLogged():
    """Verify rejecting Docker execution is recorded."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ),
        patch("app.execute_approved_repair") as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example_repaired.py",
        event="repair_docker_approval",
        status="rejected",
        details={"attempt": 1},
    )
    execute.assert_not_called()


def test_GivenDockerApproved_WhenRepairSaved_ThenApprovalLogged():
    """Verify approving Docker execution is recorded."""
    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "yes", "yes"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ),
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "passed",
                "output": "1 passed",
            },
        ) as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example_repaired.py",
        event="repair_docker_approval",
        status="approved",
        details={"attempt": 1},
    )
    execute.assert_called_once_with(
        "test_example_repaired.py",
        "examples/calculator.py",
        approved=True,
    )

def test_GivenDockerExecutionPassed_WhenRepairRuns_ThenResultLogged():
    """Verify successful Docker execution is recorded in history."""

    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "yes", "yes"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": repaired_code,
            },
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ),
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "passed",
                "output": "1 passed",
            },
        ),
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example_repaired.py",
        event="repair_docker_execution",
        status="passed",
        details={"attempt": 1},
    )

def test_GivenDockerExecutionFailed_WhenRepairRuns_ThenResultLogged():
    """Verify failed Docker execution is recorded."""

    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "yes", "yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ),
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "failed",
                "output": "AssertionError",
            },
        ),
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example_repaired.py",
        event="repair_docker_execution",
        status="failed",
        details={"attempt": 1},
    )


def test_GivenDockerExecutionTimeout_WhenRepairRuns_ThenResultLogged():
    """Verify Docker execution timeout is recorded."""

    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "yes", "yes"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={"status": "success", "output": repaired_code},
        ),
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ),
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "timeout",
                "output": "Execution timed out",
            },
        ),
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example_repaired.py",
        event="repair_docker_execution",
        status="timeout",
        details={"attempt": 1},
    )

def test_GivenRetryRejected_WhenDockerFails_ThenRejectionLogged():
    """Verify rejected retry is logged and no second attempt starts."""

    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch("builtins.input", side_effect=["yes", "yes", "yes", "no"]),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": repaired_code,
            },
        ) as generate,
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ),
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "failed",
                "output": "AssertionError",
            },
        ),
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example_repaired.py",
        event="repair_retry_approval",
        status="rejected",
        details={
            "attempt": 1,
            "next_attempt": 2,
        },
    )

    generate.assert_called_once()

def test_GivenRetryApproved_WhenDockerFailsTwice_ThenMaximumAttemptsEnforced():
    """Verify an approved retry runs once and stops after two attempts."""

    repaired_code = "def test_example():\n    assert 2 == 2\n"

    with (
        patch(
            "builtins.input",
            side_effect=["yes", "yes", "yes", "yes", "yes", "yes", "yes"],
        ),
        patch("app.record_repair_history") as history,
        patch(
            "app.generate_test_repair",
            return_value={
                "status": "success",
                "output": repaired_code,
            },
        ) as generate,
        patch(
            "app.validate_test_repair",
            return_value={
                "valid": True,
                "code": repaired_code,
                "errors": [],
                "warnings": [],
            },
        ),
        patch(
            "app.generate_repair_diff",
            return_value={
                "status": "success",
                "changed": True,
                "diff": "- old\n+ new",
            },
        ),
        patch(
            "app.save_approved_repair",
            return_value={
                "status": "success",
                "filename": "test_example_repaired.py",
                "output": "Saved successfully",
            },
        ),
        patch(
            "app.execute_approved_repair",
            return_value={
                "status": "failed",
                "output": "AssertionError",
            },
        ) as execute,
    ):
        app.handle_test_repair(
            "test_example.py",
            "examples/calculator.py",
            "AssertionError",
        )

    history.assert_any_call(
        filename="test_example_repaired.py",
        event="repair_retry_approval",
        status="approved",
        details={
            "attempt": 1,
            "next_attempt": 2,
        },
    )

    assert generate.call_count == 2
    assert execute.call_count == 2

    started_attempts = [
        call.kwargs["details"]["attempt"]
        for call in history.call_args_list
        if call.kwargs.get("event") == "repair_attempt_started"
    ]
    assert started_attempts == [1, 2]
