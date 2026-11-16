
from ollama import chat

from tools.file_reader import read_file
from tools.code_analyzer import analyze_code
from tools.test_generator import generate_unit_tests


MODEL_NAME = "qwen2.5:3b"

SYSTEM_PROMPT = """
You are an AI Developer Assistant.

Your responsibilities:
- Explain source code clearly.
- Analyze Python, C++, and Java code.
- Generate unit tests for source code.
- Identify potential bugs and edge cases.

When generating Python tests:
- Use pytest.
- Include all required imports.
- Generate complete executable test code.
- Include normal, edge, and exception cases.
- Return code inside a ```python Markdown code block.
- Do not invent unavailable APIs.

When generating C++ tests:
- Use Google Test.
- Prefer ASSERT_* assertions.
- Do not use GoogleMock.
- Use Given_When_Then style test names.

Never claim to have read a file unless its contents
were successfully returned by a tool.
"""


def run_developer_agent(user_input: str):

    request = user_input.lower()

    # Extract a source file path from the user's request.
    import re

    match = re.search(
        r"([\w./\\-]+\.(?:py|cpp|cxx|cc|h|hpp|java))\b",
        user_input,
        re.IGNORECASE
    )

    file_path = match.group(1) if match else None

    tool_result = None

    if file_path:

        if (
            "test" in request
            and any(word in request for word in ["generate", "create", "write"])
        ):
            print(f"[DEBUG] Running generate_unit_tests: {file_path}")
            tool_result = generate_unit_tests(file_path)

        elif any(word in request for word in ["analyze", "review", "bug"]):
            print(f"[DEBUG] Running analyze_code: {file_path}")
            tool_result = analyze_code(file_path)

        else:
            print(f"[DEBUG] Running read_file: {file_path}")
            tool_result = read_file(file_path)

        if tool_result.startswith(
            ("Error:", "Access denied:", "File reading error:")
        ):
            return tool_result

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    if tool_result is not None:
        messages.append({
            "role": "system",
            "content": (
                "The following content was retrieved from the "
                "requested source file using an approved local tool. "
                "Use it to answer the user's request.\n\n"
                + tool_result
            )
        })

    response = chat(
        model=MODEL_NAME,
        messages=messages
    )

    return response.message.content or "No response generated."
