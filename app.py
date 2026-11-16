
import re

from agents.developer_agent import run_developer_agent
from tools.test_writer import save_generated_test
from tools.test_runner import run_generated_tests
from tools.result_analyzer import analyze_test_result


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


def handle_test_execution(filename):
    """Request approval and execute saved tests in Docker."""

    print("\nThe generated test file has been saved.")
    print("Docker execution is available for the calculator example.")

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

            analysis = analyze_test_result(result)

            print("\n========== AI FAILURE ANALYSIS ==========")
            print(analysis)
            print("=========================================")

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
    print("- Docker Test Runner")
    print("- AI Failure Analyzer")
    print("Type 'exit' to close.")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            print("AI Assistant: Goodbye!")
            break

        if not user_input:
            continue

        try:
            print("\nAI Assistant: Processing...")

            response = run_developer_agent(user_input)

            print("\nAI Assistant:\n", response)

            if not is_test_generation_request(user_input):
                continue

            code = extract_python_code(response)

            if not code:
                print("\nNo Python test code found in the response.")
                continue

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

            # Execute only after a successful save.
            if not save_result.startswith("Saved successfully:"):
                continue

            handle_test_execution(filename)

        except (KeyboardInterrupt, EOFError):
            print("\nAI Assistant: Goodbye!")
            break

        except Exception as error:
            print("\nApplication error:", error)


if __name__ == "__main__":
    main()
