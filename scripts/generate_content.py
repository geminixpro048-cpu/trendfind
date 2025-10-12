#!/usr/bin/env python3
# TrendFind Autopilot v5.1
# Gera artigos automáticos (texto + imagem) com modelos gratuitos do OpenRouter

import os
import random
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from time import sleep

# Caminhos
BASE_DIR = "/home/asciix/trendfind"
CONTENT_DIR = f"{BASE_DIR}/content/posts"
IMAGE_DIR = f"{BASE_DIR}/static/images"
MODEL_FILE = f"{BASE_DIR}/scripts/models_valid.json"

# Configurações principais
SITE_URL = "https://www.trendfind.online"
MAX_MODELS = 3  # tenta até 3 modelos antes de fallback textual
ARTICLE_TOPICS = [
    "Artificial Intelligence", "Machine Learning", "Blockchain",
    "Cybersecurity", "Green Energy", "Futurism", "Smart Cities",
    "Quantum Computing", "Digital Transformation", "Web3"
]

# ---- Funções utilitárias ----

def log(msg):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")

def load_api_keys():
    """Carrega múltiplas API Keys do .env"""
    load_dotenv()
    keys = []
    for i in range(1, 6):
        k = os.getenv(f"OPENROUTER_API_KEY_{i}")
        if k:
            keys.append(k.strip())
    if not keys:
        # fallback para a variável antiga
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            keys.append(key.strip())
    if not keys:
        log("❌ Nenhuma chave OPENROUTER_API_KEY encontrada no .env")
        exit(1)
    return keys

def next_key(keys, current):
    idx = (keys.index(current) + 1) % len(keys)
    return keys[idx]

def generate_image(slug, topic):
    """Gera uma imagem via Unsplash"""
    url = f"https://source.unsplash.com/1200x630/?{topic.replace(' ', '%20')}"
    image_path = f"{IMAGE_DIR}/{slug}.jpg"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(r.content)
            log(f"🖼️  Imagem salva: {image_path}")
        else:
            log(f"⚠️  Falha ao obter imagem ({r.status_code}) → usando placeholder.")
    except Exception as e:
        log(f"⚠️  Erro ao gerar imagem: {e}")
    return image_path

def slugify(text):
    return text.lower().replace(" ", "-").replace(":", "").replace("’", "").replace("'", "")

# ---- Função principal ----

def main():
    log("🚀 Iniciando geração automática (TrendFind Autopilot v5.1)...")

    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    api_keys = load_api_keys()
    current_key = api_keys[0]
    headers = {"Authorization": f"Bearer {current_key}", "Content-Type": "application/json"}

    # Escolher tópico aleatório
    topic = random.choice(ARTICLE_TOPICS)
    log(f"🧠 Tópico escolhido: {topic}")

    # Carregar modelos válidos
    models = []
    try:
        with open(MODEL_FILE, "r") as f:
            models = json.load(f)
    except Exception:
        log("⚠️  Falha ao carregar models_valid.json, usando fallback.")
        models = ["mistralai/mistral-7b-instruct:free", "deepseek/deepseek-r1:free"]

    slug = slugify(topic)
    filename = f"{CONTENT_DIR}/{slug}.md"
    image_path = generate_image(slug, topic)

    content = None
    model_used = None

    for model in models[:MAX_MODELS]:
        log(f"💡 Tentando modelo: {model}")
        headers["Authorization"] = f"Bearer {current_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Write a detailed SEO-friendly tech article in Markdown. Include title, description, tags and body as JSON."},
                {"role": "user", "content": f"Generate a complete tech article about {topic}. Format strictly as JSON with fields title, description, tags, and body."}
            ],
            "max_tokens": 1200,
            "temperature": 0.8,
        }

        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=40)
            if resp.status_code == 429:
                log(f"⚠️  {model} → Rate limit (429). Mudando de chave...")
                current_key = next_key(api_keys, current_key)
                sleep(3)
                continue
            elif resp.status_code != 200:
                log(f"⚠️  {model} → Falhou ({resp.status_code}) {resp.text[:80]}")
                continue

            text = resp.json()["choices"][0]["message"]["content"]
            try:
                data = json.loads(text)
                content = data
                model_used = model
                break
            except Exception:
                log(f"⚠️  {model} retornou JSON inválido, ignorando.")
                continue
        except Exception as e:
            log(f"⚠️  Erro ao contactar modelo {model}: {e}")

    if not content:
        log("❗ Nenhum modelo válido → usando fallback textual.")
        content = {
            "title": topic,
            "description": f"Latest insights about {topic}.",
            "tags": [topic],
            "body": f"# {topic}\n\nAutomated article generation failed. This is a placeholder content for {topic}."
        }

    # ---- Cria o artigo Markdown ----
    title = content.get("title", topic)
    description = content.get("description", f"Insights about {topic}.")
    tags = content.get("tags", [topic])
    date = datetime.now().isoformat()
    canonical = f"{SITE_URL}/posts/{slug}/"

    with open(filename, "w") as f:
        f.write(f"""---
title: "{title}"
date: {date}
draft: false
slug: "{slug}"
description: "{description}"
keywords: {tags}
tags: {tags}
images: ["/images/{slug}.jpg"]
canonicalURL: "{canonical}"
og_title: "{title}"
og_description: "{description}"
og_image: "/images/{slug}.jpg"
twitter_card: "summary_large_image"
twitter_title: "{title}"
twitter_description: "{description}"
twitter_image: "/images/{slug}.jpg"
author: "TrendFind Autopilot"
---

{content.get("body", "")}
""")

    log(f"✅ Artigo criado: {filename}")
    log("🏁 Processo concluído.")


if __name__ == "__main__":
    main()
