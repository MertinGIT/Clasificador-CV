import requests
from dotenv import load_dotenv
import os
load_dotenv()
API_URL = os.getenv("API_URL")

def ask_ollama(prompt: str, model: str = "llama2"):
    response = requests.post(API_URL, json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    response.raise_for_status()
    result = response.json()
    return result["response"]
