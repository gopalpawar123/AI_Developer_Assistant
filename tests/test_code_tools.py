from tools.code_analyzer import analyze_code
from tools.test_generator import generate_unit_tests
from tools.test_generator import get_python_import_info


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

def test_GivenPythonFunctions_WhenExtractingImports_ThenCorrectImportGenerated():
    source = """
def add(a, b):
    return a + b

def divide(a, b):
    return a / b
"""

    import_statement, functions = get_python_import_info(
        "examples/calculator.py",
        source
    )

    assert import_statement == (
        "from examples.calculator import add, divide"
    )
    assert functions == ["add", "divide"]


def test_GivenPrivateFunction_WhenExtractingImports_ThenExcluded():
    source = """
def _helper():
    pass

def calculate():
    return 10
"""

    import_statement, functions = get_python_import_info(
        "examples/calculator.py",
        source
    )

    assert import_statement == (
        "from examples.calculator import calculate"
    )
    assert functions == ["calculate"]


def test_GivenCalculator_WhenGeneratingPrompt_ThenExplicitImportIncluded():
    result = generate_unit_tests("examples/calculator.py")

    assert (
        "from examples.calculator import add, divide"
        in result
    )
    assert "Do not redefine production functions" in result
