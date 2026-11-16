import pytest
from examples import calculator

def test_add():
    assert calculator.add(2, 3) == 5
    assert calculator.add(-1, 1) == 0
    assert calculator.add(-1, -1) == -2

def test_divide_normal():
    assert calculator.divide(4, 2) == 2
    assert calculator.divide(10, 5) == 2

def test_divide_by_zero():
    with pytest.raises(ValueError) as exc_info:
        calculator.divide(10, 0)
    assert "Cannot divide by zero" in str(exc_info.value)
