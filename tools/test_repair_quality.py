import ast


def is_trivial_assertion(node: ast.AST) -> bool:
    """Identify obviously true literal assertions without evaluating code."""
    if isinstance(node, ast.Constant):
        return node.value is True

    if not isinstance(node, ast.Compare):
        return False
    if len(node.ops) != 1 or len(node.comparators) != 1:
        return False

    left, right = node.left, node.comparators[0]
    if not isinstance(left, ast.Constant) or not isinstance(right, ast.Constant):
        return False

    left_value, right_value = left.value, right.value
    if type(left_value) not in (int, float, str, bool):
        return False
    if type(right_value) not in (int, float, str, bool):
        return False

    operator = node.ops[0]
    try:
        if isinstance(operator, ast.Eq):
            return left_value == right_value
        if isinstance(operator, ast.NotEq):
            return left_value != right_value
        if type(left_value) in (int, float) and type(right_value) in (int, float):
            if isinstance(operator, ast.Gt):
                return left_value > right_value
            if isinstance(operator, ast.GtE):
                return left_value >= right_value
            if isinstance(operator, ast.Lt):
                return left_value < right_value
            if isinstance(operator, ast.LtE):
                return left_value <= right_value
    except (TypeError, ValueError, OverflowError):
        return False
    return False


def get_test_bypasses(tree: ast.AST) -> set:
    """Collect direct pytest skip/xfail usage for each test function."""
    bypasses = set()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue

        for decorator in node.decorator_list:
            expression = decorator.func if isinstance(decorator, ast.Call) else decorator
            if (
                isinstance(expression, ast.Attribute)
                and expression.attr in ("skip", "skipif", "xfail")
                and isinstance(expression.value, ast.Attribute)
                and expression.value.attr == "mark"
                and isinstance(expression.value.value, ast.Name)
                and expression.value.value.id == "pytest"
            ):
                bypasses.add((node.name, expression.attr))

        # Avoid attributing calls in nested functions to their outer test.
        def scan_body(statements):
            for statement in statements:
                for child in ast.walk(statement):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if (
                            isinstance(func, ast.Attribute)
                            and func.attr in ("skip", "xfail")
                            and isinstance(func.value, ast.Name)
                            and func.value.id == "pytest"
                        ):
                            bypasses.add((node.name, func.attr))

        scan_body(node.body)

    return bypasses


def analyze_test_structure(code: str) -> dict:
    """Collect basic pytest coverage indicators without executing code."""
    tree = ast.parse(code)

    tests = set()
    assertions = 0
    exception_checks = 0
    trivial_assertions = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                tests.add(node.name)

        elif isinstance(node, ast.Assert):
            assertions += 1
            if is_trivial_assertion(node.test):
                trivial_assertions += 1

        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                expression = item.context_expr
                if (
                    isinstance(expression, ast.Call)
                    and isinstance(expression.func, ast.Attribute)
                    and isinstance(expression.func.value, ast.Name)
                    and expression.func.value.id == "pytest"
                    and expression.func.attr == "raises"
                ):
                    exception_checks += 1

    return {
        "tests": tests,
        "assertions": assertions,
        "exception_checks": exception_checks,
        "trivial_assertions": trivial_assertions,
        "bypasses": get_test_bypasses(tree),
    }


def validate_repair_quality(original_code: str, repaired_code: str) -> dict:
    """Compare test structure and flag suspicious coverage reductions."""
    errors = []
    warnings = []

    try:
        original = analyze_test_structure(original_code)
        repaired = analyze_test_structure(repaired_code)
    except (SyntaxError, TypeError, ValueError) as error:
        return {
            "valid": False,
            "errors": [f"Unable to analyze test structure: {error}"],
            "warnings": [],
        }

    removed_tests = original["tests"] - repaired["tests"]
    if removed_tests:
        errors.append(
            "Repair removed existing test functions: "
            + ", ".join(sorted(removed_tests))
        )

    new_bypasses = repaired["bypasses"] - original["bypasses"]
    if new_bypasses:
        descriptions = [
            f"{test_name}: {bypass}"
            for test_name, bypass in sorted(new_bypasses)
        ]
        errors.append(
            "Repair introduced test-skipping or xfail mechanisms: "
            + ", ".join(descriptions)
        )

    if repaired["trivial_assertions"]:
        errors.append(
            "Repair contains trivial assertions that always evaluate to True."
        )

    if repaired["assertions"] < original["assertions"]:
        warnings.append("Repair reduced the number of assertions.")

    if repaired["exception_checks"] < original["exception_checks"]:
        warnings.append("Repair reduced the number of pytest.raises checks.")

    if repaired["assertions"] + repaired["exception_checks"] == 0:
        errors.append(
            "Repaired tests contain no meaningful assertions "
            "or exception checks."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
