import requests
import json
import urllib3

# Отключаем предупреждения о просроченном сертификате
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "sk-RbasvIn2680TUV2JphxtqkePLkI8D"

# Используем slug модели из списка: chatgpt, chatgpt_5, deepseek и т.д.
# Для модели GPT-5 (slug "gpt-5") используем endpoint /public/text/chatgpt_5
url = "https://api.air.fail/public/text/chatgpt_5"

headers = {
    "Authorization": API_KEY,  # без "Bearer"
}

form_data = {
    "content": "Привет! Как дела?",
    "info": json.dumps({
        "version": "gpt-5",  # slug версии из списка
        "temperature": 0.5
    })
}

try:
    response = requests.post(
        url,
        data=form_data,
        headers=headers,
        verify=False,  # обход просроченного сертификата
        timeout=120
    )
    print("Статус:", response.status_code)
    print("Ответ:", response.text)
except Exception as e:
    print("Ошибка:", e)