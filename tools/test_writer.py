
import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "generated_tests"


def save_generated_test(filename: str, code: str) -> str:
    """Validate and save generated Python test code without overwriting files."""

    if not filename.startswith("test_") or not filename.endswith(".py"):
        return "Error: Filename must start with test_ and end with .py."

    if Path(filename).name != filename or "\\" in filename or "/" in filename:
        return "Error: Only a filename is allowed, not a path."

    if not code.strip():
        return "Error: Generated code is empty."

    if len(code.encode("utf-8")) > 100 * 1024:
        return "Error: Generated code exceeds 100 KB."

    try:
        ast.parse(code)
    except SyntaxError as error:
        return f"Error: Invalid Python syntax: {error}"

    OUTPUT_DIR.mkdir(exist_ok=True)

    output_path = OUTPUT_DIR / filename

    try:
        # Exclusive creation prevents overwriting existing files.
        with output_path.open("x", encoding="utf-8") as file:
            file.write(code)

        return f"Saved successfully: {output_path}"

    except FileExistsError:
        return "Error: File already exists. Existing files will not be overwritten."

    except OSError as error:
        return f"Error: Unable to save file: {error}"
