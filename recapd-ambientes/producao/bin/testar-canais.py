#!/usr/bin/env python3
"""testar-canais.py — TESTE: quais canais conseguem POSTAR de fato (upload real privado).

Sobe um vídeo pequeno como PRIVADO em cada canal (menos os 2 manhwa já usados hoje)
e registra o resultado. Vídeos ficam privados (só o dono vê) e são fáceis de achar
pelo título 'TESTE CANAL - APAGAR'. Lista os IDs no fim pra você apagar depois.

⚠️ 33 canais compartilham 1 projeto de API (cota 10k/dia = ~6 uploads). Depois disso
os outros falham com quotaExceeded — isso NÃO quer dizer que o canal não posta, só que
o PROJETO ficou sem cota hoje. Categorias no resultado deixam isso claro.

Uso: python bin/testar-canais.py
"""
import json
import sys
import time
import urllib.error
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import youtube_poster as yp  # noqa: E402

SKIP = {"zsEhAgkXUSofZr5Y", "hNQrW5ouNe0Ni5Me"}  # inovare recap manga / nova conta (maxados hoje)
TEST_VIDEO = r"D:/hipercool-producao/workspace/shorts/the-meek-cat-cap3/the-meek-cat_cap3_parte07.mp4"


def reason_of(e):
    if isinstance(e, urllib.error.HTTPError):
        try:
            body = e.read().decode("utf-8", "replace")
            j = json.loads(body)
            return f"{e.code}:{j['error']['errors'][0]['reason']}"
        except Exception:
            return f"HTTP {e.code}"
    return str(e)[:70]


def main():
    canais = yp._load_canais()
    res = []
    for c in canais:
        nome = c["nome"].strip()
        cid = c["id"]
        if cid in SKIP:
            res.append((nome, cid, "PULADO", "manhwa já usado hoje"))
            continue
        # 1. token vivo?
        try:
            yp.refresh_access_token(c)
        except Exception as e:  # noqa
            r = reason_of(e)
            res.append((nome, cid, "TOKEN_MORTO", r))
            print(f"TOKEN_MORTO  {nome[:32]:32} {r}", flush=True)
            continue
        # 2. consegue subir?
        try:
            vid = yp.upload(TEST_VIDEO, "TESTE CANAL - APAGAR",
                            "teste automatizado de upload", ["teste"], c,
                            privacy="private")
            res.append((nome, cid, "POSTOU", f"https://youtu.be/{vid}"))
            print(f"POSTOU ✓     {nome[:32]:32} https://youtu.be/{vid}", flush=True)
        except Exception as e:  # noqa
            r = reason_of(e)
            res.append((nome, cid, "FALHOU", r))
            print(f"FALHOU ✗     {nome[:32]:32} {r}", flush=True)
        time.sleep(0.4)

    out = (Path(__file__).resolve().parent.parent /
           "_LEIA_POSTAR_VIDEOS" / "teste_canais_resultado.json")
    out.write_text(json.dumps(
        [{"nome": n, "id": i, "status": s, "info": inf} for n, i, s, inf in res],
        ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n==================== RESUMO ====================")
    for k, v in Counter(s for _, _, s, _ in res).items():
        print(f"  {k}: {v}")
    print("\n==================== POSTARAM (podem postar) ====================")
    for n, i, s, inf in res:
        if s == "POSTOU":
            print(f"  {n[:36]:36} {inf}")
    print("\n==================== FALHARAM ====================")
    for n, i, s, inf in res:
        if s in ("FALHOU", "TOKEN_MORTO"):
            print(f"  [{s}] {n[:32]:32} {inf}")
    print(f"\nResultado salvo em: {out}")


if __name__ == "__main__":
    main()
