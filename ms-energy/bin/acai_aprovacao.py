# -*- coding: utf-8 -*-
r"""acai_aprovacao.py — ponte da fila do açaí com o Painel de Clientes (dona 14/11: "o painel pra colocar os posts pra
aprovar é https://clientes.opus-sem-limites.com.br/ na conta do açaí; os que eles aprovarem já posta automático").

Uma passada (tarefa AcaiAprovacao, 30/30 min, oculta):
  1) ENVIA: item pronto da fila_para_postar (reel_*.mp4/reel.mp4 ou carrossel com 1.jpg..N.jpg + legenda.txt), sem
     postado.json e sem enviado_painel.json -> POST /api/aprovacao/enviar (cliente "precioso"). Máx. ACAI_ENVIAR_MAX
     por passada (padrão 4).
  2) POSTA: item que o cliente APROVOU no painel -> acai_postar_fila.postar(pasta) (Instagram do açaí) e marca
     "postado" no painel com o link. Recusado = anota recusado.json na pasta e não posta.
Desligar: env ACAI_APROVACAO=0 (ou desativar a tarefa). Só envio, sem postar: ACAI_POSTAR_APROVADOS=0.
Log: D:\ms-energy\logs\acai_aprovacao.log
"""
import base64
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

FILA = Path(r"D:\ms-energy\videos\acai\fila_para_postar")
PAINEL = "https://clientes.opus-sem-limites.com.br"
CHAVES = Path(r"D:\painel-clientes\segredos\chaves.json")
CLIENTE = "precioso"
LOG = Path(r"D:\ms-energy\logs\acai_aprovacao.log")


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        try:
            print(linha, flush=True)
        except (OSError, ValueError):
            pass


def _api(rota, dados=None):
    chave = json.loads(CHAVES.read_text("utf-8"))["admin"]
    req = urllib.request.Request(f"{PAINEL}{rota}", data=None if dados is None else json.dumps(dados).encode(),
                                 headers={"Content-Type": "application/json", "X-Chave": chave,
                                          "User-Agent": "painel-clientes-acai/1"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())


def _arquivos(p):
    """(tipo, [arquivos]) do item pronto, ou None."""
    reel = next((x for x in [p / "reel.mp4", *sorted(p.glob("reel_*.mp4"))] if x.exists()), None)
    if reel:
        return "reel", [reel]
    imgs = sorted((x for x in p.glob("*.jpg") if x.stem.isdigit()), key=lambda x: int(x.stem))
    return ("carrossel", imgs) if imgs else None


def enviar(maximo):
    n = 0
    for p in sorted(FILA.iterdir()):
        if n >= maximo:
            break
        if not p.is_dir() or (p / "postado.json").exists() or (p / "enviado_painel.json").exists():
            continue
        if not (p / "legenda.txt").exists():
            continue
        a = _arquivos(p)
        if not a:
            continue
        tipo, arqs = a
        leg = (p / "legenda.txt").read_text("utf-8")
        try:
            import acai_postar_fila
            leg = acai_postar_fila.legenda_final(leg)
        except Exception:  # noqa: BLE001 — sem o rodapé, a legenda crua serve pra aprovação
            pass
        iid = p.name[:80]
        r = _api("/api/aprovacao/enviar", {
            "cliente": CLIENTE, "id": iid, "tipo": tipo, "legenda": leg, "titulo": p.name.replace("_", " ")[:120],
            "arquivos": [{"nome": f"{i}{x.suffix}" if tipo == "carrossel" else "reel.mp4",
                          "b64": base64.b64encode(x.read_bytes()).decode()} for i, x in enumerate(arqs, 1)]})
        (p / "enviado_painel.json").write_text(json.dumps({"id": iid, "em": datetime.now().isoformat(timespec="seconds"),
                                                           "status": r.get("status")}), "utf-8")
        log(f"enviado pra aprovação: {p.name} ({tipo}, {len(arqs)} arquivo(s))")
        n += 1
    return n


def postar_aprovados():
    itens = _api(f"/api/aprovacao?cliente={CLIENTE}").get("itens", [])
    for it in itens:
        p = FILA / it.get("id", "")
        if not p.is_dir():
            continue
        if it.get("status") == "recusado" and not (p / "recusado.json").exists():
            (p / "recusado.json").write_text(json.dumps({"obs": it.get("obs"), "em": it.get("decidido")}), "utf-8")
            log(f"RECUSADO pelo cliente: {p.name} {it.get('obs') or ''}")
        if it.get("status") != "aprovado" or (p / "postado.json").exists():
            continue
        if os.environ.get("ACAI_POSTAR_APROVADOS", "1") == "0":
            log(f"aprovado (postagem automática desligada): {p.name}")
            continue
        try:
            import acai_postar_fila
            link = acai_postar_fila.postar(p)
            _api("/api/aprovacao/postado", {"cliente": CLIENTE, "id": it["id"], "link": link})
            log(f"APROVADO e POSTADO: {p.name} -> {link}")
        except Exception as e:  # noqa: BLE001
            log(f"[!] aprovado mas a postagem falhou ({p.name}): {type(e).__name__}: {str(e)[:200]}")
        break  # 1 post por passada (Instagram: ritmo humano)


def main():
    if os.environ.get("ACAI_APROVACAO") == "0":
        return
    sys.path.insert(0, r"D:\ms-energy\bin")
    try:
        postar_aprovados()
    except Exception as e:  # noqa: BLE001
        log(f"[!] leitura das aprovações falhou: {type(e).__name__}: {e}")
    try:
        enviar(int(os.environ.get("ACAI_ENVIAR_MAX", "4")))
    except Exception as e:  # noqa: BLE001
        log(f"[!] envio pra aprovação falhou: {type(e).__name__}: {e}")


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
