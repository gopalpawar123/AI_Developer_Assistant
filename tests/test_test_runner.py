
from unittest.mock import patch
from tools.test_runner import run_generated_tests


def test_GivenNoApproval_WhenRunningTests_ThenExecutionRejected():
    result = run_generated_tests("test_ai_calculator.py")

    assert result["status"] == "rejected"


def test_GivenInvalidFilename_WhenRunningTests_ThenErrorReturned():
    result = run_generated_tests("../test_invalid.py", approved=True)

    assert result["status"] == "error"


def test_GivenMissingFile_WhenRunningTests_ThenErrorReturned():
    result = run_generated_tests(
        "test_file_does_not_exist.py",
        approved=True
    )

    assert result["status"] == "error"


@patch("tools.test_runner.subprocess.run")
def test_GivenSuccessfulDockerExecution_WhenRunningTests_ThenPassed(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "3 passed"
    mock_run.return_value.stderr = ""

    result = run_generated_tests(
        "test_ai_calculator.py",
        approved=True
    )

    assert result["status"] == "passed"
    assert result["returncode"] == 0
    assert "3 passed" in result["output"]
    mock_run.assert_called_once()
