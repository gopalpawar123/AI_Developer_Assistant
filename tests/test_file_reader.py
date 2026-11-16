
from tools.file_reader import read_file


def test_read_existing_project_file():

    content = read_file("app.py")

    assert "AI DEVELOPER ASSISTANT" in content


def test_read_missing_file():

    content = read_file("missing_file.py")

    assert "does not exist" in content


def test_block_sensitive_file():

    content = read_file(".env")

    assert "Access denied" in content
