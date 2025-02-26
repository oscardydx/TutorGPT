import requests

# Configuración
IAM_TOKEN = "t1.9euelZqeyZnKyJyKnc-Ki5adnZ2Kne3rnpWal82dyY6Sy8eSyMmdm5mNmcvl8_dONg1C-e9sd0pS_t3z9w5lCkL572x3SlL-zef1656VmsbJkc2Zy5eSiZ6KzYuNnJnO7_zF656VmsbJkc2Zy5eSiZ6KzYuNnJnO.AD3GP02VhZWsMKnYsuJKYVGKSDWg9fbm1amcUXgXWVIdKEWOLh9M1H94yOT_FHheMVq7pz2OELBE1CQgRqImBw"  # Reemplaza con tu token de autenticación de Yandex Cloud
FOLDER_ID = "b1gc4453l5d6nl17mohu"  # ID de la carpeta en Yandex Cloud
ENDPOINT = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def yandex_gpt_request(prompt, max_tokens=100):
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
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