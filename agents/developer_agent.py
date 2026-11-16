
from ollama import chat

from tools.file_reader import read_file


MODEL_NAME = "qwen2.5:3b"

AVAILABLE_TOOLS = {
    "read_file": read_file
}


def run_developer_agent(user_input: str):

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI Developer Assistant. "
                "You can read project source files using the "
                "read_file tool. When the user asks you to "
                "inspect or analyze a file, use this tool. "
                "Never claim to have read a file unless the "
                "tool returned its contents."
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
            tools=[read_file]
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
