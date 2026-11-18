
from pathlib import Path

from tools.test_writer import save_generated_test


def save_approved_repair(
    original_filename: str,
    repaired_code: str,
    approved: bool = False,
) -> dict:
    """
    Save repaired tests only after explicit approval.

    Never overwrite the original test file.
    """

    # Step 1: Require user approval
    if approved is not True:
        return {
            "status": "rejected",
            "output": "User approval is required before saving.",
        }

    # Step 2: Validate original filename
    if (
        not isinstance(original_filename, str)
        or Path(original_filename).name != original_filename
        or not original_filename.startswith("test_")
        or not original_filename.endswith(".py")
        or "/" in original_filename
        or "\\" in original_filename
    ):
        return {
            "status": "error",
            "output": "Invalid original test filename.",
        }

    # Step 3: Validate repaired code
    if not isinstance(repaired_code, str) or not repaired_code.strip():
        return {
            "status": "error",
            "output": "Repaired code is empty.",
        }

    # Step 4: Generate a new filename
    repaired_filename = (
        f"{Path(original_filename).stem}_repaired.py"
    )

    # Step 5: Save using existing safe writer
    result = save_generated_test(
        repaired_filename,
        repaired_code,
    )

    if result.startswith("Error:"):
        return {
            "status": "error",
            "output": result,
        }

    return {
        "status": "success",
        "output": result,
        "filename": repaired_filename,
    }
