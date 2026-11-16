
from tools.source_inspector import (
    extract_source_path,
    inspect_python_source
)


def test_GivenRequest_WhenExtractingPath_ThenCorrectPathReturned():
    request = "Generate pytest tests for examples/calculator.py"

    assert extract_source_path(request) == "examples/calculator.py"


def test_GivenWindowsPath_WhenExtractingPath_ThenNormalized():
    request = r"Generate tests for examples\calculator.py"

    assert extract_source_path(request) == "examples/calculator.py"


def test_GivenNoPath_WhenExtractingPath_ThenNoneReturned():
    assert extract_source_path("Generate pytest tests") is None


def test_GivenCalculator_WhenInspecting_ThenFunctionsDetected():
    result = inspect_python_source("examples/calculator.py")

    assert result["valid"] is True
    assert result["module"] == "examples.calculator"
    assert result["functions"] == ["add", "divide"]


def test_GivenMissingFile_WhenInspecting_ThenErrorReturned():
    result = inspect_python_source("examples/missing_module.py")

    assert result["valid"] is False
    assert result["error"] is not None
