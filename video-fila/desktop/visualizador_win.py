"""Visualizador do DESKTOP (Windows): abre no Chrome, um por vez, cada vídeo LONGO que acabou de ir ao ar no YouTube.

01/11 dona: "a visualização dos longos nos notebooks não pode ter vídeos longos, apenas curtos; os longos devem ser
no desktop". O PC1 (D:\\video-fila\\visualizador.py enviar) manda os curtos pro x200ma e os longos (tipo "completo")
pra cá em D:\\visualizador\\fila.json. Mesma lógica do x200ma\\visualizador.py: só abre com a tela desbloqueada, nunca o
mesmo vídeo 2x, like/comentário ficam com quem assiste. Arquivo PAUSADO nesta pasta = não abre nada novo.
Roda pela tarefa VisualizadorLongos (a cada minuto, só com o usuário logado): pythonw visualizador_win.py --uma
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(r"D:\visualizador")
FILA = BASE / "fila.json"
VISTOS = BASE / "vistos.json"
ESTADO = BASE / "estado.json"
LOG = BASE / "visualizador.log"
PAUSADO = BASE / "PAUSADO"
PERFIL = BASE / "chrome-perfil"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

MIN_S = 600        # longo: fica aberto pelo menos 10 min antes de passar pro próximo
JANELA_H = 12      # publicado há mais que isto: já passou, não abre
ESPERA_401_MIN = 10
DESISTE_MIN = 120
CHECAGENS_POR_RODADA = 3
VISTOS_DIAS = 7


def log(msg):
    try:
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            LOG.replace(LOG.with_suffix(".log.1"))
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
    except OSError:
        pass


def ler(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def gravar(p, dados):
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def dt(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def tela_bloqueada():
    """Windows: com a tela bloqueada o LogonUI.exe fica rodando."""
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq LogonUI.exe", "/NH"], capture_output=True, text=True,
                           timeout=15, creationflags=SEM_JANELA)
        return "LogonUI.exe" in r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False


def no_ar(vid):
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
            return "sim", json.loads(r.read().decode("utf-8", "replace")).get("title", "")
    except urllib.error.HTTPError as e:
        return ("401" if e.code in (401, 403) else "nao"), ""
    except (urllib.error.URLError, OSError, ValueError):
        return "rede", ""


def fechar_navegador():
    """Fecha só o Chrome deste perfil (o Chrome normal do dono continua)."""
    # 01/11 dona logou a conta nesse Chrome pra dar like: fecha COM CALMA (taskkill sem /F = o Chrome grava os
    # cookies/login), espera, e só força o que sobrar; depois guarda cópia dos cookies
    pega = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like '*"
            + str(PERFIL) + "*' }")
    ps = (f"$p = @({pega}); if ($p.Count) {{ $p | ForEach-Object {{ taskkill /PID $_.ProcessId 2>$null | Out-Null }}; "
          f"for ($i=0; $i -lt 15 -and @({pega}).Count; $i++) {{ Start-Sleep 1 }}; "
          f"@({pega}) | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }} }}")
    try:
        subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps], timeout=90,
                       capture_output=True, creationflags=SEM_JANELA)
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:  # cópia dos cookies (login do YouTube) — se o perfil corromper, volta daqui
        import shutil
        for rel in (r"Default\Network\Cookies", r"Default\Login Data", r"Local State"):
            orig = PERFIL / rel
            if orig.exists():
                dest = BASE / "backup_login" / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(orig, dest)
    except OSError:
        pass
    prefs = PERFIL / "Default" / "Preferences"  # fechado à força: sem "restaurar páginas?" na próxima vez
    d = ler(prefs, None)
    if isinstance(d, dict):
        d.setdefault("profile", {}).update(exit_type="Normal", exited_cleanly=True)
        try:
            prefs.write_text(json.dumps(d), encoding="utf-8")
        except OSError:
            pass


def abrir(vid):
    fechar_navegador()
    subprocess.Popen([CHROME, f"--user-data-dir={PERFIL}", "--no-first-run", "--no-default-browser-check",
                      "--start-maximized", "--autoplay-policy=no-user-gesture-required", "--new-window",
                      f"https://www.youtube.com/watch?v={vid}"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def rodada(est, vistos):
    agora = datetime.now(timezone.utc)
    fila = ler(FILA, {})
    itens = fila.get("videos", [])
    vencidos = sorted((v for v in itens if v.get("id") and v["id"] not in vistos and v.get("quando")
                       and agora - timedelta(hours=JANELA_H) <= dt(v["quando"]) <= agora), key=lambda v: v["quando"])
    est.update(atualizado=agora.isoformat(timespec="seconds"), pendentes=len(vencidos),
               proximo=min((v["quando"] for v in itens if v.get("quando") and dt(v["quando"]) > agora), default=None),
               fila_recebida=fila.get("gerado"))
    if PAUSADO.exists():
        est["situacao"] = "pausado (arquivo PAUSADO)"
        return
    if tela_bloqueada():
        est["situacao"] = "tela bloqueada: esperando alguém olhar"
        return
    atual = est.get("atual") or {}
    if atual and time.time() - atual.get("aberto_ts", 0) < MIN_S:
        est["situacao"] = f"mostrando {atual.get('id')}"
        return
    for v in vencidos[:CHECAGENS_POR_RODADA]:
        situ, titulo = no_ar(v["id"])
        if situ == "rede":
            est["situacao"] = "sem internet pra checar o YouTube"
            return
        atraso_min = (agora - dt(v["quando"])).total_seconds() / 60
        if situ == "nao" and atraso_min > DESISTE_MIN:
            vistos[v["id"]] = {"aberto": agora.isoformat(timespec="seconds"), "titulo": "", "canal": v.get("canal"),
                               "nao_abriu": "não ficou público"}
            log(f"desistiu de {v['id']} ({v.get('canal')}): {atraso_min:.0f} min depois da hora e não está público")
            continue
        if situ == "nao" or (situ == "401" and atraso_min < ESPERA_401_MIN):
            continue
        abrir(v["id"])
        atual = {"id": v["id"], "titulo": titulo, "canal": v.get("canal"), "projeto": v.get("projeto"),
                 "quando": v["quando"], "aberto": agora.isoformat(timespec="seconds"), "aberto_ts": time.time()}
        vistos[v["id"]] = {"aberto": atual["aberto"], "titulo": titulo, "canal": v.get("canal")}
        est["atual"] = atual
        est["ultimos"] = ([{k: atual[k] for k in ("id", "titulo", "canal", "aberto")}] + est.get("ultimos", []))[:20]
        est["situacao"] = f"mostrando {v['id']}"
        log(f"abriu {v['id']} ({v.get('canal')}) {titulo[:80]!r}")
        return
    est["situacao"] = "mostrando " + atual["id"] if atual else "nada novo no ar"


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    est, vistos = ler(ESTADO, {}), ler(VISTOS, {})
    limite = (datetime.now(timezone.utc) - timedelta(days=VISTOS_DIAS)).isoformat()
    vistos = {k: v for k, v in vistos.items() if v.get("aberto", "") >= limite}
    try:
        rodada(est, vistos)
    except Exception as e:  # noqa: BLE001
        est["situacao"] = f"erro: {type(e).__name__}: {e}"
        log(est["situacao"])
    gravar(VISTOS, vistos)
    gravar(ESTADO, est)


if __name__ == "__main__":
    main()
