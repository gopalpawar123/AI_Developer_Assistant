
from pathlib import Path

from tools.file_reader import read_file

SUPPORTED_EXTENSIONS = {".py", ".cpp", ".cxx", ".cc", ".h", ".hpp", ".java"}


def analyze_code(file_path: str) -> str:
    """Read a source file and return its contents for AI code analysis."""

    extension = Path(file_path).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return "Error: Unsupported source file type."

    content = read_file(file_path)

    if content.startswith(("Error:", "Access denied:", "File reading error:")):
        return content

    return (
        f"Source file: {file_path}\n"
        f"Language extension: {extension}\n\n"
        f"Analyze the following source code:\n\n{content}"
    )
