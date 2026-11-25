r"""Posta Reel numa Página do Facebook pela Graph API (sem Chrome) — 24/11/2026.

Fluxo oficial: POST /{page}/video_reels upload_phase=start -> POST rupload.facebook.com/video-upload/{v}/{video_id}
(bytes, headers offset/file_size) -> POST /{page}/video_reels upload_phase=finish video_state=PUBLISHED description.
SEMPRE pela saída fixa da conta (fish_audio._subir_ponte; recusa Kaggle; nunca a casa).
Token da Página: secrets\fb_paginas_<conta>.json (bin\fb_token_assistido.py / fb_token_auto.py).

    python fb_reel_api.py teste <chave_da_pagina>     # posta 1 reel (o próximo da fila da Página) e registra
Em código: postar_api(conta, asset_id, video, texto) -> (ok, msg, video_id)
"""
import json
import sys
import time
from pathlib import Path

BIN = Path(__file__).resolve().parent
SEC = BIN.parent / "secrets"
V = "v21.0"
G = f"https://graph.facebook.com/{V}"
RUP = f"https://rupload.facebook.com/video-upload/{V}"
sys.path.insert(0, str(BIN))
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")


def token_pagina(conta, asset_id):
    f = SEC / f"fb_paginas_{conta}.json"
    if not f.exists():
        return None
    return (json.loads(f.read_text(encoding="utf-8")).get("paginas", {}).get(str(asset_id)) or {}).get("token")


def _sessao(conta):
    import fish_audio
    import requests
    cfg = json.loads((BIN.parent / "config" / "facebook_paginas.json").read_text(encoding="utf-8"))["contas"][conta]
    _, n = fish_audio.checar_conta(cfg["email"])
    if f"rnprmtfo-{n}" != cfg["saida"]:
        raise SystemExit(f"{conta}: saída do cofre rnprmtfo-{n} != configurada {cfg['saida']}")
    porta = fish_audio._subir_ponte(n)
    s = requests.Session()
    s.proxies = {"http": f"http://127.0.0.1:{porta}", "https": f"http://127.0.0.1:{porta}"}
    return s


def _erro(r):
    try:
        e = r.json().get("error") or {}
        return f"{e.get('code')}/{e.get('error_subcode')}: {e.get('message')}"
    except Exception:  # noqa: BLE001
        return f"HTTP {r.status_code}: {r.text[:200]}"


DESCANSO = BIN.parent / "logs" / "fb_api_descanso.json"


def descansando(conta):
    """25/11: rupload respondeu 429 (limite de envio) pela saída da mundosolar1995 depois de ~6 Reels seguidos pela API.
    Conta em descanso = não usa a API até a hora gravada (posta pelo Chrome)."""
    try:
        ate = json.loads(DESCANSO.read_text(encoding="utf-8")).get(conta)
    except (OSError, ValueError):
        return None
    from datetime import datetime
    return ate if ate and datetime.fromisoformat(ate) > datetime.now() else None


