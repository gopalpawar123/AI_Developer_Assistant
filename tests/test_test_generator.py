def test_generation_prompt_prevents_misleading_test_names():
    from tools.test_generator import PYTHON_TEST_RULES

    assert "Every test name MUST accurately describe" in PYTHON_TEST_RULES
    assert "test_multiplication MUST NOT call add()" in PYTHON_TEST_RULES
    assert "Do not create duplicate tests with misleading names" in PYTHON_TEST_RULES