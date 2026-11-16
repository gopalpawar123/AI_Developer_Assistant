
import ast
import builtins


def validate_generated_test(code: str, required_imports=None) -> dict:
    """Statically validate generated pytest code without executing it."""

    errors = []
    warnings = []

    if not code.strip():
        return {
            "valid": False,
            "errors": ["Generated test code is empty."],
            "warnings": []
        }

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return {
            "valid": False,
            "errors": [f"Invalid Python syntax: {error}"],
            "warnings": []
        }

    required_imports = required_imports or []

    imported_names = set()
    defined_names = set()
    assigned_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(
                    alias.asname or alias.name.split(".")[0]
                )

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)

        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)

        elif isinstance(node, ast.Name) and isinstance(
            node.ctx, (ast.Store, ast.Param)
        ):
            assigned_names.add(node.id)

    for name in required_imports:
        if name not in imported_names:
            errors.append(
                f"Missing required import: {name}"
            )

    # Detect common undefined names.
    available_names = (
        imported_names
        | defined_names
        | assigned_names
        | set(dir(builtins))
    )

    undefined_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in available_names:
                undefined_names.add(node.id)

    for name in sorted(undefined_names):
        warnings.append(
            f"Possibly undefined name: {name}"
        )

    # Check that at least one pytest-style test exists.
    test_functions = [
        name for name in defined_names
        if name.startswith("test_")
    ]

    if not test_functions:
        errors.append("No pytest test functions found.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