def _descansar(conta, horas=2):
    from datetime import datetime, timedelta
    try:
        d = json.loads(DESCANSO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    d[conta] = (datetime.now() + timedelta(hours=horas)).isoformat(timespec="seconds")
    DESCANSO.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def _ultimo_post(conta):
    """Hora do último Reel desta conta (qualquer via) no registro."""
    from datetime import datetime
    try:
        cfg = json.loads((BIN.parent / "config" / "facebook_paginas.json").read_text(encoding="utf-8"))["paginas"]
        reg = json.loads((BIN.parent / "logs" / "facebook_paginas.json").read_text(encoding="utf-8"))["postados"]
    except (OSError, ValueError, KeyError):
        return None
    qs = [e.get("quando", "") for k, v in reg.items() if (cfg.get(k) or {}).get("conta") == conta for e in v]
    return datetime.fromisoformat(max(qs)) if qs else None


def postar_api(conta, asset_id, video, texto, esperar_s=300):
    tok = token_pagina(conta, asset_id)
    if not tok:
        return False, "sem token da Página (gerar com fb_token_auto.py)", None
    if descansando(conta):
        return False, f"start: API em descanso até {descansando(conta)}", None
    # 25/11: pela API sai 1 Reel a cada ~2 min (Chrome: 5-11 min) e em ~2 h a emersonjosiel02 levou o 368 (limite de
    # frequência/spam). Mínimo de FB_API_INTERVALO_MIN (15) entre posts da MESMA conta: espera aqui em vez de disparar.
    import os
    mins = float(os.environ.get("FB_API_INTERVALO_MIN", "15"))
    ult = _ultimo_post(conta)
    if ult:
        from datetime import datetime
        falta = mins * 60 - (datetime.now() - ult).total_seconds()
        if falta > 0:
            print(f"   API: esperando {falta / 60:.0f} min (intervalo mínimo da conta)", flush=True)
            time.sleep(falta)
    s = _sessao(conta)
    # rupload com 429 = limite de envio da conta: NÃO insiste (pode virar bloqueio); descansa 2 h e o Chrome segura
    try:
        if s.get(f"{RUP}/", timeout=20).status_code == 429:
            _descansar(conta)
            return False, "start: rupload 429 (limite de envio) — API em descanso 2 h", None
    except Exception:  # noqa: BLE001
        pass
    r = s.post(f"{G}/{asset_id}/video_reels", data={"upload_phase": "start", "access_token": tok}, timeout=60)
    if r.status_code != 200 or "video_id" not in r.text:
        return False, f"start: {_erro(r)}", None
    vid = r.json()["video_id"]
    dados = Path(video).read_bytes()
    mb = len(dados) / 1e6
    r = None
    for tent in range(3):  # 25/11: rupload às vezes derruba a conexão (Max retries) — tenta de novo antes do Chrome
        try:
            r = s.post(f"{RUP}/{vid}", data=dados, timeout=int(120 + 10 * mb),
                       headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(len(dados)),
                                "Content-Type": "application/octet-stream"})
            break
        except Exception:  # noqa: BLE001
            if tent == 2:
                raise
            time.sleep(15)
    if r.status_code != 200 or not r.json().get("success"):
        return False, f"upload ({mb:.0f} MB): {_erro(r)}", vid
    r = s.post(f"{G}/{asset_id}/video_reels", timeout=60,
               data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED", "description": texto,
                     "access_token": tok})
    if r.status_code != 200 or not r.json().get("success"):
        return False, f"finish: {_erro(r)}", vid
    # status até publicar (o FB processa o vídeo)
    fim = time.time() + esperar_s
    ultimo = ""
    while time.time() < fim:
        st = s.get(f"{G}/{vid}", params={"fields": "status", "access_token": tok}, timeout=30).json().get("status", {})
        ultimo = json.dumps(st, ensure_ascii=False)[:300]
        pub = (st.get("publishing_phase") or {}).get("status")
        proc = (st.get("processing_phase") or {}).get("status")
        if st.get("video_status") == "error" or proc == "error" or pub == "error":
            return False, f"o FB recusou no processamento: {ultimo}", vid
        if pub == "complete" or st.get("video_status") == "ready" and pub in (None, "complete"):
            return True, f"ok api ({mb:.0f} MB)", vid
        time.sleep(10)
    return True, f"enviado, ainda processando (video_id {vid}): {ultimo}", vid


def teste(chave):
    """Posta o próximo vídeo da fila da Página pela API e registra como um post normal."""
    import catalogo
    import postar_facebook_paginas as pfp
    from datetime import datetime
    cfg = json.loads(pfp.CFG.read_text(encoding="utf-8"))
    pag = cfg["paginas"][chave]
    reg = pfp._ler(pfp.REG, {})
    cat = pfp.carregar_catalogo()
    for v in pfp.candidatos(chave, pag, cat, reg)[:8]:
        legenda = catalogo.legenda_reuso(v)
        if not legenda:
            continue
        try:
            mp4 = catalogo.baixar(v)
        except Exception as e:  # noqa: BLE001
            print("não baixou:", str(e)[:120]); continue
        d = pfp.duracao(mp4)
        if d is None or d > pfp.DUR_MAX:
            catalogo.liberar(mp4); continue
        t0 = time.time()
        ok, msg, vid = postar_api(pag["conta"], pag["asset_id"], str(mp4), legenda)
        catalogo.liberar(mp4)
        print(f"[{pag['nome']}] {'OK' if ok else 'ERRO'} em {time.time() - t0:.0f} s — {msg} — {v['caminho'][-60:]}")
        reg = pfp._ler(pfp.REG, {})
        if ok:
            reg.setdefault("postados", {}).setdefault(chave, []).append(
                {"caminho": v["caminho"], "quando": datetime.now().isoformat(timespec="seconds"), "legenda": legenda[:200],
                 "duracao": round(d, 1), "via": "api", "video_id": vid})
        else:
            reg.setdefault("erros", {}).setdefault(chave, {})[datetime.now().isoformat(timespec="seconds")] = f"api: {msg}"[:300]
        pfp._gravar(reg)
        return ok
    print(f"[{pag['nome']}] nenhum vídeo postável")
    return False


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) == 3 and sys.argv[1] == "teste":
        teste(sys.argv[2])
    else:
        print(__doc__)
