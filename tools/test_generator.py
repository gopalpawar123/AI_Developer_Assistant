
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


def get_python_import_info(file_path: str, content: str):
    """Find top-level Python functions and build an import statement."""

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None, []

    functions = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]

    module_path = Path(file_path).with_suffix("")
    module_name = ".".join(module_path.parts)

    if not functions:
        return None, []

    import_statement = (
        f"from {module_name} import {', '.join(functions)}"
    )

    return import_statement, functions


def generate_unit_tests(file_path: str) -> str:
    """Read source code and prepare AI unit test instructions."""

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
                "\nPython source information:\n"
                f"Available functions: {', '.join(functions)}\n"
                f"Required import statement:\n"
                f"{import_statement}\n\n"
                "Python-specific requirements:\n"
                "- Include the required import statement exactly.\n"
                "- Import functions from the existing source module.\n"
                "- Do not redefine production functions in tests.\n"
                "- Use pytest.raises for expected exceptions.\n"
                "- Generate standalone executable pytest tests.\n"
                "- Return the complete tests inside one ```python code block.\n"
            )
        else:
            python_requirements = (
                "\nPython-specific requirements:\n"
                "- Import the existing source module or classes correctly.\n"
                "- Do not invent functions that are not in the source.\n"
                "- Return the complete tests inside one ```python code block.\n"
            )

    return (
        f"Generate unit tests for: {file_path}\n"
        f"Framework: {framework}\n\n"
        "Requirements:\n"
        "- Cover normal inputs, edge cases, and failure scenarios.\n"
        "- Do not invent unavailable APIs or dependencies.\n"
        "- For C++ GTest, use ASSERT_* assertions.\n"
        "- For C++ GTest, do not use GoogleMock or EXPECT_CALL.\n"
        "- Prefer Given_When_Then style test names.\n"
        "- Include all required imports for the source functions.\n"
        "- Generate complete, executable test files.\n"
        "- Do not use undefined functions or variables.\n"
        "- Do not claim tests passed unless they were executed.\n"
        f"{python_requirements}\n"
        f"Source code:\n{content}"
    )
