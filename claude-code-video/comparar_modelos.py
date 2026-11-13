"""Comparação de editores (26/10, pedido do dono): o MESMO material do Cardápio (roteiro, narração, fotos do vídeo
aprovado do Opus 5.5) editado por outros modelos, um depois do outro. Resultado em estado/comparacao.json.

    python comparar_modelos.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gerar  # noqa: E402

BASE = "futebolcom_ia2_20261025_231549"      # vídeo editor aprovado (Opus 5.5)
MODELOS = ["antigravity/gemini-3.8-flash-tiered", "kr/claude-sonnet-4.5", "antigravity/claude-opus-4-6-thinking"]
SAIDA = gerar.RAIZ / "estado" / "comparacao.json"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # mesma trava da tarefa ClaudeCodeVideo: ela vê o PID vivo e não começa outro vídeo junto
    gerar.TRAVA.write_text(str(__import__("os").getpid()))
    try:
        _comparar()
    finally:
        gerar.TRAVA.unlink(missing_ok=True)


def _comparar():
    base = gerar.Trabalho(gerar.TRABALHOS / BASE)
    res = json.loads(SAIDA.read_text("utf-8")) if SAIDA.exists() else {}
    for m in MODELOS:
        if res.get(m, {}).get("status") == "pronto":
            continue
        t = gerar.Trabalho.novo("futebolcom.ia2")
        for c in ("roteiro", "audio", "imgs", "origens_img"):
            t.e[c] = base.e[c]
        t.e.update(modo="editor", modelo_editor=m, feitas=["roteiro", "narracao", "imagens"], comparacao=True)
        t.salvar()
        gerar.log(f"### COMPARAÇÃO: {m} editando ({t.e['id']})")
        ini = time.time()
        for _ in range(3):                      # até 3 tentativas (render que falha volta pro modelo consertar)
            if gerar.rodar(t) or gerar.Trabalho(t.pasta).e["status"] in ("pronto", "falhou", "aguardando_cota"):
                break
        e = gerar.Trabalho(t.pasta).e
        res[m] = {"id": e["id"], "status": e["status"], "minutos": round((time.time() - ini) / 60, 1),
                  "saida": e.get("saida"), "erro": e.get("ultimo_erro"), "resumo": e.get("resumo_editor")}
        SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")
        gerar.log(f"### COMPARAÇÃO: {m} -> {e['status']} em {res[m]['minutos']} min")
        time.sleep(5)


if __name__ == "__main__":
    main()
