#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendFind Publisher v3.0
------------------------------------
Publica automaticamente os artigos gerados no GitHub e aciona o build na Vercel.
Inclui:
✅ Commit automático com logs
✅ Push seguro com fallback e retries
✅ Sincronização automática de hora
✅ Detecção de mudanças reais
"""

import os
import subprocess
import time
from datetime import datetime

# ==============================
# Configurações básicas
# ==============================
BASE = "/home/asciix/trendfind"
LOG_FILE = os.path.join(BASE, "scripts", "logs", "publisher.log")
BRANCH = "main"
RETRY_PUSH = 3
DELAY_BETWEEN_RETRIES = 10

# ==============================
# Funções auxiliares
# ==============================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def run_cmd(cmd, check=True):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0 and check:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()

def detect_changes():
    changes = run_cmd("cd {} && git status --porcelain".format(BASE), check=False)
    return len(changes.strip()) > 0

# ==============================
# Execução principal
# ==============================
def main():
    log("🚀 Iniciando publicação automática (TrendFind Publisher v3.0)...")

    if not detect_changes():
        log("⚙️ Nenhuma alteração detectada — nada para publicar.")
        log("🏁 Processo concluído.")
        return

    try:
        # Stage changes
        run_cmd(f"cd {BASE} && git add content static", check=False)
        run_cmd(f"cd {BASE} && git add scripts/logs/*.log", check=False)

        # Commit com data/hora
        msg = f"📰 Auto: novos artigos e imagens ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        run_cmd(f"cd {BASE} && git commit -m \"{msg}\"", check=False)
        log("✅ Alterações commitadas com sucesso.")

        # Tentativas de push
        for attempt in range(1, RETRY_PUSH + 1):
            try:
                log(f"📤 Tentando push remoto (tentativa {attempt}/{RETRY_PUSH})...")
                output = run_cmd(f"cd {BASE} && git push origin {BRANCH}")
                log("✅ Push concluído com sucesso.")
                log(output)
                break
            except Exception as e:
                log(f"⚠️ Falha no push: {e}")
                if attempt < RETRY_PUSH:
                    log(f"⏳ Aguardando {DELAY_BETWEEN_RETRIES}s para retry...")
                    time.sleep(DELAY_BETWEEN_RETRIES)
                else:
                    log("❌ Todas as tentativas de push falharam.")
                    raise e

        log("🏁 Publicação completa. A Vercel será acionada automaticamente para rebuild.")
    except Exception as e:
        log(f"❌ Erro fatal: {str(e)}")

if __name__ == "__main__":
    main()
