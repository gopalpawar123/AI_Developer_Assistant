
from tools import test_writer


def test_save_generated_test(tmp_path, monkeypatch):
    monkeypatch.setattr(test_writer, "OUTPUT_DIR", tmp_path)

    code = "def test_example():\n    assert 2 + 2 == 4\n"

    result = test_writer.save_generated_test(
        "test_generated_example.py",
        code
    )

    assert "Saved successfully" in result
    assert (tmp_path / "test_generated_example.py").exists()


def test_reject_invalid_filename():
    result = test_writer.save_generated_test(
        "../invalid.py",
        "assert True"
    )

    assert "Error:" in result


def test_reject_invalid_python():
    result = test_writer.save_generated_test(
        "test_invalid.py",
        "def broken("
    )

    assert "Invalid Python syntax" in result


def test_prevent_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(test_writer, "OUTPUT_DIR", tmp_path)

    filename = "test_existing.py"
    code = "def test_example():\n    assert True\n"

    first = test_writer.save_generated_test(filename, code)
    second = test_writer.save_generated_test(filename, code)

    assert "Saved successfully" in first
    assert "already exists" in second
