#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendFind Image Verifier v2.0
----------------------------------
Verifica se todas as imagens referenciadas nos posts existem no /static/images/,
ou são URLs externas válidas (Unsplash, etc.).
Se alguma imagem local estiver em falta, substitui por /images/default.jpg.
"""

import os
import re
import requests
from datetime import datetime

BASE_PATH = "/home/asciix/trendfind"
POSTS_PATH = os.path.join(BASE_PATH, "content", "posts")
STATIC_IMAGES = os.path.join(BASE_PATH, "static", "images")
DEFAULT_IMAGE = "/images/default.jpg"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def image_exists_locally(image_path):
    """Verifica se uma imagem local existe no /static/images/"""
    if image_path.startswith("/images/"):
        full_path = os.path.join(STATIC_IMAGES, os.path.basename(image_path))
        return os.path.exists(full_path)
    return True  # se não for local, assume válido

def url_exists(url):
    """Verifica se uma imagem externa (Unsplash, etc.) está acessível"""
    try:
        r = requests.head(url, timeout=8)
        return r.status_code == 200
    except Exception:
        return False

def process_post(post_path):
    with open(post_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'featured_image:\s*"(.*?)"', content)
    if not match:
        log(f"⚠️  Sem imagem → {os.path.basename(post_path)}")
        return False

    image = match.group(1).strip()
    changed = False

    # Verificar imagem
    if image.startswith("http"):
        if not url_exists(image):
            log(f"❌ URL quebrado: {image} → default")
            content = re.sub(r'featured_image:\s*".*?"', f'featured_image: "{DEFAULT_IMAGE}"', content)
            changed = True
        else:
            log(f"🌍 Externa OK: {os.path.basename(post_path)} → {image}")
    else:
        if not image_exists_locally(image):
            log(f"❌ Local inexistente: {image} → default")
            content = re.sub(r'featured_image:\s*".*?"', f'featured_image: "{DEFAULT_IMAGE}"', content)
            changed = True
        else:
            log(f"🖼️ Local OK: {os.path.basename(post_path)} → {image}")

    if changed:
        with open(post_path, "w", encoding="utf-8") as f:
            f.write(content)
        log(f"💾 Corrigido: {os.path.basename(post_path)}")

    return True

def main():
    log("🚀 Iniciando verificação de imagens (TrendFind Image Verifier v2.0)...")

    if not os.path.exists(POSTS_PATH):
        log("❌ Diretório de posts não encontrado.")
        return

    posts = [os.path.join(POSTS_PATH, f) for f in os.listdir(POSTS_PATH) if f.endswith(".md")]
    total, ok = len(posts), 0

    for p in posts:
        if process_post(p):
            ok += 1

    log(f"🏁 Verificação concluída: {ok}/{total} posts processados.")
    log("✅ Todas as imagens inexistentes foram substituídas por /images/default.jpg, se necessário.")

if __name__ == "__main__":
    main()
