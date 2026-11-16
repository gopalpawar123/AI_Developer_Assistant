
import re

from agents.developer_agent import run_developer_agent
from tools.test_writer import save_generated_test


def extract_python_code(response):
    """Extract a Python code block from an AI response."""

    match = re.search(
        r"```(?:python|py)\s*\n(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip() + "\n"

    return None


def main():
    print("======================================")
    print("       AI DEVELOPER ASSISTANT")
    print("======================================")
    print("Model: Qwen 2.5 3B")
    print("Available tools: read_file, analyze_code, generate_unit_tests")
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

            # Check whether the user requested test generation.
            is_test_request = (
                "test" in user_input.lower()
                and any(
                    word in user_input.lower()
                    for word in ["generate", "create", "write"]
                )
            )

            if is_test_request:
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

                result = save_generated_test(filename, code)

                print("\n", result)

        except Exception as error:
            print("\nApplication error:", error)


if __name__ == "__main__":
    main()
