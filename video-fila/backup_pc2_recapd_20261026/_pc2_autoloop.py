#!/usr/bin/env python3
"""_pc2_autoloop.py — loop de produção AUTÔNOMO de anime deitado no PC2.

Roda DENTRO do PC2, independente de qualquer sessão externa. Sobe no boot via
tarefa agendada (gatilho de logon). Resiliente a reinício dos 2 PCs:
  - Render roda no daemon local (porta 8772); este loop só orquestra.
  - Cada vídeo OK é ARQUIVADO em C:\\recapd-e-animes\\saida\\<id>_<data>\\ (pasta
    ESTÁVEL, fora do %TEMP% que pode ser limpo). Nada se perde no restart.
  - Guard de instância única (lockfile) evita 2 autoloops.
  - done.json (via python, sem BOM) evita repetir vídeo.

O fetch pra D:\\hipercool-materiais (outro PC) é SEPARADO: pode ser feito quando
aquele PC estiver de pé, lendo de saida\\. Assim o autoloop nunca depende do host.
"""
import json, os, sys, time, glob, shutil, urllib.request, urllib.error
from pathlib import Path

PROJECT = Path(r"C:/recapd-e-animes")
sys.path.insert(0, str(PROJECT / "bin"))
WS = PROJECT / "workspace"
LOG = WS / "autoloop.log"
DONE = WS / "dispatch_deitado_done.json"
SAIDA = PROJECT / "saida"                      # pasta estável de vídeos prontos
INSTANCE_LOCK = WS / "autoloop.instance.lock"  # 1 autoloop por vez
PORT = 8772
MIN_DUR, MAX_DUR = 3600, 12600                 # 1h a 3h30

def log(m):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), m)
    print(line, flush=True)
    try:
        WS.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def _instance_guard():
    """True se este é o único autoloop. Lock obsoleto (>7h) é ignorado."""
    try:
        if INSTANCE_LOCK.exists():
            age = time.time() - INSTANCE_LOCK.stat().st_mtime
            if age < 7 * 3600:
                return False
        INSTANCE_LOCK.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except Exception:
        return True

def _touch_instance():
    try:
        INSTANCE_LOCK.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

def _load_done():
    try:
        return set(json.load(open(DONE, encoding="utf-8")))
    except Exception:
        return set()

def _save_done(ids):
    try:
        json.dump(sorted(ids), open(DONE, "w", encoding="utf-8"))  # sem BOM
    except Exception as e:
        log("erro salvar done: %s" % e)

def _daemon_ok():
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % PORT, timeout=5) as r:
            return json.loads(r.read()).get("ok") is True
    except Exception:
        return False

