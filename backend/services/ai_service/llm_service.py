import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def query_llm(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": "phi3",
        "prompt": prompt,
        "stream": False
    })

    data = response.json()
    return data.get("response", "")