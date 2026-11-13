# -*- coding: utf-8 -*-
"""lancamento_pt.py — primeiras postagens do canal pt novo (Manhwa Noturno), pedido do dono em 16/10/2026.

Ordem: (1) cap 1 completo em retrato, (2) cap 1 em 16:9, (3) Shorts do cap 1, um de cada vez. Só o cap 1 NOVO
(renderizado em 16/10 com as vozes do elenco novo — nada do que saiu no canal antigo é reaproveitado). Tempo entre
eles = a política do pt em config/fila.json "postagem_pt" (fila._pode_postar: canal parado sai já; depois
intervalo_h e só no pico do Brasil). Cada vídeo só sobe com veredito "ok" da análise do vídeo pronto — o
postar_hipercool confere e recusa sozinho. Não depende da fila nem da tarefa de postagem (que seguem desligadas).

16/10 15h: os Shorts do cap 1 saíram daqui. O dono pediu 2 hoje e 3 amanhã ao longo do dia, e quem faz isso é o
bin/shorts_a_cada_2h.py (tarefa HipercoolShorts2h). Este robô termina depois do 16:9 (a etapa "shorts" só roda se
for chamada à mão: python bin/lancamento_pt.py shorts).

  python bin/lancamento_pt.py      (loop a cada 10 min até acabar; log em logs/lancamento_pt.log)
"""
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fila  # noqa: E402

LOG = fila.PROJECT / "logs" / "lancamento_pt.log"
CHAVE = "<SEGREDO_REMOVIDO>"
LONGO = fila.PROJECT / "workspace" / "videos" / "longo" / "the-inheritor"
DIA_NOVO = "20261016"  # o vídeo do cap 1 tem de ser o renderizado hoje (vozes novas)


def diz(msg, telegram=False):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(linha + "\n")
    if telegram:
        fila.avisar(f"canal novo: {msg}")


def _pode():
    c = fila.cfg()
    return fila._pode_postar({**(c.get("postagem_pt") or {}), "canal": c.get("canal_pt", "")})


def _postar_longo():
    import subprocess
    r = subprocess.run([fila.PY, str(fila.PROJECT / "bin" / "postar_hipercool.py"), "--longo", "the-inheritor",
                        "--aprovado"], cwd=fila.PROJECT, env=fila.ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=6 * 3600)
    resumo = re.findall(r"RESUMO: (.*)", (r.stdout or "") + (r.stderr or ""))
    return resumo[-1] if resumo else ((r.stdout or "") + (r.stderr or ""))[-300:]


def _marcar(chave_estado):
    """Grava no estado o que a fila (postar_pt) usa pra não postar de novo: pt_completo_em / pt_shorts_ok."""
    est = fila.ler_estado()
    est.setdefault(CHAVE, {})[chave_estado] = datetime.now().isoformat(timespec="seconds")
    fila.gravar_estado(est)


def passo(etapa):
    """Tenta a etapa da vez. Devolve a próxima etapa (ou a mesma, se ainda não deu)."""
    e = fila.ler_estado().get(CHAVE, {})
    if DIA_NOVO not in (e.get("video") or "") or e.get("situacao") != "pronto" \
            or (e.get("revisao") or {}).get("status") != "ok":
        diz(f"esperando o cap 1 novo ficar pronto e aprovado (render={e.get('render')}, situacao={e.get('situacao')}, "
            f"análise={(e.get('revisao') or {}).get('status')})")
        return etapa
    if etapa == "longo":
        comp, seg = LONGO / "the-inheritor_caps01-01.mp4", LONGO / "cap01.mp4"
        if not (comp.exists() and seg.exists() and comp.stat().st_mtime >= seg.stat().st_mtime
                and DIA_NOVO in datetime.fromtimestamp(seg.stat().st_mtime).strftime("%Y%m%d")):
            diz("esperando o 16:9 novo do cap 1 (bin/refazer_caps.py --longo 1)")
            return etapa
    pode, motivo = _pode()
    if not pode:
        diz(f"{etapa}: espera — {motivo}")
        return etapa
    video = fila.video_do_estado(e["video"])
    if etapa == "completo":
        resumo, _ = fila._postar(video, ["--no-shorts"])
        ok = re.search(r"completo=(ok|ja)", resumo)
    elif etapa == "longo":
        resumo = _postar_longo()
        ok = re.search(r"longo=(ok|ja)", resumo)
    else:
        resumo, _ = fila._postar(video, ["--no-completo", "--max-novos", "1"])
        ok = re.search(r"part_\d+=(ok|ja)", resumo)
        if ok and "faltam=" not in resumo and not re.search(r"part_\d+=ok", resumo):
            _marcar("pt_shorts_ok")
            diz(f"Shorts do cap 1: todos no ar ({resumo})", telegram=True)
            return "fim"
    if etapa == "completo" and ok:
        _marcar("pt_completo_em")
    diz(f"{etapa}: {resumo}", telegram=bool(ok) or "nao_aprovado" in resumo)
    if "nao_aprovado" in resumo:
        return etapa  # a análise recusou: fica parado aqui (a fila/o dono resolvem o vídeo)
    if not ok:
        return etapa
    return {"completo": "longo", "longo": "fim"}.get(etapa, "shorts")


def main():
    etapa = sys.argv[1] if len(sys.argv) > 1 else "completo"
    diz(f"lançamento do canal novo começando na etapa '{etapa}' (canal {fila.cfg().get('canal_pt')})")
    while etapa != "fim":
        try:
            etapa = passo(etapa)
        except Exception as ex:  # noqa: BLE001
            diz(f"erro na etapa {etapa}: {str(ex)[:300]}")
        if etapa != "fim":
            time.sleep(600)
    diz("lançamento do cap 1 terminado", telegram=True)


if __name__ == "__main__":
    main()
