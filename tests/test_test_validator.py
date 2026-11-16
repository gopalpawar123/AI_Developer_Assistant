
from tools.test_validator import validate_generated_test


def test_GivenValidCode_WhenValidating_ThenAccepted():
    code = """
import pytest
from examples.calculator import add, divide

def test_add():
    assert add(2, 3) == 5

def test_divide():
    assert divide(10, 2) == 5
"""

    result = validate_generated_test(
        code,
        required_imports=["add", "divide"]
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_GivenMissingImports_WhenValidating_ThenRejected():
    code = """
def test_add():
    assert add(2, 3) == 5
"""

    result = validate_generated_test(
        code,
        required_imports=["add"]
    )

    assert result["valid"] is False
    assert "Missing required import: add" in result["errors"]


def test_GivenInvalidSyntax_WhenValidating_ThenRejected():
    result = validate_generated_test("def test_broken(")

    assert result["valid"] is False
    assert "Invalid Python syntax" in result["errors"][0]


def test_GivenNoTests_WhenValidating_ThenRejected():
    result = validate_generated_test(
        "def helper():\n    return 10\n"
    )

    assert result["valid"] is False
    assert "No pytest test functions found." in result["errors"]


def test_GivenUndefinedName_WhenValidating_ThenWarningReturned():
    code = """
def test_example():
    assert missing_function() == 10
"""

    result = validate_generated_test(code)

    assert result["valid"] is True
    assert "Possibly undefined name: missing_function" in result["warnings"]


def test_GivenCorrectSourceModule_WhenValidating_ThenAccepted():
    code = """
from examples.calculator import add, divide

def test_add():
    assert add(2, 3) == 5
"""

    result = validate_generated_test(
        code,
        required_imports=["add", "divide"],
        source_module="examples.calculator"
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_GivenWrongSourceModule_WhenValidating_ThenRejected():
    code = """
from wrong_module import add, divide

def test_add():
    assert add(2, 3) == 5
"""

    result = validate_generated_test(
        code,
        required_imports=["add", "divide"],
        source_module="examples.calculator"
    )

    assert result["valid"] is False
    assert "Missing required import: add from examples.calculator" in result["errors"]
    assert "Missing required import: divide from examples.calculator" in result["errors"]

