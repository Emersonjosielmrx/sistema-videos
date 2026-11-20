r"""garimpar_milhoes.py — pesquisa PROFUNDA de recaps longos com MILHÕES de views que ainda não fizemos (dona 19/11:
"faça uma pesquisa profunda pra ver os vídeos que deixamos passar ou vídeos novos que tenham muitas visualizações e não
estão na nossa fila; o de hoje tinha pouco mais de 200 mil, e eu já vi vídeos de milhões que ainda não fizemos").

Diferente do garimpar_fontes (8 buscas por relevância, corte 300 mil): aqui
  1. a aba "mais vistos" dos CANAIS-FONTE grandes (os que já deram fonte na lista + os do VIP abaixo);
  2. ~20 buscas com 100 resultados cada;
  3. fica só >= MIN_VIEWS (1 mi), 35-170 min, "recap"/"resumo"/"explained" no título, sem adulto;
  4. tira o que já foi feito/está na fila/postado/ignorado (mesmo _ja_conhecidos do garimpar_fontes);
  5. tira o que tem LEGENDA QUEIMADA (fonte_sem_legenda.nota >= 2 nas miniaturas) — dona: "de preferência sem tarja";
  6. entra na lista de prioridade LOGO DEPOIS das séries forcar_longo, por views.
1 chamada yt-dlp por vez, 25 s de pausa (regra: sem rajada); respeita ytdlp_vez (pausa/proxy). Pode levar ~30 min.

    python garimpar_milhoes.py          # garimpa e grava
    python garimpar_milhoes.py --ver    # só mostra
"""
import json
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import garimpar_fontes as gf  # noqa: E402
import fonte_sem_legenda as fsl  # noqa: E402

MIN_VIEWS = 1_000_000
PAUSA = 25
BUSCAS = [
    "manhwa recap", "manhwa recap full", "manhua recap", "webtoon recap", "anime recap", "anime recap full",
    "manhwa recap system", "manhwa recap reincarnated", "manhwa recap regressor", "manhwa recap revenge",
    "manhwa recap cheating girlfriend", "manhwa recap billionaire", "manhwa recap level up", "manhwa recap villain",
    "manhwa recap tower", "manhwa recap hunter", "manhwa recap murim", "anime recap isekai",
    "anime recap overpowered", "manga recap",
]
CANAIS_VIP = ["@JinwooRecap", "@AniRoll", "@MamoruManhwa", "@YogiriRecap", "@Manhwa_Fresh", "@Recapkun",
              "@AniClimax", "@TobsManhwa", "@PopiRecaps", "@AniLast", "@ANiSagaX", "@HarutoXplainer"]


def _ytdlp(alvo, n):
    import ytdlp_vez
    if ytdlp_vez.pausado():
        return None
    cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "-J", "--playlist-end", str(n), alvo]
    px = ytdlp_vez.proxy_url()
    if px:
        cmd[3:3] = ["--proxy", px]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return json.loads(r.stdout or "{}").get("entries") or []
    except Exception as e:  # noqa: BLE001
        print(f"  {alvo[:60]} falhou ({type(e).__name__})", flush=True)
        return []


def _ok(e):
    if not isinstance(e, dict):
        return None
    vid, t = e.get("id"), e.get("title") or ""
    dur, views = (e.get("duration") or 0) / 60, e.get("view_count") or 0
    if not vid or len(vid) != 11 or gf.ADULTO.search(t):
        return None
    if not (gf.MIN_MIN <= dur <= gf.MAX_MIN) or views < MIN_VIEWS:
        return None
    tl = t.lower()
    if not any(x in tl for x in ("recap", "resumo", "explained")):
        return None
    return {"id": vid, "tipo": "manhwa" if any(x in tl for x in ("manhwa", "manhua", "webtoon", "manga")) else "anime",
            "canal": e.get("channel") or e.get("uploader") or "", "views": views, "min": round(dur), "titulo": t[:110],
            "garimpado": time.strftime("%Y-%m-%d"), "milhoes": True}


def canais_da_lista():
    d = json.loads(gf.CFG.read_text(encoding="utf-8"))
    out = []
    for v in d.get("videos", []):
        c = (v.get("canal") or "").strip()
        if c.startswith("@") and c not in out:
            out.append(c)
    return out


def main(ver):
    sys.path.insert(0, r"D:\hipercool-materiais\comum")
    conhecidos = gf._ja_conhecidos()
    achados = {}
    canais = list(dict.fromkeys(CANAIS_VIP + canais_da_lista()))
    print(f"{len(canais)} canais + {len(BUSCAS)} buscas (pausa {PAUSA} s entre cada)", flush=True)
    for c in canais:
        ents = _ytdlp(f"https://www.youtube.com/{c}/videos?view=0&sort=p", 60)
        if ents is None:
            print("yt-dlp pausado — paro aqui", flush=True)
            break
        ok = [x for x in (_ok(e) for e in ents) if x]
        for x in ok:
            achados[x["id"]] = x
        print(f"  canal {c}: {len(ents)} vídeos, {len(ok)} >= 1 mi", flush=True)
        time.sleep(PAUSA)
    for q in BUSCAS:
        ents = _ytdlp(f"ytsearch100:{q}", 100)
        if ents is None:
            print("yt-dlp pausado — paro aqui", flush=True)
            break
        ok = [x for x in (_ok(e) for e in ents) if x]
        for x in ok:
            achados[x["id"]] = x
        print(f"  busca '{q}': {len(ents)} resultados, {len(ok)} >= 1 mi", flush=True)
        time.sleep(PAUSA)
    novos = [v for v in achados.values() if v["id"] not in conhecidos]
    sem_leg = []
    for v in sorted(novos, key=lambda v: -v["views"]):
        n = fsl.nota(v["id"])
        v["legenda_nota"] = n
        if n is not None and n <= 1:
            sem_leg.append(v)
        print(f"  {v['views']:>11,} {v['min']:>4} min leg={n} {v['canal'][:18]:18} {v['titulo'][:55]}", flush=True)
    print(f"\n{len(achados)} achados >= 1 mi | {len(novos)} ainda não feitos | {len(sem_leg)} sem legenda queimada",
          flush=True)
    if ver or not sem_leg:
        return
    d = json.loads(gf.CFG.read_text(encoding="utf-8"))
    vids = d.get("videos", [])
    i = sum(1 for v in vids if v.get("forcar_longo"))  # depois das séries da dona
    vids[i:i] = sem_leg
    d["videos"] = vids
    d["ja_garimpados"] = sorted(set(d.get("ja_garimpados", [])) | {v["id"] for v in sem_leg})
    gf.CFG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(sem_leg)} entraram na frente da lista (depois das séries)", flush=True)


if __name__ == "__main__":
    main("--ver" in sys.argv)
