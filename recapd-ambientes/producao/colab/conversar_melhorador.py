"""conversar_melhorador.py — dona 27/10: "abrir um chat pra falar com o melhorador, que pareça a conversa onde ele
está, no terminal, já aberto na conversa e pronto pra digitar".

Mostra onde o melhorador está (ligado?, últimas voltas, decisões, consertos, GPUs, pedidos) e abre o Claude Code no
terminal numa conversa FIXA (mesmo id sempre: a 1ª vez cria, depois continua de onde parou), com o prompt de
linhas\\LONGOS\\PROMPT_CONVERSA.md e só os modelos permitidos (sem Opus/Kiro). Atalho: CONVERSAR_MELHORADOR.bat.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import juri_longo  # noqa: E402
import melhorador_longo as ml  # noqa: E402

SESSAO = "6c0f3a52-8d1e-4b7a-9e2c-4d1b0a7e5f31"  # id fixo da conversa com o melhorador
MARCA = ml.LINHA / ".conversa_criada"
MODELO = os.environ.get("MELHORADOR_CHAT_MODELO", "agy/gemini-3.8-flash-high")


def resumo():
    c = ml._ler(ml.CFG, {})
    est = ml._ler(ml.ESTADO, {})
    print("=" * 78)
    print(f" MELHORADOR DO RECAP LONGO — {'LIGADO' if ml.ligado() else 'DESLIGADO (só liga no sinal da dona)'}")
    print("=" * 78)
    vids = list((est.get("videos") or {}).values())[-3:]
    for v in vids:
        print(f" vídeo {v['ficha'][:50]}: nota {v.get('nota')}")
    for d in (est.get("decisoes") or [])[-1:]:
        print(f" última decisão ({d['em'][:16]}, {d['modelo']}): {str((d.get('resposta') or {}).get('diagnostico'))[:220]}")
    for m in (est.get("mudancas") or [])[-3:]:
        print(f" mudança {m['chave']}: {m['estado']}")
    fila = [p for p in est.get("propostas", []) if p.get("estado") == "nova"]
    print(f" consertos de código na fila: {len(fila)} (modelo: {(c.get('codigo') or {}).get('modelo')})")
    g = (est.get("gpu") or {}).get("ultimas")
    if g:
        print(f" GPUs: {g['com_conta']} de {g['total']} trabalhando (visto {g['em'][11:16]})")
    try:
        linhas = ml.LOG.read_text(encoding="utf-8").splitlines()[-6:]
        print(" últimas linhas do log:")
        for l in linhas:
            print("   " + l[:150])
    except OSError:
        pass
    print("-" * 78)
    print(" Pedido novo: é só digitar. Ele grava em PEDIDOS_DONA.md e usa em toda decisão.  Sair: /exit")
    print("-" * 78)


def main():
    resumo()
    cfg = json.loads(juri_longo.CCV_CONFIG.read_text("utf-8"))
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["gateway"], ANTHROPIC_AUTH_TOKEN=cfg["chave"], ANTHROPIC_MODEL=MODELO,
               ANTHROPIC_DEFAULT_OPUS_MODEL=MODELO, ANTHROPIC_DEFAULT_SONNET_MODEL=MODELO,
               ANTHROPIC_DEFAULT_HAIKU_MODEL=MODELO, ANTHROPIC_SMALL_FAST_MODEL=MODELO,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    env.pop("ANTHROPIC_API_KEY", None)
    cmd = [juri_longo._exe(), "--model", MODELO, "--name", "Melhorador LONGOS",
           "--append-system-prompt", (ml.LINHA / "PROMPT_CONVERSA.md").read_text(encoding="utf-8"),
           "--add-dir", str(ml.LINHA), "--add-dir", str(AQUI.parent), "--add-dir", r"D:\gemini-argo"]
    cmd += ["--resume", SESSAO] if MARCA.exists() else ["--session-id", SESSAO]
    MARCA.write_text("1", encoding="utf-8")
    # o sem_janela (vem com o juri_longo) põe CREATE_NO_WINDOW quando creationflags é 0 e o chat sumiria do
    # terminal; CREATE_UNICODE_ENVIRONMENT (0x400) não muda nada e mantém o console
    sys.exit(subprocess.call(cmd, env=env, cwd=str(ml.LINHA), creationflags=0x400 if sys.platform == "win32" else 0))


if __name__ == "__main__":
    main()
