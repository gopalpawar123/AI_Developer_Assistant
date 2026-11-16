
from agents.developer_agent import run_developer_agent


def main():

    print("======================================")
    print("       AI DEVELOPER ASSISTANT")
    print("======================================")

    print("Model: Qwen 2.5 3B")
    print("Available tool: read_file")
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

            print("\nAI Assistant:", response)

        except Exception as error:

            print("\nApplication error:", error)


if __name__ == "__main__":
    main()
