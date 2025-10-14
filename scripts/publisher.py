#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendFind Publisher v3.1
-------------------------------------------------
Publica automaticamente novos artigos:
1. Executa o verificador de imagens (check_images.py)
2. Faz commit e push para GitHub
3. Dispara rebuild automático no Vercel
"""

import os
import subprocess
from datetime import datetime

BASE_PATH = "/home/asciix/trendfind"
REPO_PATH = BASE_PATH
SCRIPTS_PATH = os.path.join(BASE_PATH, "scripts")

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def run_cmd(cmd, cwd=None):
    """Executa comando shell e devolve código de saída."""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.returncode

def run_image_check():
    """Executa o verificador de imagens antes do push"""
    check_script = os.path.join(SCRIPTS_PATH, "check_images.py")
    if os.path.exists(check_script):
        log("🖼️  Executando verificação de imagens antes do commit...")
        code = run_cmd(f"python3 {check_script}")
        if code == 0:
            log("✅ Verificação de imagens concluída com sucesso.")
        else:
            log("⚠️  Verificação de imagens concluída com avisos.")
    else:
        log("❌ check_images.py não encontrado, a publicar mesmo assim.")

def publish():
    """Fluxo principal: add → commit → push"""
    log("🚀 Iniciando publicação automática (TrendFind Publisher v3.1)...")

    # 1️⃣ Garante que não há build antigo
    run_cmd("rm -rf public", cwd=REPO_PATH)
    run_cmd("hugo --minify", cwd=REPO_PATH)

    # 2️⃣ Corre o verificador de imagens
    run_image_check()

    # 3️⃣ Faz commit e push
    run_cmd("git add -A", cwd=REPO_PATH)
    commit_msg = "📰 AutoPublish: novos artigos e verificação de imagens"
    run_cmd(f'git commit -m "{commit_msg}"', cwd=REPO_PATH)
    log("📤 Tentando push remoto (tentativa 1/3)...")

    push_code = run_cmd("git push origin main", cwd=REPO_PATH)
    if push_code == 0:
        log("✅ Push concluído com sucesso.")
    else:
        log("⚠️  Falha no push remoto. Tenta novamente manualmente.")

    log("🏁 Publicação completa. O Vercel fará rebuild automático.")

if __name__ == "__main__":
    publish()
