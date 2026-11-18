
from pathlib import Path

from tools.test_runner import (
    ALLOWED_TEST_DIR,
    run_generated_tests,
    validate_source_path,
)


def execute_approved_repair(
    repaired_filename: str,
    source_path: str,
    approved: bool = False,
) -> dict:
    """
    Execute a saved AI-repaired test in Docker.

    Requires separate execution approval.
    Never executes Python tests directly on the host.
    """

    # Step 1: Require explicit execution approval.
    if approved is not True:
        return {
            "status": "rejected",
            "output": "User approval is required before executing the repaired test.",
        }

    # Step 2: Validate repaired test filename.
    if (
        not isinstance(repaired_filename, str)
        or Path(repaired_filename).name != repaired_filename
        or not repaired_filename.startswith("test_")
        or not repaired_filename.endswith("_repaired.py")
        or "/" in repaired_filename
        or "\\" in repaired_filename
    ):
        return {
            "status": "error",
            "output": "Invalid repaired test filename.",
        }

    # Step 3: Ensure the saved test exists.
    test_file = ALLOWED_TEST_DIR / repaired_filename

    if not test_file.is_file() or test_file.is_symlink():
        return {
            "status": "error",
            "output": "Repaired test file does not exist or is not allowed.",
        }

    # Step 4: Validate the source file.
    if validate_source_path(source_path) is None:
        return {
            "status": "error",
            "output": "Invalid or unavailable source file.",
        }

    # Step 5: Execute using the existing Docker runner.
    return run_generated_tests(
        filename=repaired_filename,
        approved=True,
        source_path=source_path,
    )
