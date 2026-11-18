import pytest

from tools.test_repair_quality import validate_repair_quality


def test_GivenValidRepair_WhenCheckingQuality_ThenAccepted():
    original = '''
def test_reverse():
    assert reverse_string("hello") == "hello"
'''
    repaired = '''
def test_reverse():
    assert reverse_string("hello") == "olleh"
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is True
    assert result["errors"] == []


def test_GivenRemovedTest_WhenCheckingQuality_ThenRejected():
    original = '''
def test_one():
    assert 1 == 1

def test_two():
    assert 2 == 2
'''
    repaired = '''
def test_one():
    assert 1 == 1
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is False
    assert any("removed" in error.lower() for error in result["errors"])


def test_GivenTrivialAssertion_WhenCheckingQuality_ThenRejected():
    original = '''
def test_reverse():
    assert reverse_string("hello") == "olleh"
'''
    repaired = '''
def test_reverse():
    assert True
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is False
    assert any("trivial" in error.lower() for error in result["errors"])


def test_GivenReducedAssertions_WhenCheckingQuality_ThenWarning():
    original = '''
def test_reverse():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("abc") == "cba"
'''
    repaired = '''
def test_reverse():
    assert reverse_string("hello") == "olleh"
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is True
    assert any("assertions" in warning.lower() for warning in result["warnings"])


def test_GivenRemovedExceptionCheck_WhenCheckingQuality_ThenWarning():
    original = '''
import pytest

def test_reverse():
    assert reverse_string("hello") == "olleh"
    with pytest.raises(TypeError):
        reverse_string(123)
'''
    repaired = '''
def test_reverse():
    assert reverse_string("hello") == "olleh"
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is True
    assert any("pytest.raises" in warning for warning in result["warnings"])


def test_GivenNoAssertions_WhenCheckingQuality_ThenRejected():
    original = '''
def test_reverse():
    assert reverse_string("hello") == "olleh"
'''
    repaired = '''
def test_reverse():
    reverse_string("hello")
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is False
    assert any("no meaningful assertions" in error.lower() for error in result["errors"])


@pytest.mark.parametrize(
    "assertion",
    [
        "assert True",
        "assert 1 == 1",
        "assert 2 > 1",
        'assert "hello" == "hello"',
        "assert 5 >= 3",
        "assert 10 != 20",
    ],
)
def test_GivenTrivialConstantAssertion_WhenRepairing_ThenRejected(assertion):
    original = '''
def test_calculation():
    assert calculate(2, 3) == 5
'''
    repaired = f'''
def test_calculation():
    {assertion}
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is False
    assert any("trivial" in error.lower() for error in result["errors"])


def test_GivenMeaningfulAssertion_WhenRepairing_ThenAccepted():
    original = '''
def test_calculation():
    assert calculate(2, 3) == 5
'''
    repaired = '''
def test_calculation():
    assert calculate(3, 4) == 7
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is True
    assert result["errors"] == []


@pytest.mark.parametrize(
    "bypass",
    [
        "pytest.skip('Avoid failure')",
        "pytest.xfail('Known failure')",
    ],
)
def test_GivenNewRuntimeBypass_WhenCheckingQuality_ThenRejected(bypass):
    original = '''
def test_calculation():
    assert calculate(2, 3) == 5
'''
    repaired = f'''
import pytest

def test_calculation():
    {bypass}
    assert calculate(2, 3) == 5
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is False
    assert any("test-skipping" in error for error in result["errors"])


@pytest.mark.parametrize(
    "marker",
    [
        "@pytest.mark.skip(reason='Avoid failure')",
        "@pytest.mark.skipif(True, reason='Avoid failure')",
        "@pytest.mark.xfail(reason='Known failure')",
    ],
)
def test_GivenNewSkipMarker_WhenCheckingQuality_ThenRejected(marker):
    original = '''
def test_calculation():
    assert calculate(2, 3) == 5
'''
    repaired = f'''
import pytest

{marker}
def test_calculation():
    assert calculate(2, 3) == 5
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is False
    assert any("test-skipping" in error for error in result["errors"])


def test_GivenExistingSkipMarker_WhenPreserved_ThenAccepted():
    original = '''
import pytest

@pytest.mark.skip(reason="Existing condition")
def test_calculation():
    assert calculate(2, 3) == 5
'''
    repaired = '''
import pytest

@pytest.mark.skip(reason="Existing condition")
def test_calculation():
    assert calculate(3, 4) == 7
'''
    result = validate_repair_quality(original, repaired)
    assert result["valid"] is True
    assert result["errors"] == []
