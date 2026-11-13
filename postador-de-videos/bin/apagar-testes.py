#!/usr/bin/env python3
"""apagar-testes.py — Apaga os vídeos privados criados por testar-canais.py.

Lê _LEIA_POSTAR_VIDEOS/teste_canais_resultado.json, pega cada vídeo que POSTOU e
manda DELETE na API (só apaga os do teste 'TESTE CANAL - APAGAR', que são privados).

Uso:
    python bin/apagar-testes.py            # apaga de verdade
    python bin/apagar-testes.py --dry-run  # só lista o que apagaria
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))
import youtube_poster as yp  # noqa: E402

RESULT_FILES = [
    PROJECT / "_LEIA_POSTAR_VIDEOS" / "teste_canais_resultado.json",
    PROJECT / "_LEIA_POSTAR_VIDEOS" / "testar_limite_resultado.json",
]


def deletar(video_id, canal):
    tok = yp.refresh_access_token(canal)
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}"
    req = urllib.request.Request(url, method="DELETE",
                                 headers={"Authorization": f"Bearer {tok}"})
    urllib.request.urlopen(req, timeout=30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    dados = []
    for rf in RESULT_FILES:
        if rf.exists():
            dados.extend(json.loads(rf.read_text(encoding="utf-8")))
    canais = {c["id"]: c for c in yp._load_canais()}
    alvos = [d for d in dados if d["status"] == "POSTOU" and "youtu.be/" in d["info"]]
    print(f"{len(alvos)} vídeos de teste pra apagar\n")

    ok = 0
    for d in alvos:
        vid = d["info"].split("youtu.be/")[-1].strip()
        canal = canais.get(d["id"])
        if not canal:
            print(f"  ? sem creds p/ {d['nome']}")
            continue
        if args.dry_run:
            print(f"  [dry] apagaria {vid}  ({d['nome']})")
            continue
        try:
            deletar(vid, canal)
            print(f"  ✓ apagado {vid}  ({d['nome']})")
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"  ✗ erro {e.code} em {vid} ({d['nome']})")
        except Exception as e:  # noqa
            print(f"  ✗ erro {e} em {vid}")
    if not args.dry_run:
        print(f"\n✅ {ok}/{len(alvos)} apagados.")


if __name__ == "__main__":
    main()
