
from pathlib import Path

from tools.file_reader import read_file

TEST_FRAMEWORKS = {
    ".py": "pytest",
    ".cpp": "Google Test (GTest)",
    ".cxx": "Google Test (GTest)",
    ".cc": "Google Test (GTest)",
    ".java": "JUnit 5"
}


def generate_unit_tests(file_path: str) -> str:
    """Read a source file and prepare instructions for AI unit test generation."""

    extension = Path(file_path).suffix.lower()

    if extension not in TEST_FRAMEWORKS:
        return "Error: Unsupported file type for test generation."

    content = read_file(file_path)

    if content.startswith(("Error:", "Access denied:", "File reading error:")):
        return content

    framework = TEST_FRAMEWORKS[extension]

    return (
        f"Generate unit tests for: {file_path}\n"
        f"Framework: {framework}\n\n"
        "Requirements:\n"
        "- Cover normal inputs, edge cases, and failure scenarios.\n"
        "- Do not invent unavailable APIs or dependencies.\n"
        "- For C++ GTest, use ASSERT_* assertions.\n"
        "- For C++ GTest, do not use GoogleMock or EXPECT_CALL.\n"
        "- Prefer Given_When_Then style test names.\n"
        "- Explain any assumptions and required dependencies.\n\n"
        f"Source code:\n{content}"
    )
