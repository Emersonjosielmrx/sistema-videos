# -*- coding: utf-8 -*-
"""Disco do MS Energy no Drive (25/10, dono: "o que o MS Energy tem de tanto pra ocupar 800 MB? vídeo e foto têm que usar
o Drive"). Fica no PC só o que a produção ainda vai usar:

  trechos   os 11 vídeos-fonte do vídeo real (182 MB inteiros) viram só os pedaços usados (clipes.json:
            trecho_<id>.mp4, inicio 0); o original some do PC SÓ se estiver no Drive (ms-energy/material_real/videos)
  postados  vídeo pronto que já saiu no Instagram E no TikTok -> manhwa-drive:ms-energy/videos_postados
  antigos   vídeo de antes do ms_v2 que nunca mais pode sair (fala proibida) -> manhwa-drive:ms-energy/videos_antigos
  crus      clipe cru do Veo com mais de 3 dias (o final já foi montado) -> manhwa-drive:ms-energy/veo_clips

rclone move só apaga daqui depois de subir inteiro. Roda sozinho 1x/dia pelo vigia (MSEnergy_VigiaClientes).
  python arquivar_drive_ms.py            # faz
  python arquivar_drive_ms.py --ver      # só mostra
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe"
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
RAIZ = Path(r"D:\ms-energy")
CLIPES = RAIZ / "assets" / "videos_reais" / "clipes.json"
VIDEOS_FONTE = RAIZ / "assets" / "fotos_instagram" / "google_fotos" / "videos"
SHORTS = RAIZ / "videos" / "shorts_veo"
CRUS = RAIZ / "cache" / "veo_clips"
LOG_POST = RAIZ / "videos" / "postagem_log.json"
DRIVE = "manhwa-drive:ms-energy"
ESTADO = RAIZ / "cache" / "arquivar_drive.json"


def _rc(*args, timeout=1800):
    r = subprocess.run([RCLONE, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    return r.returncode == 0, (r.stderr or r.stdout)[-300:]


_LISTAS = {}


def _no_drive(remoto, local):
    """O arquivo está no Drive com o mesmo tamanho? Lê a pasta do Drive 1 vez (25/10: 1 lsjson por arquivo estourou o
    tempo com o Drive lento) e, se o Drive não responder, responde 'não' (o arquivo fica no PC)."""
    pasta, nome = remoto.rsplit("/", 1)
    if pasta not in _LISTAS:
        try:
            r = subprocess.run([RCLONE, "lsjson", pasta, "--files-only"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=900)
            _LISTAS[pasta] = {x["Name"]: x["Size"] for x in json.loads(r.stdout or "[]")} if r.returncode == 0 else {}
        except (subprocess.TimeoutExpired, ValueError):
            _LISTAS[pasta] = {}
    return _LISTAS[pasta].get(nome) == local.stat().st_size


def recortar_trechos(ver=False, log=print):
    d = json.loads(CLIPES.read_text("utf-8"))
    mudou, fontes = False, set()
    for c in d["clipes"]:
        if c["arquivo"].startswith("trecho_"):
            continue
        orig = VIDEOS_FONTE / c["arquivo"]
        if not orig.exists():
            continue
        fontes.add(c["arquivo"])
        dest = VIDEOS_FONTE / f"trecho_{c['id']}.mp4"
        if ver:
            log(f"  recortaria {c['id']}: {c['arquivo']} {c['inicio']}-{c['fim']} s")
            continue
        r = subprocess.run([FF, "-y", "-v", "error", "-ss", f"{c['inicio']:.2f}", "-t", f"{c['fim'] - c['inicio']:.2f}",
                            "-i", str(orig), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", str(dest)], capture_output=True, text=True, timeout=300)
        if r.returncode or not dest.exists() or dest.stat().st_size < 50_000:
            log(f"  [trechos] {c['id']}: recorte falhou - fica o original")
            continue
        c.update(origem=c["arquivo"], origem_inicio=c["inicio"], arquivo=dest.name, fim=round(c["fim"] - c["inicio"], 2),
                 inicio=0.0)
        mudou = True
    if mudou:
        CLIPES.with_suffix(".json.bak_20261025").write_text(CLIPES.read_text("utf-8"), "utf-8") \
            if not CLIPES.with_suffix(".json.bak_20261025").exists() else None
        CLIPES.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    usados = {c["arquivo"] for c in d["clipes"]}
    livre = 0
    for nome in fontes:
        orig = VIDEOS_FONTE / nome
        if ver or nome in usados or not orig.exists():
            continue
        if _no_drive(f"{DRIVE}/material_real/videos/{nome}", orig):
            livre += orig.stat().st_size
            orig.unlink()
        else:
            log(f"  [trechos] {nome} NÃO está no Drive igual - fica no PC")
    log(f"[trechos] {len(fontes)} vídeo(s)-fonte; liberados {livre / 2**20:.0f} MB")


def _mover(arquivos, destino, ver, rotulo, log):
    arquivos = [a for a in arquivos if a.exists()]
    tam = sum(a.stat().st_size for a in arquivos) / 2**20
    if ver or not arquivos:
        log(f"[{rotulo}] {len(arquivos)} arquivo(s), {tam:.0f} MB -> {destino}{' (só mostrando)' if ver else ''}")
        return
    lista = RAIZ / "cache" / f"_mover_{rotulo}.txt"
    lista.write_text("\n".join(a.name for a in arquivos), "utf-8")
    ok, msg = _rc("move", str(arquivos[0].parent), destino, "--files-from", str(lista))
    lista.unlink(missing_ok=True)
    log(f"[{rotulo}] {len(arquivos)} arquivo(s), {tam:.0f} MB -> {destino}: {'ok' if ok else 'FALHOU ' + msg}")


def arquivar(ver=False, log=print):
    sys.path.append(r"D:\postador-de-videos\bin")
    log_post = json.loads(LOG_POST.read_text("utf-8")) if LOG_POST.exists() else {}
    mp4 = list(SHORTS.glob("*.mp4"))
    postados = [p for p in mp4 if log_post.get(p.stem, {}).get("insta") and log_post.get(p.stem, {}).get("tiktok")]
    antigos = []
    try:
        import postar_ms_energy as pm
        for p in mp4:
            if p in postados or p.stem.startswith("ms_energy_solar_202610"):
                continue
            meta = json.loads(p.with_suffix(".json").read_text("utf-8")) if p.with_suffix(".json").exists() else {}
            if meta.get("pipeline") != "ms_v2":
                # 25/10 (dono: "deve ficar só os pra postar no dia"): TODO antigo vai pro Drive (a reserva do dia vazio
                # passa a ser o vídeo real, gerado na hora sem crédito)
                antigos.append(p)
    except Exception as e:  # noqa: BLE001
        log(f"[antigos] não deu pra conferir ({type(e).__name__}) - ficam no PC")
    junto = lambda ps: ps + [p.with_suffix(".json") for p in ps if p.with_suffix(".json").exists()]  # noqa: E731
    _mover(junto(postados), f"{DRIVE}/videos_postados", ver, "postados", log)
    _mover(junto(antigos), f"{DRIVE}/videos_antigos", ver, "antigos", log)
    limite = datetime.now().timestamp() - 3 * 86400
    _mover([p for p in CRUS.glob("*.mp4") if p.stat().st_mtime < limite], f"{DRIVE}/veo_clips", ver, "crus", log)


def arquivar_dia(log=print):
    """1x por dia (chamado pelo vigia)."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    try:
        if json.loads(ESTADO.read_text("utf-8")).get("ultima") == hoje:
            return
    except (OSError, ValueError):
        pass
    recortar_trechos(log=log)
    arquivar(log=log)
    ESTADO.write_text(json.dumps({"ultima": hoje}), "utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ver = "--ver" in sys.argv
    recortar_trechos(ver)
    arquivar(ver)
