#!/usr/bin/env python3
import os, requests, random, json, re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEYS = [
    os.getenv("OPENROUTER_API_KEY"),
    os.getenv("OPENROUTER_API_KEY_ALT")
]
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

CONTENT_DIR = "/home/asciix/trendfind/content/posts"
IMAGE_DIR = "/home/asciix/trendfind/static/images"
BASE_URL = "https://www.trendfind.online"
MODELS_FILE = "/home/asciix/trendfind/scripts/models_valid.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_random_topic():
    topics = [
        "Artificial Intelligence", "Sustainability Tech", "Cybersecurity", "Web3",
        "Green Energy", "Futurism", "Quantum Computing", "Blockchain",
        "BioTech", "Smart Cities", "Digital Transformation"
    ]
    return random.choice(topics)

def generate_with_openrouter(topic):
    with open(MODELS_FILE) as f:
        models = json.load(f)
    for model in models:
        api_key = random.choice([k for k in API_KEYS if k])
        if not api_key:
            continue
        log(f"💡 Using model: {model}")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": BASE_URL,
            "X-Title": "TrendFind Autopilot"
        }
        payload = {
            "model": model,
            "input": f"Write a detailed blog post in Markdown about {topic}, with title, description, tags, and body. Output JSON like {{'title': '', 'description': '', 'tags': [], 'body': ''}}"
        }
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            if r.status_code != 200:
                log(f"⚠️ {model} failed ({r.status_code}) — trying next")
                continue
            text = r.text
            match = re.search(r"\{.*\}", text, re.S)
            if not match:
                log(f"⚠️ Invalid JSON from {model}")
                continue
            data = json.loads(match.group(0))
            return data
        except Exception as e:
            log(f"⚠️ {model} error: {e}")
    return None

def get_unsplash_image(query, slug):
    if not UNSPLASH_ACCESS_KEY:
        return f"/images/{slug}.jpg"
    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={UNSPLASH_ACCESS_KEY}&orientation=landscape"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        image_url = data["urls"]["regular"]
        image_path = os.path.join(IMAGE_DIR, f"{slug}.jpg")
        img_data = requests.get(image_url).content
        with open(image_path, "wb") as f:
            f.write(img_data)
        log(f"🖼️ Saved image: {image_path}")
        return f"/images/{slug}.jpg"
    return "/images/default.jpg"

def slugify(text):
    return re.sub(r"[^a-z0-9\-]+", "-", text.lower()).strip("-")

def save_article(data, topic):
    title = data.get("title") or topic
    slug = slugify(title)
    description = data.get("description", "")
    tags = data.get("tags", [])
    body = data.get("body", "")
    img_path = get_unsplash_image(topic, slug)
    date_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+01:00")

    frontmatter = f"""---
title: "{title}"
date: {date_str}
draft: false
slug: "{slug}"
description: "{description}"
keywords: {tags}
tags: {tags}
featured_image: "{img_path}"
images: ["{img_path}"]
canonicalURL: "{BASE_URL}/posts/{slug}/"
og_title: "{title}"
og_description: "{description}"
og_image: "{img_path}"
twitter_card: "summary_large_image"
twitter_title: "{title}"
twitter_description: "{description}"
twitter_image: "{img_path}"
---
{body}
"""
    file_path = os.path.join(CONTENT_DIR, f"{slug}.md")
    with open(file_path, "w") as f:
        f.write(frontmatter)
    log(f"✅ Article created and saved: {file_path}")
    return file_path

if __name__ == "__main__":
    log("🚀 Starting generation (TrendFind Autopilot v5.1)...")
    topic = get_random_topic()
    log(f"🧠 Topic: {topic}")
    data = generate_with_openrouter(topic)
    if not data:
        log("⚠️ Fallback content used.")
        data = {
            "title": f"{topic} Overview",
            "description": f"Latest insights about {topic}.",
            "tags": [topic],
            "body": f"# {topic}\n\nAI-generated overview of {topic}."
        }
    save_article(data, topic)
    log("🏁 Done.")
