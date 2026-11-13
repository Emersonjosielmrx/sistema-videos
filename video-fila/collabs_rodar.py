r"""collabs_rodar.py — FAZ as collabs do YouTube (02/11 dona: "até hoje as collabs pra aparecer os 2 canais não saíram").

O collabs.py (29/10) só escolhia o parceiro; ninguém mandava o convite. Esta rotina (tarefa CollabsYouTube, de hora em
hora, oculta) lê o registro de uploads de TODOS os projetos (postador-de-videos\logs\uploads_ledger.jsonl), e para
cada vídeo das últimas 48 h de canal pt que está na roda do collabs.py:
  1. dono convida o parceiro da vez (youtube_studio_extras --colaborar @handle);
  2. parceiro aceita pelo link fixo do convite (studio.youtube.com/channel/<parceiro>/collaboration/<dono>)
     (youtube_studio_extras --aceitar-collab LINK).
Testado em 02/11 no 30GDi0l3cx0 (ForjaReact + Game Noturno): a página pública mostra "forjareact e Game Noturno".
No máx. MAX_POR_RODADA vídeos por rodada e só com o Chrome do YouTube livre (não atrasa as postagens).
Estado: estado\collabs_feitos.json. Log: estado\collabs_rodar.log.

    python collabs_rodar.py            # uma rodada
    python collabs_rodar.py --ver      # só mostra o que faria
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import collabs  # noqa: E402

LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
CANAIS = Path(r"D:\postador-de-videos\config\canais.json")
EXTRAS = r"D:\postador-de-videos\bin\youtube_studio_extras.py"
PY = r"D:\manhwa-react\.venv\Scripts\python.exe"
LOCK = Path(r"D:\postador-de-videos\logs\yt_web.lock")
EST = BASE / "estado" / "collabs_feitos.json"
LOG = BASE / "estado" / "collabs_rodar.log"
JANELA_H = 24 * 365  # 02/11 dona: "adicionar em todos que já foram postados antes" — todo o registro; novos e longos primeiro
MAX_POR_RODADA = 6
TENTATIVAS = 3


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M}] {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _extras(cred, *args):
    try:
        r = subprocess.run([PY, "-X", "utf8", EXTRAS, "--canal", cred, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(Path(EXTRAS).parent), timeout=1200,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return {"erro": "sem resposta em 20 min"}
    for linha in reversed((r.stdout or "").splitlines()):
        if linha.startswith("RESULTADO: "):
            return json.loads(linha[11:])
    return {"erro": ((r.stderr or r.stdout or "")[-200:]).strip()}


def pendentes(est):
    canais = (collabs._ler(CANAIS, {}).get("canais") or {})
    por_cred = {cid: slug for slug, c in canais.items() for cid in (c.get("creds") or [])}
    roda = {s for cs in collabs.grupos("youtube").values() if len(cs) > 1 for s in cs}
    limite = datetime.now(timezone.utc) - timedelta(hours=JANELA_H)
    out = []
    for linha in LEDGER.read_text(encoding="utf-8").splitlines()[-3000:]:
        try:
            r = json.loads(linha)
            ts = datetime.fromisoformat(r["ts"])
        except (ValueError, KeyError):
            continue
        slug = por_cred.get(r.get("canal_id"))
        vid = r.get("video_id")
        if not vid or ts < limite or slug not in roda:
            continue
        x = est.get(vid, {})
        if x.get("fim") or x.get("tentativas", 0) >= TENTATIVAS:
            continue
        out.append({"vid": vid, "slug": slug, "cred": r["canal_id"], "tipo": r.get("tipo"), "ts": r["ts"]})
    # longo primeiro (rende mais por collab), depois os mais novos (o empurrão vale mais no começo); sem repetir vídeo
    vistos, uniq = set(), []
    for p in sorted(sorted(out, key=lambda p: p["ts"], reverse=True), key=lambda p: p["tipo"] != "completo"):
        if p["vid"] not in vistos:
            vistos.add(p["vid"])
            uniq.append(p)
    return uniq, canais


def rodada(ver=False):
    est = collabs._ler(EST, {})
    lista, canais = pendentes(est)
    if not lista:
        return
    if not ver:  # espera o Chrome do YouTube soltar (postagem tem prioridade) até 15 min
        import time
        fim = time.time() + 900
        while LOCK.exists() and time.time() < fim:
            time.sleep(30)
        if LOCK.exists():
            log(f"{len(lista)} vídeo(s) esperando collab — Chrome do YouTube ocupado há 15 min, fica pra próxima")
            return
    for p in lista[:MAX_POR_RODADA]:
        x = est.setdefault(p["vid"], {"canal": p["slug"]})
        sem_login = est.setdefault("_sem_login", {})
        parc = x.get("parceiro")
        for _ in range(6):  # parceiro com o Chrome deslogado não aceita: pula pro próximo da roda
            if parc:
                break
            cand = collabs.parceiro("youtube", p["slug"], registrar=False)
            if cand and not ver and cand in sem_login and \
                    datetime.now() - datetime.fromisoformat(sem_login[cand]) < timedelta(hours=24):  # 24 h depois tenta
                collabs.parceiro("youtube", p["slug"])  # gasta a vez dele
                continue
            parc = cand
        if not parc:
            x["fim"] = "sem parceiro"
            continue
        dono, c_parc = canais.get(p["slug"], {}), canais.get(parc, {})
        handle, uc_parc, uc_dono = c_parc.get("handle"), c_parc.get("channel_id"), dono.get("channel_id")
        cred_parc = (c_parc.get("creds") or [None])[0]
        if not (handle and uc_parc and uc_dono and cred_parc):
            x["fim"] = f"faltam dados do canal ({parc})"
            continue
        if ver:
            log(f"faria: {p['vid']} ({p['slug']}, {p['tipo']}) + {parc} {handle}")
            continue
        x["parceiro"] = parc
        if x.get("convite") not in ("ok", "ja"):
            r = _extras(p["cred"], f"--video={p['vid']}", f"--colaborar={handle}")
            x["convite"] = r.get("colaborar") or r.get("erro") or "?"
            log(f"{p['vid']} {p['slug']} convidou {parc}: {x['convite']}")
            if x["convite"] not in ("ok", "ja"):
                x["tentativas"] = x.get("tentativas", 0) + 1
                collabs.EST.parent.mkdir(parents=True, exist_ok=True)
                EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
                continue
            collabs.parceiro("youtube", p["slug"])  # anda a roda só quando o convite saiu
        link = f"https://studio.youtube.com/channel/{uc_parc}/collaboration/{uc_dono}"
        r = _extras(cred_parc, f"--aceitar-collab={link}")
        x["aceite"] = r.get("aceitar_collab") or r.get("erro") or "?"
        log(f"{p['vid']} {parc} aceitou: {x['aceite']}")
        if str(x["aceite"]).startswith("ok") or x["aceite"] == "ja":
            x["fim"] = datetime.now().isoformat(timespec="minutes")
            est.get("_sem_login", {}).pop(parc, None)
        elif str(x["aceite"]).startswith("morto"):
            # Chrome do parceiro deslogado: o convite fica pendente (invisível pro público); ele sai da roda até logar
            est.setdefault("_sem_login", {})[parc] = datetime.now().isoformat(timespec="minutes")
            x["fim"] = f"parceiro {parc} sem login"
            log(f"  {parc}: Chrome deslogado — fora das collabs até logar de novo")
        else:
            x["tentativas"] = x.get("tentativas", 0) + 1
        EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
    if len(lista) > MAX_POR_RODADA and not ver:
        log(f"{len(lista) - MAX_POR_RODADA} vídeo(s) ficam pra próxima rodada")


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import msvcrt
    trava = open(BASE / "estado" / "collabs_rodar.lock", "w")
    try:
        msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        sys.exit(0)
    rodada(ver="--ver" in sys.argv)
