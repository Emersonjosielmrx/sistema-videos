# -*- coding: utf-8 -*-
"""refazer_capa.py — refaz a capa (.capa.jpg) de um capítulo JÁ renderizado com o código de capa atual.

  python bin/refazer_capa.py the-inheritor-cap02          # chave da fila (config/fila.json / fila_estado.json)

Refaz a do vídeo normal e a do censurado (esta só com painéis que não foram censurados). Usa só cache
(narração, Sightengine, recortes, rostos) — nenhuma IA nova. Útil quando a regra da capa muda depois do
render e antes de postar.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fila  # noqa: E402
import fx_acabamento  # noqa: E402
import hp_paineis  # noqa: E402
from hp_common import log  # noqa: E402


def refazer(chave):
    est = fila.ler_estado()
    e = est.get(chave) or {}
    cap = next(((o, n, p) for k, o, n, p in fila.capitulos() if k == chave), None)
    if not cap or not e.get("video"):
        log(f"[X] {chave}: capítulo sem vídeo renderizado no estado da fila")
        return False
    obra, n, pasta = cap
    sk = e.get("skip", {})
    ps, _c = hp_paineis.selecionar_paineis(pasta, 120, 1, int(sk.get("fim", 0)), int(sk.get("inicio", 0)), verbose=False)
    narr = hp_paineis.arquivo_narracao(pasta, len(ps), 1, int(sk.get("fim", 0)), int(sk.get("inicio", 0)))
    rec = json.loads(narr.read_text(encoding="utf-8"))
    info = {str(p): {"desc": d, "fala": l.get("text", ""), "persona": l.get("persona"), "genero": l.get("gender")}
            for p, d, l in zip(ps, rec.get("descriptions", []), rec.get("locucoes", []))}
    gancho = (rec.get("_editorial") or {}).get("gancho") or rec.get("titulo_video") or obra["titulo"]
    normal = fila.video_do_estado(e["video"])
    fx_acabamento.gerar_capa(ps, gancho, n, normal.with_suffix(".capa.jpg"), info=info)
    cens = normal.with_name(normal.name.replace("_ULTIMO.mp4", "_CENSURADO_ULTIMO.mp4"))
    if normal.parent.name == "normal":  # workspace/videos/<obra>/capNN/<idioma>/normal|censurado
        cens = normal.parent.parent / "censurado" / cens.name
    if cens.exists():
        meta_c = json.loads(cens.with_suffix(".meta.json").read_text(encoding="utf-8"))
        sujos = {c["painel"] for c in (meta_c.get("censura") or {}).get("paineis", [])}
        limpos = [p for p in ps if p.name not in sujos]
        fx_acabamento.gerar_capa(limpos or ps, gancho, n, cens.with_suffix(".capa.jpg"), info=info)
    return True


if __name__ == "__main__":
    for ch in sys.argv[1:]:
        refazer(ch)
