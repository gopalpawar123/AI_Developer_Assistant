
from unittest.mock import patch

from tools.result_analyzer import analyze_test_result


def test_GivenPassedTests_WhenAnalyzing_ThenNoLLMRequired():
    result = analyze_test_result({
        "status": "passed",
        "output": "3 passed"
    })

    assert "All tests passed" in result


def test_GivenRejectedExecution_WhenAnalyzing_ThenRejectedMessage():
    result = analyze_test_result({
        "status": "rejected",
        "output": "Approval required"
    })

    assert "not approved" in result


@patch("tools.result_analyzer.get_ai_response")
def test_GivenFailedTests_WhenAnalyzing_ThenLLMExplainsFailure(mock_llm):
    mock_llm.return_value = "Division by zero caused the failure."

    result = analyze_test_result({
        "status": "failed",
        "output": "ZeroDivisionError: division by zero"
    })

    assert "Division by zero" in result
    mock_llm.assert_called_once()


def test_GivenEmptyFailureOutput_WhenAnalyzing_ThenErrorMessage():
    result = analyze_test_result({
        "status": "failed",
        "output": ""
    })

    assert "no error output" in result
