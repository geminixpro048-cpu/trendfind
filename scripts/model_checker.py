#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendFind – Model Checker v3.1
------------------------------------------------
Obtém os modelos gratuitos reais do OpenRouter via endpoint JSON oficial.
Testa JSON válido e mede latência, evitando erros 402 e scraping HTML.
"""

import os
import re
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# ============================================
# 🔧 CONFIGURAÇÕES
# ============================================
BASE_PATH = "/home/asciix/trendfind"
SCRIPT_PATH = os.path.join(BASE_PATH, "scripts")
LOG_PATH = os.path.join(SCRIPT_PATH, "logs")
os.makedirs(LOG_PATH, exist_ok=True)

load_dotenv(os.path.join(BASE_PATH, ".env"))
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    print("❌ OPENROUTER_API_KEY não encontrado no .env")
    exit(1)

RESULTS_PATH = os.path.join(SCRIPT_PATH, "model_results.json")
ACTIVE_PATH = os.path.join(SCRIPT_PATH, "models_active.json")
LOG_FILE = os.path.join(LOG_PATH, "model_check.log")

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_JSON = "https://openrouter.ai/api/v1/models?max_price=0"

# ============================================
# 🧩 Funções auxiliares
# ============================================
def log(msg: str):
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


def clean_json_text(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```$", "", raw)
    return raw.strip()


def is_valid_json(text: str) -> bool:
    try:
        cleaned = clean_json_text(text)
        j = json.loads(cleaned)
        return all(k in j for k in ["title", "description", "body"])
    except Exception:
        return False


# ============================================
# 🌍 Obter lista oficial de modelos gratuitos
# ============================================
def fetch_free_models():
    """Obtém os modelos gratuitos via endpoint JSON oficial do OpenRouter."""
    try:
        log(f"🌐 A obter lista oficial de modelos gratuitos: {MODELS_JSON}")
        r = requests.get(MODELS_JSON, timeout=25)
        if r.status_code != 200:
            log(f"⚠️ Falha ao aceder à API pública ({r.status_code})")
            return []

        data = r.json()
        models = [m["id"] for m in data.get("data", []) if m.get("id")]
        log(f"📊 {len(models)} modelos gratuitos obtidos via endpoint público.")
        return models
    except Exception as e:
        log(f"❌ Erro ao obter lista pública: {e}")
        return []


# ============================================
# 🤖 Testar modelo individual
# ============================================
def test_model(model_name: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a JSON-only responder."},
            {"role": "user", "content": "Return {\"title\":\"Test\",\"description\":\"Testing JSON validity\",\"body\":\"OK\"}"}
        ],
        "temperature": 0.1
    }

    start = time.time()
    try:
        r = requests.post(CHAT_URL, headers=headers, json=payload, timeout=25)
        latency = round(time.time() - start, 2)
        if r.status_code == 200:
            resp_text = r.json()["choices"][0]["message"]["content"]
            if is_valid_json(resp_text):
                return {"model": model_name, "status": "ok", "latency": latency}
            else:
                return {"model": model_name, "status": "invalid_json", "latency": latency}
        elif r.status_code == 429:
            return {"model": model_name, "status": "rate_limited"}
        elif r.status_code == 404:
            return {"model": model_name, "status": "404"}
        elif r.status_code == 402:
            return {"model": model_name, "status": "payment_required"}
        else:
            return {"model": model_name, "status": f"error_{r.status_code}"}
    except Exception as e:
        return {"model": model_name, "status": f"exception_{str(e)[:80]}"}


# ============================================
# 🚀 Execução principal
# ============================================
def main():
    log("🚀 Iniciando verificação de modelos free (TrendFind Model Checker v3.1)...")
    models = fetch_free_models()

    if not models:
        log("⚠️ Nenhum modelo gratuito encontrado — usando fallback mínimo.")
        models = ["mistralai/mistral-7b-instruct:free", "deepseek/deepseek-r1:free"]

    results = []
    ok_models = []

    for i, model in enumerate(models, 1):
        log(f"[{i}/{len(models)}] Testando {model} ...")
        res = test_model(model)
        results.append(res)

        if res["status"] == "ok":
            ok_models.append(res["model"])
            log(f"✅ {model} → OK ({res['latency']}s)")
        elif res["status"] == "payment_required":
            log(f"💰 {model} → Pago (402) — ignorado")
        elif "rate" in res["status"]:
            log(f"⚠️ {model} → Rate limited (429)")
            time.sleep(5)
        elif "404" in res["status"]:
            log(f"❌ {model} → 404 Not Found")
        else:
            log(f"❌ {model} → {res['status']}")
        time.sleep(1.5)

    # Guardar resultados
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    with open(ACTIVE_PATH, "w") as f:
        json.dump(ok_models, f, indent=2)

    log(f"🏁 Verificação concluída: {len(ok_models)} modelos válidos de {len(models)} testados.")
    log(f"📄 Resultados em: {RESULTS_PATH}")
    log(f"✅ Lista ativa em: {ACTIVE_PATH}")


if __name__ == "__main__":
    main()
