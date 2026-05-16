import requests
from configs.settings import OLLAMA_HOST


def chat_with_ollama(model, prompt):
    url = f"{OLLAMA_HOST}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=payload)

    data = response.json()

    return data.get("response", "No response")