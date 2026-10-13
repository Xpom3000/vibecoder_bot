from openai import OpenAI

client = OpenAI(
    base_url="https://api.air.fail/public/openai/",
    api_key="sk-RbasvIn2680TUV2JphxtqkePLkI8D",  # ваш ключ
)

try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": "Привет"}],
        temperature=0.7,
    )
    print("Ответ:", response.choices[0].message.content)
except Exception as e:
    print("Ошибка:", e)