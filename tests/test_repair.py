def test_plain_python_repair_response_is_normalized():
    from tools.test_repair import normalize_repair_response

    ai_response = "assert add(1, 2) == 3"

    result = normalize_repair_response(ai_response)

    assert result == (
        "```python\n"
        "assert add(1, 2) == 3\n"
        "```"
    )

def test_fenced_python_repair_response_is_preserved():
    from tools.test_repair import normalize_repair_response

    ai_response = "```python\nassert add(1, 2) == 3\n```"

    result = normalize_repair_response(ai_response)

    assert result == ai_response


def test_invalid_python_repair_response_is_not_normalized():
    from tools.test_repair import normalize_repair_response

    ai_response = "def test_broken("

    result = normalize_repair_response(ai_response)

    assert result == ai_response