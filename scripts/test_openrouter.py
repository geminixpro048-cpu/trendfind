#!/usr/bin/env python3
import os, requests
from dotenv import load_dotenv

load_dotenv("/home/asciix/trendfind/.env")

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ Nenhuma chave OPENROUTER_API_KEY encontrada no .env")
    exit(1)

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "mistralai/mistral-7b-instruct:free",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one short sentence."}
    ]
}

print("🚀 A testar OpenRouter API...")
resp = requests.post(url, headers=headers, json=data, timeout=30)

print(f"Status code: {resp.status_code}")
if resp.status_code == 200:
    print("✅ Ligação bem-sucedida!")
    print(resp.json()["choices"][0]["message"]["content"])
else:
    print("❌ Falhou:")
    print(resp.text)
