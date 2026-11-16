
from agents.llm_client import get_ai_response


def main():

    print("======================================")
    print("       AI DEVELOPER ASSISTANT")
    print("======================================")

    print("Model: Qwen 2.5 3B")
    print("Type 'exit' to close the application.")

    # Store conversation history
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI Developer Assistant. "
                "Help users understand Python, C++, Java, "
                "software development and testing. "
                "Explain technical concepts clearly "
                "with examples."
            )
        }
    ]

    while True:

        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            print("\nAI Assistant: Goodbye!")
            break

        if not user_input:
            continue

        # Add user question to conversation
        messages.append({
            "role": "user",
            "content": user_input
        })

        try:

            print("\nAI Assistant: Thinking...")

            ai_response = get_ai_response(messages)

            # Store AI response in conversation history
            messages.append({
                "role": "assistant",
                "content": ai_response
            })

            print("\nAI Assistant:", ai_response)

        except Exception as error:

            print("\nError communicating with AI model:")
            print(error)

            # Remove unanswered user message
            messages.pop()


if __name__ == "__main__":
    main()
