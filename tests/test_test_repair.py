
from unittest.mock import patch

from tools.test_repair import (
    generate_test_repair,
    validate_test_repair,
)


# ============================================================
# AI TEST REPAIR GENERATION TESTS
# ============================================================


def test_GivenInvalidSource_WhenRepairing_ThenRejected():
    result = generate_test_repair(
        "tools/test_runner.py",
        "test_ai_string_utils.py",
        "AssertionError",
    )

    assert result["status"] == "error"


def test_GivenInvalidFilename_WhenRepairing_ThenRejected():
    result = generate_test_repair(
        "examples/string_utils.py",
        "../test_invalid.py",
        "AssertionError",
    )

    assert result["status"] == "error"


def test_GivenMissingTest_WhenRepairing_ThenRejected():
    result = generate_test_repair(
        "examples/string_utils.py",
        "test_file_does_not_exist.py",
        "AssertionError",
    )

    assert result["status"] == "error"


def test_GivenEmptyFailure_WhenRepairing_ThenRejected():
    result = generate_test_repair(
        "examples/string_utils.py",
        "test_ai_string_utils.py",
        "",
    )

    assert result["status"] == "error"


@patch("tools.test_repair.chat")
def test_GivenFailure_WhenRepairing_ThenAIProposalReturned(mock_chat):
    mock_chat.return_value = {
        "message": {
            "content": (
                "```python\n"
                "from examples.string_utils import is_palindrome\n\n"
                "def test_is_palindrome():\n"
                "    assert is_palindrome('abba') is True\n"
                "```"
            )
        }
    }

    result = generate_test_repair(
        "examples/string_utils.py",
        "test_ai_string_utils.py",
        "AssertionError: False != True",
    )

    assert result["status"] == "success"
    assert "assert is_palindrome('abba') is True" in result["output"]
    mock_chat.assert_called_once()


# ============================================================
# AI TEST REPAIR VALIDATION TESTS
# ============================================================



def test_GivenValidRepair_WhenValidating_ThenAccepted():
    response = """```python
from examples.string_utils import reverse_string, is_palindrome

def test_reverse_string():
    assert reverse_string("hello") == "olleh"

def test_is_palindrome():
    assert is_palindrome("abba") is True
```"""

    result = validate_test_repair(
        response,
        "examples/string_utils.py",
    )

    assert result["valid"] is True, result["errors"]
    assert result["errors"] == []
    assert result["code"] is not None



def test_GivenMissingImport_WhenValidatingRepair_ThenRejected():
    response = """```python
def test_is_palindrome():
    assert is_palindrome("abba") is True
```"""

    result = validate_test_repair(
        response,
        "examples/string_utils.py",
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_GivenMultipleBlocks_WhenValidatingRepair_ThenRejected():
    response = """```python
def test_one():
    assert True
```

```python
def test_two():
    assert True
```"""

    result = validate_test_repair(
        response,
        "examples/string_utils.py",
    )

    assert result["valid"] is False
    assert result["code"] is None


def test_GivenProductionRedefinition_WhenValidatingRepair_ThenRejected():
    response = """```python
from examples.string_utils import reverse_string, is_palindrome

def reverse_string(text):
    return text[::-1]

def test_reverse_string():
    assert reverse_string("abc") == "cba"
```"""

    result = validate_test_repair(
        response,
        "examples/string_utils.py",
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
