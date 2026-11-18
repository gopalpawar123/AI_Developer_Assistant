
from tools import test_repair_diff


def test_GivenChangedCode_WhenComparing_ThenDiffReturned(
    tmp_path, monkeypatch
):
    generated_tests = tmp_path / "generated_tests"
    generated_tests.mkdir()

    original = generated_tests / "test_sample.py"
    original.write_text(
        "def test_value():\n"
        "    assert 1 == 2\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        test_repair_diff,
        "PROJECT_ROOT",
        tmp_path,
    )

    repaired_code = (
        "def test_value():\n"
        "    assert 1 == 1\n"
    )

    result = test_repair_diff.generate_repair_diff(
        "test_sample.py",
        repaired_code,
    )

    assert result["status"] == "success"
    assert result["changed"] is True
    assert "-    assert 1 == 2" in result["diff"]
    assert "+    assert 1 == 1" in result["diff"]


def test_GivenSameCode_WhenComparing_ThenNoChanges(
    tmp_path, monkeypatch
):
    generated_tests = tmp_path / "generated_tests"
    generated_tests.mkdir()

    code = "def test_value():\n    assert True\n"

    (generated_tests / "test_sample.py").write_text(
        code,
        encoding="utf-8",
    )

    monkeypatch.setattr(
        test_repair_diff,
        "PROJECT_ROOT",
        tmp_path,
    )

    result = test_repair_diff.generate_repair_diff(
        "test_sample.py",
        code,
    )

    assert result["status"] == "success"
    assert result["changed"] is False
    assert result["diff"] == ""


def test_GivenInvalidFilename_WhenComparing_ThenRejected():
    result = test_repair_diff.generate_repair_diff(
        "../test_invalid.py",
        "def test_example(): pass",
    )

    assert result["status"] == "error"


def test_GivenMissingFile_WhenComparing_ThenRejected(
    tmp_path, monkeypatch
):
    (tmp_path / "generated_tests").mkdir()

    monkeypatch.setattr(
        test_repair_diff,
        "PROJECT_ROOT",
        tmp_path,
    )

    result = test_repair_diff.generate_repair_diff(
        "test_missing.py",
        "def test_example(): pass",
    )

    assert result["status"] == "error"


def test_GivenEmptyRepair_WhenComparing_ThenRejected(
    tmp_path, monkeypatch
):
    generated_tests = tmp_path / "generated_tests"
    generated_tests.mkdir()

    (generated_tests / "test_sample.py").write_text(
        "def test_example(): pass\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        test_repair_diff,
        "PROJECT_ROOT",
        tmp_path,
    )

    result = test_repair_diff.generate_repair_diff(
        "test_sample.py",
        "",
    )

    assert result["status"] == "error"


def test_GivenSymlink_WhenComparing_ThenRejected(
    tmp_path, monkeypatch
):
    generated_tests = tmp_path / "generated_tests"
    generated_tests.mkdir()

    target = tmp_path / "external.py"
    target.write_text(
        "def test_external(): pass\n",
        encoding="utf-8",
    )

    link = generated_tests / "test_link.py"

    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("Symlinks unavailable on this system")

    monkeypatch.setattr(
        test_repair_diff,
        "PROJECT_ROOT",
        tmp_path,
    )

    result = test_repair_diff.generate_repair_diff(
        "test_link.py",
        "def test_external(): assert True",
    )

    assert result["status"] == "error"
