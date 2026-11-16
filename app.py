
import re

from agents.developer_agent import run_developer_agent
from tools.test_writer import save_generated_test
from tools.test_runner import run_generated_tests
from tools.result_analyzer import analyze_test_result
from tools.test_validator import validate_generated_test
from tools.source_inspector import (
    extract_source_path,
    inspect_python_source
)


def extract_python_code(response):
    """Extract Python code from an AI response."""

    match = re.search(
        r"```(?:python|py)\s*\n(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip() + "\n"

    return None


def is_test_generation_request(user_input):
    """Check whether the user requested test generation."""

    request = user_input.lower()

    return (
        "test" in request
        and any(
            word in request
            for word in ["generate", "create", "write"]
        )
    )


def handle_test_execution(filename, source_path):
    """Request approval and execute supported tests in Docker."""

    print("\nThe generated test file has been saved.")

    # The current Docker runner only stages calculator.py.
    if source_path.replace("\\", "/") != "examples/calculator.py":
        print(
            "\nDocker execution is currently supported only for "
            "examples/calculator.py."
        )
        print("The generated test file has been saved but not executed.")
        return

    approval = input(
        "\nWould you like to execute these tests in Docker? (yes/no): "
    ).strip().lower()

    if approval != "yes":
        print("Test execution cancelled.")
        return

    print("\nExecuting tests inside Docker...")

    result = run_generated_tests(
        filename,
        approved=True
    )

    status = result.get("status", "unknown")
    output = result.get("output", "")

    print("\n========== TEST EXECUTION RESULT ==========")
    print("Status:", status.upper())
    print(output)
    print("===========================================")

    if status == "failed":
        answer = input(
            "\nWould you like AI to analyze the failure? (yes/no): "
        ).strip().lower()

        if answer == "yes":
            print("\nAI Assistant: Analyzing test failure...")

            try:
                analysis = analyze_test_result(result)

                print("\n========== AI FAILURE ANALYSIS ==========")
                print(analysis)
                print("=========================================")

            except Exception as error:
                print("\nAI failure analysis unavailable:", error)

    elif status == "passed":
        print("\nAll generated tests passed successfully.")

    elif status == "timeout":
        print("\nTest execution timed out.")

    elif status == "error":
        print("\nUnable to execute the generated tests.")


def main():
    print("======================================")
    print("       AI DEVELOPER ASSISTANT")
    print("======================================")
    print("Model: Qwen 2.5 3B")
    print("Available tools:")
    print("- File Reader")
    print("- Code Analyzer")
    print("- Unit Test Generator")
    print("- Test File Writer")
    print("- Source-Aware Test Validator")
    print("- Docker Test Runner")
    print("- AI Failure Analyzer")
    print("Type 'exit' to close.")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() == "exit":
                print("AI Assistant: Goodbye!")
                break

            if not user_input:
                continue

            print("\nAI Assistant: Processing...")

            response = run_developer_agent(user_input)

            print("\nAI Assistant:\n", response)

            # Continue normal conversation if tests were not requested.
            if not is_test_generation_request(user_input):
                continue

            # Phase 4.9: Identify the requested Python source file.
            source_path = extract_source_path(user_input)

            if not source_path:
                print(
                    "\nUnable to identify a Python source file "
                    "in the request."
                )
                continue

            # Inspect the source before validating generated code.
            source_info = inspect_python_source(source_path)

            if not source_info["valid"]:
                print(
                    "\nSource inspection failed:",
                    source_info["error"]
                )
                continue

            print("\nSource module:", source_info["module"])
            print("Available functions:", source_info["functions"])

            # Extract generated Python code.
            code = extract_python_code(response)

            if not code:
                print("\nNo Python test code found in the response.")
                continue

            # Validate generated code against the actual source module.
            print("\nValidating generated test code...")

            validation = validate_generated_test(
                code,
                required_imports=source_info["functions"],
                source_module=source_info["module"]
            )

            if not validation["valid"]:
                print("\nGenerated test validation failed:")

                for error in validation["errors"]:
                    print("-", error)

                print("\nPlease regenerate or correct the tests.")
                continue

            if validation["warnings"]:
                print("\nValidation warnings:")

                for warning in validation["warnings"]:
                    print("-", warning)

                print("\nReview these warnings before saving.")

            print("\nGenerated test validation passed.")

            # Ask the user to review and save.
            print("\nReview the generated code above before saving.")

            answer = input(
                "\nWould you like to save the generated tests? (yes/no): "
            ).strip().lower()

            if answer != "yes":
                print("Saving cancelled.")
                continue

            filename = input(
                "Enter filename (e.g. test_ai_calculator.py): "
            ).strip()

            save_result = save_generated_test(filename, code)

            print("\n", save_result)

            if not save_result.startswith("Saved successfully:"):
                continue

            # Docker execution still requires explicit approval.
            handle_test_execution(filename, source_path)

        except (KeyboardInterrupt, EOFError):
            print("\nAI Assistant: Goodbye!")
            break

        except Exception as error:
            print("\nApplication error:", error)


if __name__ == "__main__":
    main()
