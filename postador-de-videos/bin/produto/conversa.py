"""Chat da dona com o MELHORADOR no terminal (27/10: "abrir um chat pra falar com ele quando eu quiser; já abre na
conversa, tudo pronto, só pra eu digitar"). Claude Code interativo na pasta da linha (CLAUDE.md lá = papel e regras),
modelo escolhido pelo teste rápido na cadeia de config\\melhorador_produtos.json -> "conversa" (sem Opus/Kiro).
Config isolada em linhas\\PRODUTOS\\.conversa: sem os hooks/plugins dos chats do VS Code (menos RAM) e no D:.
Uso: CONVERSAR_MELHORADOR.bat (ou python -m produto.conversa)."""
import json
import os
import subprocess
import sys
from pathlib import Path

from produto import motor

LINHA = Path(r"D:\video-fila\linhas\PRODUTOS")
CONFIG_DIR = LINHA / ".conversa"
RAIZ = Path(__file__).resolve().parents[2]
CADEIA_PADRAO = ["agy/gemini-3.8-flash-high", "gemini/gemini-3.5-flash"]
ABRIR = ("A dona abriu a conversa. Leia o que mudou desde a última vez (veja 'Ao abrir' no CLAUDE.md) e diga em até "
         "6 linhas onde estamos e o que precisa dela. Depois espere o pedido dela.")


def _modelo():
    c = json.loads((RAIZ / "config" / "melhorador_produtos.json").read_text("utf-8"))
    cadeia = (c.get("conversa") or {}).get("cadeia") or CADEIA_PADRAO
    fora = set(c.get("modelos_desligados", []))
    for m in cadeia:
        if m in fora:
            continue
        print(f"testando {m}...", flush=True)
        if motor.responde(m, 90 if "argon" in m else 60):
            return m
    return None


def _preparar():
    CONFIG_DIR.mkdir(exist_ok=True)
    arq = CONFIG_DIR / ".claude.json"
    d = json.loads(arq.read_text("utf-8")) if arq.exists() else {}
    d["hasCompletedOnboarding"] = True
    d.setdefault("projects", {}).setdefault(str(LINHA).replace("\\", "/"), {})["hasTrustDialogAccepted"] = True
    arq.write_text(json.dumps(d, indent=1), "utf-8")


def main():
    m = _modelo()
    if not m:
        print("Nenhum modelo respondeu agora (Gemini 3.8 / API). Tente de novo em alguns minutos.")
        input("Enter para fechar")
        return 1
    _preparar()
    c = motor.cfg()
    env = dict(os.environ, ANTHROPIC_BASE_URL=c["gateway"], ANTHROPIC_AUTH_TOKEN=c["chave"], ANTHROPIC_MODEL=m,
               ANTHROPIC_DEFAULT_OPUS_MODEL=m, ANTHROPIC_DEFAULT_SONNET_MODEL=m, ANTHROPIC_DEFAULT_HAIKU_MODEL=m,
               ANTHROPIC_SMALL_FAST_MODEL=m, CLAUDE_CONFIG_DIR=str(CONFIG_DIR),
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    env.pop("ANTHROPIC_API_KEY", None)
    base = [motor._exe(), "--model", m, "--setting-sources", "project", "--add-dir", str(RAIZ),
            "--add-dir", r"D:\hipercool-materiais\produtos_ultimo_video", "--add-dir", r"D:\gemini-argo"]
    print(f"Melhorador PRODUTOS — modelo {m}. Para sair: /exit\n", flush=True)
    r = subprocess.call(base + ["--continue", ABRIR], cwd=str(LINHA), env=env)
    if r != 0:  # 1ª vez (nada para continuar): conversa nova
        r = subprocess.call(base + [ABRIR], cwd=str(LINHA), env=env)
    return r


if __name__ == "__main__":
    sys.exit(main())
