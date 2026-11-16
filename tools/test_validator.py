
import ast
import builtins


def validate_generated_test(
    code: str,
    required_imports=None,
    source_module=None
) -> dict:
    """
    Statically validate AI-generated pytest code.

    Checks:
    - Python syntax
    - Required imports
    - Correct source module
    - Potentially undefined names
    - Pytest test functions
    - Production function redefinitions

    Does not execute generated code.
    """

    errors = []
    warnings = []

    if not code or not code.strip():
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
    source_imported_names = set()

    # Step 1: Collect imports, definitions and assignments.
    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(
                    alias.asname or alias.name.split(".")[0]
                )

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)

                if source_module and node.module == source_module:
                    source_imported_names.add(alias.name)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)

        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)

        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            assigned_names.add(node.id)

    # Step 2: Validate required imports.
    for name in required_imports:

        if source_module:
            if name not in source_imported_names:
                errors.append(
                    f"Missing required import: {name} "
                    f"from {source_module}"
                )

        elif name not in imported_names:
            errors.append(f"Missing required import: {name}")

    # Step 3: Detect accidental production function redefinitions.
    if source_module:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in required_imports:
                    errors.append(
                        f"Production function redefined in tests: {node.name}"
                    )

    # Step 4: Detect potentially undefined names.
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
        warnings.append(f"Possibly undefined name: {name}")

    # Step 5: Verify that pytest test functions exist.
    test_functions = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]

    if not test_functions:
        errors.append("No pytest test functions found.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
