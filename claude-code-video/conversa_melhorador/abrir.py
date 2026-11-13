"""Abre o chat do melhorador no terminal, já na última conversa (ou numa nova na 1ª vez)."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent))
import motor  # noqa: E402

cfg = json.loads((PASTA.parent / "config.json").read_text("utf-8"))
modelo = os.environ.get("MODELO_MELHORADOR", "argon-gemini")
env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["gateway"], ANTHROPIC_AUTH_TOKEN=cfg["chave"], ANTHROPIC_MODEL=modelo,
           ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
           ANTHROPIC_DEFAULT_HAIKU_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
           CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
env.pop("ANTHROPIC_API_KEY", None)
exe = motor._exe()
ini = time.time()
rc = subprocess.call([exe, "--continue"], cwd=PASTA, env=env)
if rc and time.time() - ini < 10:  # 1ª vez: não há conversa para continuar
    subprocess.call([exe, "Como está o melhorador? Resuma o que ele fez, o que está em teste e os meus pedidos."],
                    cwd=PASTA, env=env)
