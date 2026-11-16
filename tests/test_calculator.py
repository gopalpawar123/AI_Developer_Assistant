import pytest
from examples.calculator import add, divide


def test_add():
    assert add(2, 3) == 5


def test_add_with_zero():
    assert add(0, 0) == 0


def test_divide_normal_case():
    assert divide(10, 2) == 5


def test_divide_with_non_zero_divisor():
    assert divide(10, 5) == 2


def test_divide_with_zero_divisor():
    with pytest.raises(ValueError):
        divide(10, 0)