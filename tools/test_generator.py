
import ast
from pathlib import Path

from tools.file_reader import read_file


TEST_FRAMEWORKS = {
    ".py": "pytest",
    ".cpp": "Google Test (GTest)",
    ".cxx": "Google Test (GTest)",
    ".cc": "Google Test (GTest)",
    ".java": "JUnit 5"
}


PYTHON_TEST_RULES = """
STRICT PYTHON TEST GENERATION RULES:

1. Generate ONLY pytest test code.
2. Import production functions from their existing source module.
3. Use the exact required import statement provided below.
4. Do not redefine production functions. Never copy or reimplement them.
5. NEVER include production function implementations in the test file.
6. Define only pytest test functions whose names begin with test_.
7. Use the actual source implementation to determine expected results.
8. Cover normal cases, edge cases, and relevant exceptions.
9. Do not invent exceptions, APIs, or behavior not present in the source.
10. Use pytest.raises only when the source raises an exception.
11. Include all necessary imports.
12. Return one complete executable Python code block.

IMPORTANT:
The generated tests must call the real imported production functions.

INCORRECT:
def reverse_string(text):
    return text[::-1]

CORRECT:
from examples.string_utils import reverse_string

def test_reverse_string():
    assert reverse_string("hello") == "olleh"

The incorrect example copies a production function.
The correct example imports and tests the existing function.
"""


def get_python_import_info(file_path: str, content: str):
    """Extract public top-level functions and create an import statement."""

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None, []

    functions = [
        node.name
        for node in tree.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        )
        and not node.name.startswith("_")
    ]

    # Normalize Windows paths before constructing the module name.
    normalized_path = file_path.replace("\\", "/")

    module_path = Path(normalized_path).with_suffix("")
    module_name = ".".join(module_path.parts)

    if not functions:
        return None, []

    import_statement = (
        f"from {module_name} import {', '.join(functions)}"
    )

    return import_statement, functions


def generate_unit_tests(file_path: str) -> str:
    """Read source code and prepare instructions for AI test generation."""

    extension = Path(file_path).suffix.lower()

    if extension not in TEST_FRAMEWORKS:
        return "Error: Unsupported file type for test generation."

    content = read_file(file_path)

    if content.startswith(
        ("Error:", "Access denied:", "File reading error:")
    ):
        return content

    framework = TEST_FRAMEWORKS[extension]

    python_requirements = ""

    if extension == ".py":
        import_statement, functions = get_python_import_info(
            file_path,
            content
        )

        if import_statement:
            python_requirements = (
                f"\n{PYTHON_TEST_RULES}\n"
                "\nSOURCE INFORMATION:\n"
                f"Source file: {file_path}\n"
                f"Available functions: {', '.join(functions)}\n\n"
                "MANDATORY IMPORT STATEMENT:\n"
                f"{import_statement}\n\n"
                "FINAL OUTPUT REQUIREMENTS:\n"
                "- Start the Python code with the necessary imports.\n"
                "- Include the mandatory source import statement exactly.\n"
                "- Test the actual imported functions.\n"
                "- Do not define functions with the same names as "
                "production functions.\n"
                "- Do not copy source implementations into tests.\n"
                "- Ensure assertions match actual source behavior.\n"
                "- Include normal and edge cases.\n"
                "- Include exception tests only when appropriate.\n"
                "- Return exactly one ```python code block.\n"
                "- Do not include explanations outside the code block.\n"
            )
        else:
            python_requirements = (
                f"\n{PYTHON_TEST_RULES}\n"
                "\nSOURCE INFORMATION:\n"
                f"Source file: {file_path}\n\n"
                "FINAL OUTPUT REQUIREMENTS:\n"
                "- Import existing source classes or functions correctly.\n"
                "- Never invent unavailable APIs.\n"
                "- Never copy source implementations into tests.\n"
                "- Return exactly one ```python code block.\n"
            )

    return (
        f"Generate unit tests for: {file_path}\n"
        f"Framework: {framework}\n\n"
        "GENERAL REQUIREMENTS:\n"
        "- Cover normal inputs, edge cases, and failure scenarios.\n"
        "- Do not invent unavailable APIs or dependencies.\n"
        "- For C++ GTest, use ASSERT_* assertions.\n"
        "- For C++ GTest, do not use GoogleMock or EXPECT_CALL.\n"
        "- Prefer Given_When_Then style test names.\n"
        "- Include all required imports for the source functions.\n"
        "- Generate complete executable test files.\n"
        "- Do not use undefined functions or variables.\n"
        "- Do not claim tests passed unless they were executed.\n"
        f"{python_requirements}\n"
        "SOURCE CODE FOR REFERENCE ONLY:\n"
        "The following code is the existing production implementation.\n"
        "Read it to understand behavior, but DO NOT copy its "
        "function definitions into the generated tests.\n\n"
        f"{content}\n"
    )
