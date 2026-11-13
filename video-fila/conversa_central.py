"""conversa_central.py — o chat da dona com o MELHORADOR CENTRAL (29/10: "tenho que poder falar com ele e ver o
histórico por um chat; dizer os pontos de melhoria que eu vejo e perguntar; um botão, porque eu nem sei usar o terminal;
abrir no VS Code e ele assumir com histórico; ao fechar, ele volta a trabalhar sozinho").

Mesmo desenho do produto.conversa (linha PRODUTOS): Claude Code interativo na pasta da linha CENTRAL (o CLAUDE.md de lá
é o papel), config isolada em linhas\\CENTRAL\\.conversa (histórico continua entre aberturas: --continue), modelo pela
cadeia da config (sem Opus/Kiro). O motor (melhorador_central.py, tarefa MelhoradorCentral) NÃO depende desta conversa:
continua rodando a cada 10 min com ou sem chat aberto — o chat só lê/escreve os mesmos arquivos (HISTORICO.md,
PEDIDOS_DONA.md, DECISOES.md) e pode disparar uma passada na hora.

Uso: CONVERSAR.bat (atalho na Área de Trabalho) ou python D:\\video-fila\\conversa_central.py
No VS Code: abrir a pasta D:\\video-fila\\linhas\\CENTRAL e iniciar o Claude Code — o CLAUDE.md faz ele assumir.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"D:\postador-de-videos\bin")
from produto import motor  # noqa: E402  (gateway, chave, claude.exe e teste de modelo — os mesmos da linha PRODUTOS)

LINHA = Path(r"D:\video-fila\linhas\CENTRAL")
CONFIG_DIR = LINHA / ".conversa"
CFG = Path(r"D:\video-fila\config\melhorador_central.json")
CADEIA_PADRAO = ["gemini/gemini-3.5-flash", "agy/gemini-3.8-flash-high", "antigravity/gemini-3.8-flash-tiered"]  # 07/11: Antigravity responde "no longer supported"
ABRIR = ("A dona abriu a conversa. Leia o que mudou desde a última vez (seção 'Ao abrir' do CLAUDE.md) e diga em até "
         "6 linhas: o que o central rodou, o que as linhas decidiram, o que está medido (elegíveis, % assistido) e o "
         "que precisa dela. Depois espere o pedido dela.")
ADD = [r"D:\video-fila", r"D:\hipercool-materiais\tarefas complexas para fable 5.1", r"D:\recapd-ambientes\producao",
       r"D:\postador-de-videos", r"D:\claude-code-video", r"D:\hipercool-videos"]


def _modelo():
    """1º modelo da cadeia que responde — testados EM PARALELO com teto de 45 s (29/10: o teste em série deixava a
    janela 2 min só com 'testando…' e a dona achou que não tinha nada na tela)."""
    from concurrent.futures import ThreadPoolExecutor
    try:
        c = json.loads(CFG.read_text("utf-8"))
    except (OSError, ValueError):
        c = {}
    cadeia = list(c.get("conversa_cadeia") or CADEIA_PADRAO)
    print("Abrindo o chat do melhorador central... (testando os modelos, até 45 s)", flush=True)
    with ThreadPoolExecutor(len(cadeia)) as ex:
        ok = list(ex.map(lambda m: motor.responde(m, 45), cadeia))
    for m, r in zip(cadeia, ok):
        print(f"  {m}: {'responde' if r else 'sem resposta'}", flush=True)
    return next((m for m, r in zip(cadeia, ok) if r), None)


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
        print("Nenhum modelo respondeu agora (gateway sem crédito). O motor continua sozinho; tente o chat mais tarde.")
        input("Enter para fechar")
        return 1
    _preparar()
    c = motor.cfg()
    env = dict(os.environ, ANTHROPIC_BASE_URL=c["gateway"], ANTHROPIC_AUTH_TOKEN=c["chave"], ANTHROPIC_MODEL=m,
               ANTHROPIC_DEFAULT_OPUS_MODEL=m, ANTHROPIC_DEFAULT_SONNET_MODEL=m, ANTHROPIC_DEFAULT_HAIKU_MODEL=m,
               ANTHROPIC_SMALL_FAST_MODEL=m, CLAUDE_CONFIG_DIR=str(CONFIG_DIR),
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    env.pop("ANTHROPIC_API_KEY", None)
    base = [motor._exe(), "--model", m, "--setting-sources", "project"]
    for d in ADD:
        base += ["--add-dir", d]
    print(f"Melhorador CENTRAL — modelo {m}. Para sair: /exit (ele continua trabalhando sozinho)\n", flush=True)
    r = subprocess.call(base + ["--continue", ABRIR], cwd=str(LINHA), env=env)
    if r != 0:  # 1ª vez (nada para continuar): conversa nova
        r = subprocess.call(base + [ABRIR], cwd=str(LINHA), env=env)
    return r


if __name__ == "__main__":
    sys.exit(main())
