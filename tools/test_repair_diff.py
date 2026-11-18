
import difflib
from pathlib import Path

from tools.test_runner import PROJECT_ROOT


def generate_repair_diff(
    test_filename: str,
    repaired_code: str,
) -> dict:
    """
    Compare an existing generated pytest file
    with proposed AI-repaired code.

    Does not modify files or execute tests.
    """

    # Step 1: Validate filename
    if (
        not isinstance(test_filename, str)
        or Path(test_filename).name != test_filename
        or not test_filename.startswith("test_")
        or not test_filename.endswith(".py")
        or "/" in test_filename
        or "\\" in test_filename
    ):
        return {
            "status": "error",
            "output": "Invalid test filename.",
        }

    # Step 2: Locate existing test
    test_file = PROJECT_ROOT / "generated_tests" / test_filename

    if test_file.is_symlink() or not test_file.is_file():
        return {
            "status": "error",
            "output": "Generated test file does not exist.",
        }

    # Step 3: Validate repaired code
    if not isinstance(repaired_code, str) or not repaired_code.strip():
        return {
            "status": "error",
            "output": "Repaired test code is empty.",
        }

    # Step 4: Read original test
    try:
        original_code = test_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return {
            "status": "error",
            "output": f"Unable to read original test: {error}",
        }

    # Step 5: Generate unified diff
    diff = difflib.unified_diff(
        original_code.splitlines(keepends=True),
        repaired_code.splitlines(keepends=True),
        fromfile=f"original/{test_filename}",
        tofile=f"repaired/{test_filename}",
    )

    diff_output = "".join(diff)

    # Step 6: Return comparison
    return {
        "status": "success",
        "changed": bool(diff_output),
        "diff": diff_output,
        "original_code": original_code,
        "repaired_code": repaired_code,
    }
