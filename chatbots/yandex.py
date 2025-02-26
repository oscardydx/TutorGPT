import requests
from decouple import config
# Configuración

ENDPOINT = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def yandex_gpt_request(prompt, max_tokens=100):
    headers = {
        "Authorization": f"Bearer {config("IAM_TOKEN")}",
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"gpt://{config("FOLDER_ID")}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": max_tokens
        },
        "messages": [{"role": "user", "text": prompt}]
    }

    response = requests.post(ENDPOINT, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
    else:
        return f"Error {response.status_code}: {response.text}"

# Ejemplo de uso
respuesta = yandex_gpt_request("¿Cuál es la capital de Francia?")
print(respuesta)