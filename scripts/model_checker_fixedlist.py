#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendFind - Model JSON Tester (fixed list)
Testa apenas os modelos fornecidos manualmente.
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

BASE = "/home/asciix/trendfind"
load_dotenv(os.path.join(BASE, ".env"))
API_KEY = os.getenv("OPENROUTER_API_KEY")
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
  "deepseek/deepseek-chat-v3.1:free",
  "openai/gpt-oss-20b:free",
  "z-ai/glm-4.5-air:free",
  "qwen/qwen3-coder:free",
  "moonshotai/kimi-k2:free",
  "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
  "google/gemma-3n-e2b-it:free",
  "tencent/hunyuan-a13b-instruct:free",
  "tngtech/deepseek-r1t2-chimera:free",
  "mistralai/mistral-small-3.2-24b-instruct:free",
  "moonshotai/kimi-dev-72b:free",
  "deepseek/deepseek-r1-0528-qwen3-8b:free",
  "deepseek/deepseek-r1-0528:free",
  "mistralai/devstral-small-2505:free",
  "google/gemma-3n-e4b-it:free",
  "meta-llama/llama-3.3-8b-instruct:free",
  "qwen/qwen3-4b:free",
  "qwen/qwen3-30b-a3b:free",
  "qwen/qwen3-14b:free",
  "tngtech/deepseek-r1t-chimera:free",
  "microsoft/mai-ds-r1:free",
  "arliai/qwq-32b-arliai-rpr-v1:free",
  "shisa-ai/shisa-v2-llama3.3-70b:free",
  "agentica-org/deepcoder-14b-preview:free",
  "meta-llama/llama-4-maverick:free",
  "meta-llama/llama-4-scout:free",
  "qwen/qwen2.5-vl-32b-instruct:free",
  "deepseek/deepseek-chat-v3-0324:free",
  "mistralai/mistral-small-3.1-24b-instruct:free",
  "google/gemma-3-4b-it:free",
  "google/gemma-3-12b-it:free",
  "nousresearch/deephermes-3-llama-3-8b-preview:free",
  "google/gemma-3-27b-it:free",
  "cognitivecomputations/dolphin3.0-mistral-24b:free",
  "mistralai/mistral-small-24b-instruct-2501:free",
  "deepseek/deepseek-r1-distill-llama-70b:free",
  "deepseek/deepseek-r1:free",
  "google/gemini-2.0-flash-exp:free",
  "meta-llama/llama-3.3-70b-instruct:free",
  "qwen/qwen-2.5-coder-32b-instruct:free"
]

RESULTS = []
VALID = []

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def is_json_valid(text):
    try:
        j = json.loads(text.strip().strip("```").replace("json", ""))
        return all(k in j for k in ["title", "description", "body"])
    except Exception:
        return False

def test_model(model):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return JSON with title, description, body."},
            {"role": "user", "content": "Give a short JSON example."}
        ],
        "temperature": 0.1
    }
    start = time.time()
    try:
        r = requests.post(CHAT_URL, headers=headers, json=payload, timeout=25)
        latency = round(time.time() - start, 2)
        if r.status_code == 200:
            txt = r.json()["choices"][0]["message"]["content"]
            if is_json_valid(txt):
                return ("ok", latency)
            else:
                return ("invalid_json", latency)
        elif r.status_code == 429:
            return ("rate_limited", latency)
        elif r.status_code == 402:
            return ("payment_required", latency)
        elif r.status_code == 404:
            return ("not_found", latency)
        else:
            return (f"error_{r.status_code}", latency)
    except Exception as e:
        return (f"exception_{str(e)[:60]}", 0)

def main():
    log(f"🚀 Testando {len(MODELS)} modelos free com JSON check...")
    for i, m in enumerate(MODELS, 1):
        status, latency = test_model(m)
        log(f"[{i}/{len(MODELS)}] {m} → {status} ({latency}s)")
        RESULTS.append({"model": m, "status": status, "latency": latency})
        if status == "ok":
            VALID.append(m)
        time.sleep(1.5)

    with open(os.path.join(BASE, "scripts", "model_results_fixed.json"), "w") as f:
        json.dump(RESULTS, f, indent=2)
    with open(os.path.join(BASE, "scripts", "models_valid.json"), "w") as f:
        json.dump(VALID, f, indent=2)
    log(f"🏁 {len(VALID)} modelos válidos de {len(MODELS)} testados.")
    log(f"📄 Guardado em scripts/models_valid.json")

if __name__ == "__main__":
    main()
