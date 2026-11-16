
from ollama import chat

from tools.file_reader import read_file
from tools.code_analyzer import analyze_code
from tools.test_generator import generate_unit_tests


MODEL_NAME = "qwen2.5:3b"

AVAILABLE_TOOLS = {
    "read_file": read_file,
    "analyze_code": analyze_code,
    "generate_unit_tests": generate_unit_tests
}


def run_developer_agent(user_input: str):

    messages = [
        {
    "role": "system",
    "content": (
        "You are an AI Developer Assistant. "
        "Use read_file to inspect files, "
        "analyze_code to review source code, and "
        "generate_unit_tests to prepare unit tests. "
        "When a tool returns source code, use that content "
        "to produce the requested analysis or tests. "
        "Never claim to have read a file unless a tool "
        "successfully returned its contents. "
        "If a tool reports an error or access denial, "
        "report that error and do not invent file contents."
    )
},
        {
            "role": "user",
            "content": user_input
        }
    ]

    # Allow a maximum of 3 tool-calling iterations
    for iteration in range(3):

        response = chat(
    model=MODEL_NAME,
    messages=messages,
    tools=[
        read_file,
        analyze_code,
        generate_unit_tests
    ]
)

        messages.append(response.message)

        tool_calls = response.message.tool_calls or []

        # No tool requested: return the final answer
        if not tool_calls:
            return response.message.content

        # Execute requested tools
        for tool_call in tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"[DEBUG] Tool called: {tool_name}, Arguments: {arguments}")

            if tool_name not in AVAILABLE_TOOLS:
                result = "Error: Unknown tool."

            else:
                try:
                    result = AVAILABLE_TOOLS[tool_name](**arguments)

                except Exception as error:
                    result = f"Tool execution failed: {error}"

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": str(result)
            })

    return "Maximum tool-calling iterations reached."
