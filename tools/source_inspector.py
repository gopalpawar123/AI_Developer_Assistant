
import ast
import re
from pathlib import Path

from tools.file_reader import read_file


SOURCE_PATTERN = re.compile(
    r"([\w./\\-]+\.py)\b",
    re.IGNORECASE
)


def extract_source_path(user_input: str):
    """Extract a Python source path from a user request."""
    match = SOURCE_PATTERN.search(user_input)

    if not match:
        return None

    return match.group(1).replace("\\", "/")


def inspect_python_source(file_path: str) -> dict:
    """Read and inspect a Python source file without executing it."""

    result = {
        "valid": False,
        "module": None,
        "functions": [],
        "error": None
    }

    if not file_path or not file_path.endswith(".py"):
        result["error"] = "Expected a Python source file."
        return result

    content = read_file(file_path)

    if content.startswith(
        ("Error:", "Access denied:", "File reading error:")
    ):
        result["error"] = content
        return result

    try:
        tree = ast.parse(content)
    except SyntaxError as error:
        result["error"] = f"Invalid source syntax: {error}"
        return result

    functions = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]

    module = ".".join(
        Path(file_path.replace("\\", "/")).with_suffix("").parts
    )

    result["valid"] = True
    result["module"] = module
    result["functions"] = functions

    return result
