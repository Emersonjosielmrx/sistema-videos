"""21/11 dona ("acompanhe a geração dos 4 longos de teste dos 2 novos motores e já poste como públicos assim que acabar
de gerar; deixe pra postar sozinho mesmo que seus tokens acabem"). Tarefa do Windows PostarXttsTeste (a cada 10 min,
oculta): quando a ficha de cada um chega (na_nuvem/<vid>_*/nuvem.json), chama postar_longos.py --so <vid> com o filtro
"só Fish" DESLIGADO só nesta chamada (o XTTS é o motor novo; o filtro só conhece o Fish). Público já é o padrão.
Quando os 4 estiverem em longos_postados.json, a própria tarefa se apaga.
    python postar_xtts_teste.py"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
POSTADOS = AQUI / "longos_postados.json"
LOG = AQUI / "postar_xtts_teste.log"
PY = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
ALVOS = {"8fM6Ay7OJho": "só KkVirjão", "gJve_WjefZs": "só Mike", "e2nIzNGXvmA": "só Momo",
         "kxohroSbgS8": "Momo+Mike+KkVirjão",
         "82ge1YYkUyA": "só Momo, PREMIUM Qwen3-TTS (21/11)"}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {msg}\n")


def postados():
    try:
        d = json.loads(POSTADOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    L = d.get("postados") if isinstance(d, dict) else d
    out = {}
    for x in L or []:  # só os postados DEPOIS de liberar o teste (a mesma fonte já saiu antes no motor antigo)
        if isinstance(x, dict) and x.get("vid") and x.get("url") and str(x.get("em") or "") >= "2026-11-21T02":
            out[x["vid"]] = x["url"]
    return out


def main():
    ja = postados()
    faltam = [v for v in ALVOS if v not in ja]
    if not faltam:
        log("os 4 já postados — apago a tarefa")
        subprocess.run(["schtasks", "/delete", "/tn", "PostarXttsTeste", "/f"], capture_output=True)
        return
    for vid in faltam:
        # ficha NOVA (chegou depois de liberar o teste) — a velha do motor antigo pode ter o mesmo vid no nome
        fichas = [f for f in FICHAS.glob(f"{vid}_*/nuvem.json")
                  if datetime.fromtimestamp(f.stat().st_mtime) >= datetime(2026, 11, 21, 2, 0)]
        if not fichas:
            continue
        log(f"{vid} ({ALVOS[vid]}) pronto — postando público")
        env = dict(os.environ, LONGO_SO_FISH_POSTAR="0", PYTHONIOENCODING="utf-8")
        try:
            r = subprocess.run([PY, "-X", "utf8", str(AQUI / "postar_longos.py"), "--so", vid], env=env,
                               capture_output=True, text=True, timeout=3 * 3600, cwd=str(AQUI),
                               creationflags=0x08000000)
            log(f"{vid}: saiu {r.returncode} | {(r.stdout or '')[-300:].strip()}")
        except subprocess.TimeoutExpired:
            log(f"{vid}: passou de 3 h — tento na próxima")
        url = postados().get(vid)
        if url:
            log(f"{vid} ({ALVOS[vid]}) NO AR: {url}")
            try:
                sys.path.insert(0, r"D:\video-fila")
                import avisos
                avisos.enviar(f"🎙️ Longo de teste XTTS ({ALVOS[vid]}) no ar, público: {url}", "longos")
            except Exception:  # noqa: BLE001
                pass
        break  # 1 por volta (o envio leva ~1 h; o próximo vai na volta seguinte)


if __name__ == "__main__":
    main()