def _archive(video_path, vid, meta=None):
    """Copia o final pra pasta estável saida\\<id>_<data>\\. Retorna o destino.
    meta (dict opcional): contexto salvo em source.json p/ o publisher do host."""
    try:
        dest_dir = SAIDA / ("%s_%s" % (vid, time.strftime("%Y%m%d")))
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "final_anime_deitado.mp4"
        shutil.copy2(video_path, dest)
        # Salva contexto p/ o publisher do host saber o que é (anime/URL/etc).
        if meta:
            try:
                json.dump(meta, open(dest_dir / "source.json", "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass
        log("arquivado: %s (%.0f MB)" % (dest, dest.stat().st_size / 1e6))
        return str(dest)
    except Exception as e:
        log("FALHA ao arquivar %s: %s" % (video_path, e))
        return None

def _archive_orphans():
    """Varre %TEMP%\\anime_worker_* por final_anime_deitado.mp4 ainda NÃO arquivado
    em saida\\ e copia. Pega vídeos prontos que qualquer caminho (task antiga, job
    interrompido) deixou no temp — resiliência a restart. Marca no done pelo work_dir."""
    try:
        temp = os.path.expandvars(r"C:/Users/Emerson-IA/AppData/Local/Temp")
        for wd in glob.glob(os.path.join(temp, "anime_worker_*")):
            fin = os.path.join(wd, "final_anime_deitado.mp4")
            if not os.path.exists(fin):
                continue
            # já arquivado? marca por um .archived no próprio workdir
            flag = os.path.join(wd, ".archived")
            if os.path.exists(flag):
                continue
            tag = "orphan_" + os.path.basename(wd).replace("anime_worker_", "")
            dest = _archive(fin, tag)
            if dest:
                try:
                    open(flag, "w").close()  # não re-arquivar
                    log("orfao arquivado de %s" % os.path.basename(wd))
                except Exception:
                    pass
    except Exception as e:
        log("erro varrer orfaos: %s" % e)

def run_once():
    import anime_discover
    done = _load_done()
    # 26/10: top=15 cortava antes de tirar os feitos — com 735 feitos nunca sobrava candidato
    cands = anime_discover.discover(min_dur=MIN_DUR, max_dur=MAX_DUR, top=100)
    cand = next((c for c in cands if c["id"] not in done), None)
    if not cand:
        log("sem candidato novo (todos %d feitos). aguardando." % len(done))
        return "no_candidate"

    vid = cand["id"]
    log("ESCOLHIDO %s | %ds | %s views | %s" %
        (vid, cand["duration"], cand["views"], cand["title"][:50]))

    payload = {"video_url": cand["url"], "titulo": cand["title"], "modo": "deitado"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:%d/run-anime" % PORT, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    log("POST /run-anime (render vai levar horas)...")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=21600) as r:
            result = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as he:
        if he.code == 409:
            log("daemon ocupado (409, outro render ativo). aguardando.")
            return "busy"
        log("FALHA no POST (%.0fmin): HTTP %s" % ((time.time()-t0)/60, he.code))
        return "post_failed"
    except Exception as e:
        log("FALHA no POST (%.0fmin): %s" % ((time.time()-t0)/60, e))
        return "post_failed"

    dt = (time.time() - t0) / 60
    if result.get("error") == "busy_rendering" or result.get("error") == "busy_rendering_disk":
        log("daemon ocupado (outro render). aguardando.")
        return "busy"

    ok = result.get("ok")
    ratio = result.get("dur_ratio")
    log("RESULTADO (%.0fmin): ok=%s dur_ok=%s dur_ratio=%s n_frases=%s" %
        (dt, ok, result.get("dur_ok"), ratio, result.get("n_frases")))

    # Marca como feito (mesmo se dur_ok False, pra não repetir infinitamente um source ruim)
    done.add(vid)
    _save_done(done)

    if ok and result.get("video_path"):
        meta = {"id": vid, "titulo": cand["title"], "url": cand["url"],
                "duration_s": cand.get("duration"), "views": cand.get("views"),
                "dur_ratio": ratio, "final_dur": result.get("final_dur"),
                "n_frases": result.get("n_frases"), "dur_ok": result.get("dur_ok")}
        _archive(result["video_path"], vid, meta=meta)
        if not result.get("dur_ok"):
            log("ATENCAO dur_ok=False (ratio %s) — arquivado mas revisar." % ratio)
    else:
        log("job falhou (erro=%s) — marcado feito p/ nao repetir." % result.get("error"))
    return "done"

def main():
    log("=== AUTOLOOP iniciado (pid %d) ===" % os.getpid())
    if not _instance_guard():
        log("outro autoloop ativo (instance lock recente). saindo.")
        return
    SAIDA.mkdir(parents=True, exist_ok=True)
    while True:
        _touch_instance()
        try:
            _archive_orphans()  # resgata vídeos prontos deixados no temp (restart-safe)
            if not _daemon_ok():
                log("daemon /health nao ok — aguardando 60s (watchdog sobe).")
                time.sleep(60)
                continue
            r = run_once()
            if r == "no_candidate":
                time.sleep(1800)     # 30min: nada novo pra fazer
            elif r in ("busy", "post_failed"):
                time.sleep(120)
            else:
                time.sleep(20)       # cooldown curto entre vídeos
        except Exception as e:
            log("loop erro: %s — aguardando 120s" % e)
            time.sleep(120)

if __name__ == "__main__":
    main()
