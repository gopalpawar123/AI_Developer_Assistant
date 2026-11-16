
from ollama import chat


MODEL_NAME = "qwen2.5:3b"


def get_ai_response(messages):

    response = chat(
        model=MODEL_NAME,
        messages=messages
    )

    return response.message.content
