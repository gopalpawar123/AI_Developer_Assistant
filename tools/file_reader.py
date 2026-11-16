
from pathlib import Path


# Define our project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories and files the tool must not access
BLOCKED_PARTS = {
    "venv",
    ".git",
    "__pycache__"
}

BLOCKED_FILES = {
    ".env"
}


def read_file(file_path: str) -> str:
    """
    Read a source code file inside the project directory.

    Args:
        file_path: Relative path of the file.

    Returns:
        File content or an error message.
    """

    try:
        requested_path = (PROJECT_ROOT / file_path).resolve()

        # Prevent access outside the project
        if not requested_path.is_relative_to(PROJECT_ROOT):
            return "Access denied: File is outside the project directory."

        # Prevent access to restricted directories
        relative_path = requested_path.relative_to(PROJECT_ROOT)

        if any(part in BLOCKED_PARTS for part in relative_path.parts):
            return "Access denied: This directory is restricted."

        if requested_path.name in BLOCKED_FILES:
            return "Access denied: This file is restricted."

        if not requested_path.is_file():
            return "Error: Requested file does not exist."

        # Limit reading to 100 KB
        if requested_path.stat().st_size > 100 * 1024:
            return "Error: File exceeds the 100 KB reading limit."

        content = requested_path.read_text(encoding="utf-8")

        return content

    except UnicodeDecodeError:
        return "Error: File is not a supported UTF-8 text file."

    except OSError as error:
        return f"File reading error: {error}"
