#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendFind Autopilot v5.2 — geração automática de artigos com imagens e SEO fixo
Força prefixo /images/ em todas as imagens.
"""

import os
import random
import requests
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_API_KEY"),
    os.getenv("OPENROUTER_API_KEY_2"),
]

MODELS_PATH = "/home/asciix/trendfind/scripts/models_valid.json"
BASE_PATH = "/home/asciix/trendfind"
SITE_URL = "https://www.trendfind.online"

TOPICS = [
    "Artificial Intelligence", "Smart Cities", "Digital Transformation",
    "Futurism", "Green Energy", "BioTech", "Web3", "Cybersecurity",
    "Blockchain", "Sustainability Tech", "Quantum Computing"
]


def choose_api_key():
    """Alterna entre múltiplas chaves API."""
    key = random.choice([k for k in OPENROUTER_KEYS if k])
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔑 API Key ativa: ...{key[-6:]}")
    return key


def choose_model():
    """Escolhe modelo aleatório a partir do ficheiro models_valid.json"""
    import json
    try:
        with open(MODELS_PATH, "r") as f:
            models = json.load(f)
        return random.choice(models)
    except Exception:
        return "mistralai/mistral-7b-instruct:free"


def generate_article(topic):
    """Gera conteúdo via OpenRouter"""
    key = choose_api_key()
    model = choose_model()
    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": SITE_URL,
        "X-Title": "TrendFind Autopilot"
    }

    prompt = f"""
    Write a complete Markdown blog article about {topic}.
    Include title, description, tags, and body in JSON format like:
    {{
      "title": "...",
      "description": "...",
      "tags": ["tag1","tag2"],
      "body": "# Heading..."
    }}
    """

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1200,
            },
            timeout=60
        )
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content
    except Exception as e:
        print(f"❌ Erro: {e}")
        return ""


def save_article(slug, title, description, tags, body):
    """Guarda artigo com front matter fixo e imagens com /images/"""
    os.makedirs(f"{BASE_PATH}/content/posts", exist_ok=True)

    image_name = f"{slug}.jpg"
    image_url = f"/images/{image_name}"

    fm = f"""---
title: "{title}"
date: {datetime.now().isoformat()}
draft: false
slug: "{slug}"
description: "{description}"
keywords: {tags}
tags: {tags}
featured_image: "{image_url}"
canonicalURL: "{SITE_URL}/posts/{slug}/"
og_title: "{title}"
og_description: "{description}"
og_image: "{image_url}"
twitter_card: "summary_large_image"
twitter_title: "{title}"
twitter_description: "{description}"
twitter_image: "{image_url}"
---
{body}
"""
    path = f"{BASE_PATH}/content/posts/{slug}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Artigo criado e salvo: {path}")


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando geração automática (TrendFind Autopilot v5.2)...")

    topic = random.choice(TOPICS)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 Tópico: {topic}")

    content = generate_article(topic)
    if not content:
        print("❌ Nenhum conteúdo gerado.")
        return

    # Parse simplificado do JSON
    import json
    try:
        data = json.loads(content.strip("` \n"))
        title = data.get("title", topic)
        description = data.get("description", f"Latest insights about {topic}.")
        tags = data.get("tags", [topic])
        body = data.get("body", f"# {topic}\n\n{content}")
    except Exception:
        title = topic
        description = f"Latest insights about {topic}."
        tags = [topic]
        body = f"# {topic}\n\n{content}"

    slug = title.lower().replace(" ", "-").replace(":", "").replace("/", "")
    save_article(slug, title, description, tags, body)

    # Geração da imagem
    img_path = f"{BASE_PATH}/static/images/{slug}.jpg"
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    unsplash_url = f"https://source.unsplash.com/featured/1200x630/?{topic.replace(' ', ',')}"
    try:
        img_data = requests.get(unsplash_url).content
        with open(img_path, "wb") as f:
            f.write(img_data)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🖼️ Imagem salva: {img_path}")
    except Exception as e:
        print(f"⚠️ Falha ao gerar imagem: {e}")


if __name__ == "__main__":
    main()
