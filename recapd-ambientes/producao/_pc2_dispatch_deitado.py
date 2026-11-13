#!/usr/bin/env python3
"""_pc2_dispatch_deitado.py — dispara 1 job de anime DEITADO 1h+ no daemon local.

Roda DENTRO do PC2 (C:/recapd-e-animes) pra a conexao HTTP localhost aguentar
o render de horas (o client remoto cortaria em ~1h). Faz discover 1h+, escolhe
o candidato mais visto ainda nao feito, despacha e loga o resultado com o
dur_ratio (verificacao de duracao do fix 2026-07-27).

Uso no PC2:
    venv\\Scripts\\python.exe _pc2_dispatch_deitado.py
"""
import json, sys, time, urllib.request
from pathlib import Path

PROJECT = Path(r"C:/recapd-e-animes")
sys.path.insert(0, str(PROJECT / "bin"))
LOG = PROJECT / "workspace" / "dispatch_deitado.log"
RESULT = PROJECT / "workspace" / "dispatch_deitado_result.json"
DONE = PROJECT / "workspace" / "dispatch_deitado_done.json"  # ids ja despachados
PORT = 8772

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def _load_done():
    try:
        return set(json.loads(DONE.read_text(encoding="utf-8")))
    except Exception:
        return set()

def _save_done(ids):
    try:
        DONE.write_text(json.dumps(sorted(ids), ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def main():
    import anime_discover
    log("=== dispatch deitado 1h+ ===")

    done = _load_done()
    # 1h a ~1h20 (min_dur=3600, max_dur=4800): valida o fix com render mais curto/barato.
    # Depois de validado, subir max_dur pra 12600 pra pegar os campeões de view maiores.
    cands = anime_discover.discover(min_dur=3600, max_dur=4800, top=15)
    log(f"discover: {len(cands)} candidatos 1h+")
    cand = next((c for c in cands if c["id"] not in done), None)
    if not cand:
        log("Nenhum candidato 1h+ novo. Abortando.")
        return 2

    log(f"ESCOLHIDO: {cand['title'][:70]} | {cand['duration']}s | {cand['views']} views | {cand['id']}")
    done.add(cand["id"])
    _save_done(done)

    payload = {"video_url": cand["url"], "titulo": cand["title"], "modo": "deitado"}
    url = f"http://127.0.0.1:{PORT}/run-anime"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    log(f"POST /run-anime (timeout 6h)... render vai levar horas, aguarde.")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=21600) as r:
            result = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log(f"FALHA no POST: {e}")
        return 1

    dt = time.time() - t0
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = result.get("ok")
    log(f"RESULTADO ({dt/60:.0f}min): ok={ok}")
    if ok:
        log(f"  video={result.get('video_path')}")
        log(f"  n_frases={result.get('n_frases')} final_dur={result.get('final_dur')}s "
            f"orig_dur={result.get('orig_dur')}s dur_ratio={result.get('dur_ratio')} "
            f"dur_ok={result.get('dur_ok')}")
        if not result.get("dur_ok"):
            log("  !!! ATENCAO: dur_ok=False — vídeo saiu curto demais, investigar roteiro.")
    else:
        log(f"  erro={result.get('error')}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
