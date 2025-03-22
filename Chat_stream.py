import os
from dotenv import load_dotenv
from openai import OpenAI
from LLMtoHTML import converter
import logging

load_dotenv()
logging.basicConfig(level=logging.ERROR)

GEMINI_MODEL = "gemini-2.0-flash"  # Or your preferred Gemini model

def get_gemini_client():
    """
    Retrieves and validates the Gemini API client.
    """
    gemini_api_key = os.getenv("gemini_api_key")
    gemini_api_url = os.getenv("gemini_api_url")
    if not gemini_api_key or not gemini_api_url:
        raise ValueError("GEMINI_API_KEY or GEMINI_API_URL environment variable not set.")
    return OpenAI(api_key=gemini_api_key, base_url=gemini_api_url)

def chat_gemini_stream(messages):
    """
    Chats with Gemini using the streaming API.

    Args:
        messages: A list of message dictionaries in the format:
                  [{"role": "system", "content": "system message"},
                   {"role": "user", "content": "user message"},
                   {"role": "assistant", "content": "assistant message"},
                   ...]

    Returns:
        A generator that yields the streamed content chunks.
    """
    try:
        client = get_gemini_client()
        stream = client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=messages,
            stream=True,  # Enable streaming
        )

        for chunk in stream:
            if chunk.choices:
                yield chunk.choices[0].delta.content or ""

    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        yield f"Error: {e}"
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        yield f"Error: {e}"

def main():
    """
    Example usage of the Gemini streaming chat.
    """
    user_question = "使用Docker compose 搭配 Dockerfile搭建容器，若要添加環境變數寫在哪比較好"

    messages = [
        {"role": "system", "content": ""},
        {"role": "user", "content": user_question}
    ]

    full_response = ""
    for chunk in chat_gemini_stream(messages):
        print(chunk, end="", flush=True)  # Print each chunk as it arrives
        full_response += chunk

    print("\n\n--- Full Response (for converter) ---")
    print(full_response)
    converter(full_response)

if __name__ == "__main__":
    main()
