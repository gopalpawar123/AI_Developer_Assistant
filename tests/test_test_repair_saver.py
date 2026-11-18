
from tools import test_repair_saver
from tools import test_writer


def test_GivenNoApproval_WhenSavingRepair_ThenRejected(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        test_writer, "OUTPUT_DIR", tmp_path
    )

    result = test_repair_saver.save_approved_repair(
        "test_sample.py",
        "def test_example(): assert True",
        approved=False,
    )

    assert result["status"] == "rejected"
    assert not (tmp_path / "test_sample_repaired.py").exists()


def test_GivenApproval_WhenSavingRepair_ThenSaved(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        test_writer, "OUTPUT_DIR", tmp_path
    )

    result = test_repair_saver.save_approved_repair(
        "test_sample.py",
        "def test_example(): assert True",
        approved=True,
    )

    assert result["status"] == "success"
    assert result["filename"] == "test_sample_repaired.py"
    assert (tmp_path / "test_sample_repaired.py").exists()


def test_GivenExistingRepair_WhenSaving_ThenNoOverwrite(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        test_writer, "OUTPUT_DIR", tmp_path
    )

    existing = tmp_path / "test_sample_repaired.py"
    existing.write_text("original content", encoding="utf-8")

    result = test_repair_saver.save_approved_repair(
        "test_sample.py",
        "def test_example(): assert True",
        approved=True,
    )

    assert result["status"] == "error"
    assert existing.read_text(encoding="utf-8") == "original content"


def test_GivenInvalidFilename_WhenSaving_ThenRejected():
    result = test_repair_saver.save_approved_repair(
        "../test_sample.py",
        "def test_example(): assert True",
        approved=True,
    )

    assert result["status"] == "error"


def test_GivenEmptyCode_WhenSaving_ThenRejected():
    result = test_repair_saver.save_approved_repair(
        "test_sample.py",
        "",
        approved=True,
    )

    assert result["status"] == "error"


def test_GivenInvalidSyntax_WhenSaving_ThenRejected(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        test_writer, "OUTPUT_DIR", tmp_path
    )

    result = test_repair_saver.save_approved_repair(
        "test_sample.py",
        "def broken(",
        approved=True,
    )

    assert result["status"] == "error"
    assert not (tmp_path / "test_sample_repaired.py").exists()
