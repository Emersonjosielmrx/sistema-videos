#!/usr/bin/env python3
"""Visualizador do x200ma: abre no navegador, um por vez, cada vídeo que acabou de ir ao ar no YouTube.

A lista vem do PC1 (D:\\video-fila\\visualizador.py enviar -> ~/visualizador/fila.json, de 10 em 10 min). Só abre com a
tela desbloqueada (alguém olhando) e nunca o mesmo vídeo duas vezes. Like e comentário ficam com quem está assistindo.
Arquivo PAUSADO nesta pasta = não abre nada novo. Roda como serviço do usuário: systemctl --user status visualizador
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path.home() / "visualizador"
FILA = BASE / "fila.json"
VISTOS = BASE / "vistos.json"
ESTADO = BASE / "estado.json"
LOG = BASE / "visualizador.log"
PAUSADO = BASE / "PAUSADO"
PERFIL = BASE / "chrome-perfil"

MIN_S = 240        # cada vídeo fica aberto pelo menos isto antes de passar pro próximo da fila
JANELA_H = 6       # publicado há mais que isto: já passou, não abre
ESPERA_401_MIN = 10  # oEmbed 401/403 (incorporação desligada) depois da hora de publicar: abre mesmo assim
DESISTE_MIN = 120   # 404 até isto depois da hora de publicar = removido/bloqueado
CHECAGENS_POR_RODADA = 3  # consultas ao oEmbed por rodada (sem rajada no YouTube)
CICLO_S = 30
VISTOS_DIAS = 7


def log(msg):
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linha, flush=True)
    try:
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            LOG.replace(LOG.with_suffix(".log.1"))
        with LOG.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
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


def env_grafico():
    """O ambiente da sessão gráfica (Wayland/X) vem do gerenciador do usuário: depois de reiniciar, o serviço pode subir
    antes do login e herdar um ambiente sem tela."""
    env = dict(os.environ)
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    try:
        r = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True, text=True, timeout=10, env=env)
        for linha in r.stdout.splitlines():
            k, _, v = linha.partition("=")
            if k in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS", "XDG_SESSION_TYPE"):
                env[k] = v
    except (OSError, subprocess.TimeoutExpired):
        pass
    return env


def tela_bloqueada(env):
    """True = tela bloqueada/proteção de tela (ninguém olhando). Sem resposta do GNOME = trata como desbloqueada."""
    try:
        r = subprocess.run(["gdbus", "call", "--session", "--dest", "org.gnome.ScreenSaver", "--object-path",
                            "/org/gnome/ScreenSaver", "--method", "org.gnome.ScreenSaver.GetActive"],
                           capture_output=True, text=True, timeout=10, env=env)
        return "true" in r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False


def no_ar(vid):
    """'sim' (público), 'nao' (ainda não / removido), '401' (privado ou incorporação desligada) ou 'rede' (sem resposta)."""
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
            return "sim", d.get("title", "")
    except urllib.error.HTTPError as e:
        return ("401" if e.code in (401, 403) else "nao"), ""
    except (urllib.error.URLError, OSError, ValueError):
        return "rede", ""


def _processos_do_perfil():
    pids = []
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            try:
                cmd = (p / "cmdline").read_bytes().split(b"\0")
            except OSError:
                continue
            if f"--user-data-dir={PERFIL}".encode() in cmd:
                pids.append(int(p.name))
    return pids


def fechar_navegador():
    """Fecha só o Chrome deste perfil (o Chrome normal do dono continua)."""
    pids = _processos_do_perfil()
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    for _ in range(10):
        if not _processos_do_perfil():
            break
        time.sleep(1)
    for pid in _processos_do_perfil():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    prefs = PERFIL / "Default" / "Preferences"  # fechado à força: sem o aviso "restaurar páginas?" na próxima vez
    d = ler(prefs, None)
    if isinstance(d, dict):
        d.setdefault("profile", {}).update(exit_type="Normal", exited_cleanly=True)
        try:
            prefs.write_text(json.dumps(d), encoding="utf-8")
        except OSError:
            pass


def abrir(vid, env):
    fechar_navegador()
    url = f"https://www.youtube.com/watch?v={vid}"  # watch e não /shorts/: o Short não fica repetindo sozinho
    subprocess.Popen(["google-chrome", f"--user-data-dir={PERFIL}", "--no-first-run", "--no-default-browser-check",
                      "--start-maximized", "--autoplay-policy=no-user-gesture-required", "--new-window", url],
                     env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)


def rodada(est, vistos, env):
    agora = datetime.now(timezone.utc)
    itens = ler(FILA, {}).get("videos", [])
    vencidos = sorted((v for v in itens if v.get("id") and v["id"] not in vistos and v.get("quando")
                       and agora - timedelta(hours=JANELA_H) <= dt(v["quando"]) <= agora), key=lambda v: v["quando"])
    est.update(atualizado=agora.isoformat(timespec="seconds"), pendentes=len(vencidos),
               proximo=min((v["quando"] for v in itens if v.get("quando") and dt(v["quando"]) > agora), default=None),
               fila_recebida=ler(FILA, {}).get("gerado"))
    if PAUSADO.exists():
        est["situacao"] = "pausado (arquivo PAUSADO)"
        return
    if tela_bloqueada(env):
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
        if situ == "nao" and atraso_min > DESISTE_MIN:  # removido/bloqueado: para de perguntar
            vistos[v["id"]] = {"aberto": agora.isoformat(timespec="seconds"), "titulo": "", "canal": v.get("canal"),
                               "nao_abriu": "não ficou público"}
            log(f"desistiu de {v['id']} ({v.get('canal')}): {atraso_min:.0f} min depois da hora e não está público")
            continue
        if situ == "nao" or (situ == "401" and atraso_min < ESPERA_401_MIN):
            continue  # ainda não está público: tenta de novo na próxima rodada
        abrir(v["id"], env)
        atual = {"id": v["id"], "titulo": titulo, "canal": v.get("canal"), "projeto": v.get("projeto"),
                 "quando": v["quando"], "aberto": agora.isoformat(timespec="seconds"), "aberto_ts": time.time(),
                 "checagem": situ}
        vistos[v["id"]] = {"aberto": atual["aberto"], "titulo": titulo, "canal": v.get("canal")}
        est["atual"] = atual
        est["ultimos"] = ([{k: atual[k] for k in ("id", "titulo", "canal", "aberto")}] + est.get("ultimos", []))[:20]
        est["situacao"] = f"mostrando {v['id']}"
        log(f"abriu {v['id']} ({v.get('canal')}, {v.get('projeto')}) {titulo[:80]!r}")
        return
    est["situacao"] = "mostrando " + atual["id"] if atual else "nada novo no ar"


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    log("visualizador iniciado")
    while True:
        est, vistos = ler(ESTADO, {}), ler(VISTOS, {})
        limite = (datetime.now(timezone.utc) - timedelta(days=VISTOS_DIAS)).isoformat()
        vistos = {k: v for k, v in vistos.items() if v.get("aberto", "") >= limite}
        try:
            rodada(est, vistos, env_grafico())
        except Exception as e:  # noqa: BLE001 — uma rodada com defeito não derruba o serviço
            est["situacao"] = f"erro: {type(e).__name__}: {e}"
            log(est["situacao"])
        gravar(VISTOS, vistos)
        gravar(ESTADO, est)
        if "--uma" in sys.argv:
            return
        time.sleep(CICLO_S)


if __name__ == "__main__":
    main()
