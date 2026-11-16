from tools.code_analyzer import analyze_code
from tools.test_generator import generate_unit_tests


def test_analyze_python_file():
    result = analyze_code("examples/calculator.py")
    assert "def add" in result
    assert "def divide" in result


def test_generate_python_tests():
    result = generate_unit_tests("examples/calculator.py")
    assert "pytest" in result
    assert "def divide" in result


def test_reject_unsupported_file():
    result = analyze_code("README.md")
    assert "Unsupported" in result


def test_reject_sensitive_file():
    result = analyze_code("private.py")
    assert "does not exist" in result