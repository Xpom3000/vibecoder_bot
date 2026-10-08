import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def get_ai_response(user_message: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": user_message}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Ошибка при запросе к API: {e}"

if __name__ == "__main__":
    print(get_ai_response("Привет! Как дела?"))