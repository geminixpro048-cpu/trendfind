#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendFind Autopilot v5.0
------------------------------------
Rotação de chaves, download automático de imagens e SEO audit.
"""

import os
import re
import json
import time
import random
import requests
from datetime import datetime
from dotenv import load_dotenv

# =====================================================
# Configuração base
# =====================================================
BASE = "/home/asciix/trendfind"
SCRIPT_PATH = os.path.join(BASE, "scripts")
CONTENT_PATH = os.path.join(BASE, "content", "posts")
STATIC_IMAGES = os.path.join(BASE, "static", "images")
LOG_PATH = os.path.join(SCRIPT_PATH, "logs")

os.makedirs(LOG_PATH, exist_ok=True)
os.makedirs(CONTENT_PATH, exist_ok=True)
os.makedirs(STATIC_IMAGES, exist_ok=True)

load_dotenv(os.path.join(BASE, ".env"))

API_KEYS = os.getenv("OPENROUTER_API_KEYS", "").split(",")
if not API_KEYS or not API_KEYS[0].startswith("sk-or-v1-"):
    print("❌ Nenhuma OPENROUTER_API_KEYS válida encontrada no .env")
    exit(1)

UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_FILE = os.path.join(SCRIPT_PATH, "models_valid.json")
LAST_INDEX_FILE = os.path.join(SCRIPT_PATH, "last_model_index.json")
LOG_FILE = os.path.join(LOG_PATH, "autopilot.log")

ARTICLES_PER_RUN = 1
DELAY_BETWEEN_ARTICLES = 0
COOLDOWN_429 = 10

TOPICS = [
    "Artificial Intelligence", "Sustainability Tech", "Green Energy",
    "Smart Cities", "Digital Transformation", "Quantum Computing",
    "Blockchain", "Metaverse", "Cybersecurity", "Futurism",
    "Space Exploration", "Augmented Reality", "BioTech", "Web3"
]

# =====================================================
# Utilitários
# =====================================================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def clean_json(text):
    return text.strip().replace("```json", "").replace("```", "")

def is_valid_json(text):
    try:
        j = json.loads(clean_json(text))
        return all(k in j for k in ["title", "description", "body"])
    except Exception:
        return False

def generate_slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

def get_next_model():
    with open(MODELS_FILE) as f:
        models = json.load(f)
    idx = 0
    if os.path.exists(LAST_INDEX_FILE):
        try:
            with open(LAST_INDEX_FILE) as f:
                idx = json.load(f).get("index", 0)
        except:
            idx = 0
    model = models[idx % len(models)]
    next_idx = (idx + 1) % len(models)
    with open(LAST_INDEX_FILE, "w") as f:
        json.dump({"index": next_idx}, f)
    return model

# =====================================================
# API Keys manager
# =====================================================
class KeyManager:
    def __init__(self, keys):
        self.keys = [k.strip() for k in keys if k.strip()]
        self.index = 0

    def current(self):
        return self.keys[self.index % len(self.keys)]

    def next(self):
        self.index = (self.index + 1) % len(self.keys)
        key = self.current()
        log(f"🔄 Alternando para próxima API key ({self.index+1}/{len(self.keys)}): ...{key[-6:]}")
        return key

KEY_MANAGER = KeyManager(API_KEYS)

# =====================================================
# Unsplash image
# =====================================================
def get_unsplash_image(query):
    if not UNSPLASH_KEY:
        log("⚠️ Nenhuma chave UNSPLASH definida — imagem padrão usada.")
        return "/images/default.jpg"
    try:
        r = requests.get(
            f"https://api.unsplash.com/photos/random?query={query}&orientation=landscape&client_id={UNSPLASH_KEY}",
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("urls", {}).get("regular", "/images/default.jpg")
        else:
            log(f"⚠️ Unsplash retornou {r.status_code}")
    except Exception as e:
        log(f"⚠️ Erro ao obter imagem: {str(e)[:100]}")
    return "/images/default.jpg"

def download_image(url, slug):
    if not url.startswith("http"):
        return
    try:
        path = os.path.join(STATIC_IMAGES, f"{slug}.jpg")
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            log(f"🖼️ Imagem salva: {path}")
        else:
            log(f"⚠️ Falha ao descarregar imagem ({r.status_code})")
    except Exception as e:
        log(f"⚠️ Falha ao baixar imagem: {str(e)[:100]}")

# =====================================================
# SEO check
# =====================================================
def seo_check(title, description):
    if len(title) < 30 or len(title) > 70:
        log(f"⚠️ [SEO] Título fora do intervalo ideal (30–70): {len(title)} chars.")
    if len(description) < 50 or len(description) > 160:
        log(f"⚠️ [SEO] Descrição fora do intervalo ideal (50–160): {len(description)} chars.")

# =====================================================
# Geração de artigo
# =====================================================
def generate_article():
    topic = random.choice(TOPICS)
    model = get_next_model()
    api_key = KEY_MANAGER.current()

    log(f"🚀 Iniciando geração automática (TrendFind Autopilot v5.0)...")
    log(f"🧠 Tópico: {topic}")
    log(f"💡 Modelo: {model}")
    log(f"🔑 API ativa: ...{api_key[-6:]}")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = (
        f"Write a JSON blog post about '{topic}' with fields: "
        f"title, description, tags, and body. The body must be Markdown with headings and 5+ paragraphs."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional tech writer who outputs only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    try:
        r = requests.post(CHAT_URL, headers=headers, json=payload, timeout=90)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            if not is_valid_json(content):
                log(f"⚠️ {model} retornou JSON inválido — tentar próximo modelo...")
                return None
            data = json.loads(clean_json(content))
            save_article(data, topic, model)
            return True
        elif r.status_code == 429:
            log(f"⚠️ {model} → Rate limit (429). Espera {COOLDOWN_429}s + troca chave.")
            time.sleep(COOLDOWN_429)
            KEY_MANAGER.next()
            return None
        elif r.status_code in [404, 402]:
            log(f"⚠️ {model} falhou ({r.status_code}) — tentar próximo modelo...")
            return None
        else:
            log(f"❌ Erro {r.status_code}: {r.text[:120]}")
            return None
    except Exception as e:
        log(f"❌ Exceção: {str(e)[:100]}")
        return None

def save_article(data, topic, model):
    title = data["title"]
    desc = data.get("description", "")
    tags = data.get("tags", [topic])
    slug = generate_slug(title)
    seo_check(title, desc)
    image_url = get_unsplash_image(topic)
    download_image(image_url, slug)

    filename = os.path.join(CONTENT_PATH, f"{slug}.md")
    date = datetime.now().isoformat()

    frontmatter = f"""---
title: "{title}"
date: {date}
draft: false
slug: "{slug}"
description: "{desc}"
keywords: {json.dumps(tags)}
tags: {json.dumps(tags)}
featured_image: "/images/{slug}.jpg"
canonicalURL: "https://www.trendfind.online/posts/{slug}/"
og_title: "{title}"
og_description: "{desc}"
og_image: "/images/{slug}.jpg"
twitter_card: "summary_large_image"
twitter_title: "{title}"
twitter_description: "{desc}"
twitter_image: "/images/{slug}.jpg"
model_used: "{model}"
---
{data['body']}
"""
    with open(filename, "w") as f:
        f.write(frontmatter)
    log(f"✅ Artigo criado e salvo: {filename}")

# =====================================================
# Main
# =====================================================
if __name__ == "__main__":
    for i in range(ARTICLES_PER_RUN):
        ok = False
        for _ in range(10):
            if generate_article():
                ok = True
                break
        if not ok:
            log("❌ Nenhum modelo gerou artigo válido.")
        if i < ARTICLES_PER_RUN - 1:
            log(f"🕐 Aguardando {DELAY_BETWEEN_ARTICLES}s...")
            time.sleep(DELAY_BETWEEN_ARTICLES)
    log("🏁 Processo concluído.")
