r"""gerente_videos.py — 23/11 dona: "todos os vídeos devem ser centralizados e controlados por scripts pra não encher o
disco, além de scripts pra saber tudo o que entrou, pra depois não ficarmos loucos procurando".

Achado (outro chat, 23/11): animes recap tinha 695 vídeos / 27,8 GB. 577 video_sem_capa.mp4 (16 GB) — o capar_shorts
guarda o original pra REFAZER a capa e o mover_shorts_postados só cuidava do video.mp4; longos postados em
"videos laterais" (3,7 GB) ficavam porque nenhum backup olhava essa pasta.

UM lugar pra saber o que tem e por quê: INVENTARIO_VIDEOS.md (+ estado\inventario_videos.json), refeito a cada rodada:
cada vídeo das pastas de produção com tipo, tamanho, data, se é da FILA (não postado), POSTADO, se está no Drive, e a
REGRA que vale pra ele. Limpeza (só com --limpar), por regras SEGURAS:
  R1 video_sem_capa.mp4 de Short JÁ POSTADO                       -> apaga (só servia pra refazer a capa antes de postar)
  R2 video_capa_tmp.mp4 / *.tmp.mp4 com > 24 h                    -> apaga (render de capa interrompido)
  R3 video_1080p.mp4 de Short já postado                          -> apaga (upscale; o postado é o que vale)
  R4 video.mp4 de Short postado                                   -> mover_shorts_postados.py (Drive + confere + apaga)
  R5 longo de "videos laterais" postado (ledger)                  -> rclone move pro Drive (confere por arquivo) e anota
  R6 fila_celulares\videos\*.mp4 sem pedido pendente              -> apaga (cópia da fila; o original está na pasta)
  NUNCA: vídeo não postado (é a fila) — no máximo vai pro Drive se o disco < DISCO_MIN_GB e tiver > 30 dias.
Tudo que apaga/move vai pra logs\gerente_videos.jsonl (o quê, regra, tamanho, onde ficou).
    python gerente_videos.py            # só inventário (não apaga nada)
    python gerente_videos.py --limpar   # inventário + regras R1..R6
Tarefa GerenteVideos (de 2 em 2 h). Desliga: estado\gerente_videos.off.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\video-fila")
SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
LATERAIS = Path(r"D:\hipercool-materiais\animes recap\videos laterais")
LONGOS_POSTAR = Path(r"D:\hipercool-materiais\_longos_postar")
LONGOS_POSTADOS = Path(r"D:\recapd-ambientes\producao\colab\longos_postados.json")
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
FILA_CEL = Path(r"D:\projeto celular sub controle\fila_celulares")
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
MANIFESTO = Path(r"D:\manhwa-react\logs\backup_drive.jsonl")
RCLONE = r"D:\tools\rclone.exe"
DRIVE_LONGOS = "manhwa-drive:videos-backup/anime/_longos_postados"
INV_MD = BASE / "INVENTARIO_VIDEOS.md"
INV_JSON = BASE / "estado" / "inventario_videos.json"
LOG = BASE / "logs" / "gerente_videos.jsonl"
DESLIGA = BASE / "estado" / "gerente_videos.off"
# outras pastas que guardam vídeo — entram no INVENTÁRIO (tamanho por pasta) pra ninguém precisar procurar
OUTRAS = [r"D:\veo\beta\videos", r"D:\veo\beta\videos_pos",
          r"D:\video-fila\produto_fila", r"D:\hipercool-materiais\historias-em-frames",
          r"D:\hipercool-materiais\animes recap\na_nuvem", r"D:\hipercool-materiais\animes recap\segurados",
          # 23/11: o workspace da produção é JUNCTION pras pastas centrais (assets, anime, videos...) — contava 8 GB em
          # dobro e dava falso alarme. Fica a pasta real de material (banco de clipes/músicas: NÃO é sobra).
          r"D:\hipercool-materiais\assets",r"D:\manhwa-react\saida", r"D:\claude-code-video\saida",
          r"D:\tmp"]
VID = (".mp4", ".mov", ".mkv", ".webm")


def log(m):
    print(m, flush=True)


def registrar(**k):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), **k}, ensure_ascii=False) + "\n")


def postados():
    """pastas (nome, minúsculo) e caminhos de vídeo que aparecem no uploads_ledger (= subiram pro YouTube)."""
    pastas, caminhos = set(), set()
    for ln in LEDGER.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        c = str(r.get("caminho") or "")
        if c:
            caminhos.add(c.lower())
            pastas.add(Path(c).parent.name.lower())
    return pastas, caminhos


def postado_ficha(pasta):
    """postar.json com posted_url de verdade (não fila de celular) também vale como postado."""
    try:
        p = json.loads((pasta / "postar.json").read_text("utf-8"))
    except (OSError, ValueError):
        return False
    u = str(p.get("posted_url") or "")
    return bool(u) and not u.startswith("fila_celular:")


def video_final_no_drive(pasta):
    return (pasta / "_NO_DRIVE.txt").exists()


def inventario():
    ja_pastas, ja_cam = postados()
    itens = []
    for pasta in (SHORTS.iterdir() if SHORTS.exists() else []):
        if not pasta.is_dir():
            continue
        post = pasta.name.lower() in ja_pastas or postado_ficha(pasta)
        no_drive = video_final_no_drive(pasta)
        for f in pasta.iterdir():
            if f.suffix.lower() not in VID or not f.is_file():
                continue
            st = f.stat()
            n = f.name.lower()
            if n == "video_sem_capa.mp4":
                # 23/11: 459 pastas do ESTOQUE tinham o video.mp4 final no Drive (_NO_DRIVE) e o sem-capa no PC (14 GB).
                # O sem-capa só serve pra refazer capa: vai pro Drive ao lado do final (R7) e sai do PC.
                regra = "R1 apagar" if post else ("R7 Drive+apagar" if no_drive else "fica (refazer capa antes de postar)")
            elif "capa_tmp" in n or n.endswith(".tmp.mp4"):
                regra = "R2 apagar" if time.time() - st.st_mtime > 86400 else "fica (render em curso)"
            elif n == "video_1080p.mp4":
                regra = "R3 apagar" if post else "fica"
            elif n == "video.mp4":
                regra = "R4 Drive+apagar" if post else "FILA (não postado)"
            else:
                regra = "fica (outro)"
            itens.append({"arq": str(f), "pasta": pasta.name, "tipo": n, "bytes": st.st_size,
                          "data": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"), "postado": post,
                          "final_no_drive": no_drive, "regra": regra, "onde": "shorts"})
    for f in (LATERAIS.rglob("*") if LATERAIS.exists() else []):
        if f.suffix.lower() not in VID or not f.is_file():
            continue
        post = str(f).lower() in ja_cam
        itens.append({"arq": str(f), "pasta": f.parent.name, "tipo": "longo", "bytes": f.stat().st_size,
                      "data": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"), "postado": post,
                      "final_no_drive": False, "regra": "R5 Drive+apagar" if post else "FILA (não postado)",
                      "onde": "videos laterais"})
    # 23/11: _longos_postar = onde o postar_longos baixa o longo do Drive pra subir. Já postado (longos_postados.json)
    # = sobra (o original segue no Drive, nuvem.json "drive") -> R8 confere o tamanho no Drive e apaga.
    try:
        lp = json.loads(LONGOS_POSTADOS.read_text("utf-8"))
        ja_longos = {str(x.get("nome")) for x in (lp.get("postados") if isinstance(lp, dict) else lp) or []}
    except (OSError, ValueError):
        ja_longos = set()
    for f in (LONGOS_POSTAR.glob("*/*.mp4") if LONGOS_POSTAR.exists() else []):
        nome = f.parent.name
        post = nome in ja_longos
        itens.append({"arq": str(f), "pasta": nome, "tipo": "longo_baixado", "bytes": f.stat().st_size,
                      "data": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"), "postado": post,
                      "final_no_drive": None, "regra": "R8 conferir Drive+apagar" if post else "FILA (não postado)",
                      "onde": "_longos_postar"})
    pend = {json.loads(p.read_text("utf-8")).get("video", "").lower()
            for p in (FILA_CEL / "pendentes").glob("*.json")} if (FILA_CEL / "pendentes").exists() else set()
    for f in ((FILA_CEL / "videos").glob("*.mp4") if (FILA_CEL / "videos").exists() else []):
        itens.append({"arq": str(f), "pasta": "fila_celulares", "tipo": "copia_fila_celular", "bytes": f.stat().st_size,
                      "data": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"), "postado": None,
                      "final_no_drive": None, "regra": "fica (pedido pendente)" if str(f).lower() in pend
                      else "R6 apagar", "onde": "fila_celulares"})
    outras = {}
    for o in OUTRAS:
        p = Path(o)
        if not p.exists():
            continue
        n = b = 0
        for f in p.rglob("*"):
            if f.suffix.lower() in VID and f.is_file():
                n += 1
                b += f.stat().st_size
        outras[o] = (n, b)
    return itens, outras


def escrever(itens, outras, feito=None):
    agora = datetime.now()
    livre = shutil.disk_usage("D:\\").free / 1e9
    por = defaultdict(lambda: [0, 0])
    for x in itens:
        k = (x["onde"], x["tipo"] if x["onde"] == "shorts" else x["onde"], x["regra"])
        por[k][0] += 1
        por[k][1] += x["bytes"]
    linhas = [f"# 📦 Inventário de vídeos — {agora:%d/%m %H:%M}", "",
              f"Disco D livre: **{livre:.1f} GB**. Gerado por `video-fila\\gerente_videos.py` (tarefa GerenteVideos, "
              "2 em 2 h). Log do que foi apagado/movido: `video-fila\\logs\\gerente_videos.jsonl`.", "",
              "## Pastas de produção (com regra)", "",
              "| Onde | Tipo | Regra | Arquivos | GB |", "|---|---|---|---:|---:|"]
    for (onde, tipo, regra), (n, b) in sorted(por.items(), key=lambda kv: -kv[1][1]):
        linhas.append(f"| {onde} | {tipo} | {regra} | {n} | {b / 1e9:.2f} |")
    linhas += ["", "## Outras pastas com vídeo (só contagem — sem regra automática ainda)", "",
               "| Pasta | Vídeos | GB |", "|---|---:|---:|"]
    for o, (n, b) in sorted(outras.items(), key=lambda kv: -kv[1][1]):
        linhas.append(f"| `{o}` | {n} | {b / 1e9:.2f} |")
    longos = [x for x in itens if x["onde"] == "videos laterais"]
    if longos:
        linhas += ["", "## Longos em `videos laterais`", "", "| Pasta | GB | Postado | Regra |", "|---|---:|---|---|"]
        linhas += [f"| {x['pasta']} | {x['bytes'] / 1e9:.2f} | {'sim' if x['postado'] else 'não'} | {x['regra']} |"
                   for x in longos]
    if feito:
        linhas += ["", "## Última limpeza", ""] + [f"- {k}: {n} arquivo(s), {b / 1e9:.2f} GB" for k, (n, b) in feito.items()]
    INV_MD.write_text("\n".join(linhas) + "\n", "utf-8")
    INV_JSON.parent.mkdir(exist_ok=True)
    INV_JSON.write_text(json.dumps({"em": agora.isoformat(timespec="seconds"), "livre_gb": round(livre, 1),
                                    "itens": itens, "outras": outras}, ensure_ascii=False), "utf-8")


def rclone_move_conferido(arq, destino):
    """move UM arquivo pro Drive: rclone move apaga o local só depois de conferir o tamanho lá."""
    r = subprocess.run([RCLONE, "move", str(arq), destino, "--retries", "5"], capture_output=True, text=True,
                       timeout=7200, creationflags=0x08000000)
    return r.returncode == 0 and not Path(arq).exists()


def limpar(itens):
    feito = defaultdict(lambda: [0, 0])
    for x in itens:
        r = x["regra"]
        f = Path(x["arq"])
        if not f.exists():
            continue
        if r in ("R1 apagar", "R2 apagar", "R3 apagar", "R6 apagar"):
            f.unlink()
        elif r == "R7 Drive+apagar":
            # mesma pasta do video.mp4 final no Drive (linha do _NO_DRIVE.txt)
            alvo = (f.parent / "_NO_DRIVE.txt").read_text("utf-8", "ignore").strip().splitlines()
            dest = alvo[0].rsplit("/", 1)[0] if alvo and "/" in alvo[0] and ":" in alvo[0] else None
            if not dest or not rclone_move_conferido(f, dest):
                registrar(arq=str(f), regra=r, falhou=True, destino=dest)
                continue
        elif r == "R8 conferir Drive+apagar":
            # o original do Drive é o "drive" do nuvem.json da ficha; só apaga se lá existir com o MESMO tamanho
            dest = None
            for nj in list(FICHAS.glob(f"{x['pasta']}/nuvem.json")):
                try:
                    dest = json.loads(nj.read_text("utf-8")).get("drive")
                except (OSError, ValueError):
                    pass
            tam_drive = None
            if dest:
                rr = subprocess.run([RCLONE, "lsjson", dest], capture_output=True, text=True, timeout=120,
                                    creationflags=0x08000000)
                try:
                    tam_drive = (json.loads(rr.stdout or "[]") or [{}])[0].get("Size")
                except (ValueError, IndexError):
                    tam_drive = None
            if tam_drive != x["bytes"]:
                registrar(arq=str(f), regra=r, falhou=True, destino=dest, tam_drive=tam_drive)
                continue
            f.unlink()
        elif r == "R5 Drive+apagar":
            dest = f"{DRIVE_LONGOS}/{x['pasta']}"
            if not rclone_move_conferido(f, dest):
                registrar(arq=str(f), regra=r, falhou=True)
                continue
            (f.parent / "_NO_DRIVE.txt").write_text(f"{dest}/{f.name}\n", encoding="utf-8")
            with MANIFESTO.open("a", encoding="utf-8") as m:
                m.write(json.dumps({"em": datetime.now().astimezone().isoformat(timespec="seconds"), "local": str(f),
                                    "drive": f"{dest}/{f.name}", "nome": f.name, "bytes": x["bytes"]},
                                   ensure_ascii=False) + "\n")
        else:
            continue
        feito[r][0] += 1
        feito[r][1] += x["bytes"]
        registrar(arq=str(f), regra=r, bytes=x["bytes"], pasta=x["pasta"])
    # R4: o mover já existente (lote + confere no Drive + apaga só o que bateu)
    if any(x["regra"] == "R4 Drive+apagar" for x in itens):
        r = subprocess.run([sys.executable, r"D:\hipercool-materiais\comum\mover_shorts_postados.py"],
                           capture_output=True, text=True, timeout=7200, creationflags=0x08000000)
        feito["R4 Drive+apagar (mover_shorts_postados)"] = [r.returncode, 0]
    return feito


def main():
    if DESLIGA.exists():
        return
    itens, outras = inventario()
    feito = None
    if "--limpar" in sys.argv:
        feito = limpar(itens)
        itens, outras = inventario()
    escrever(itens, outras, feito)
    print(INV_MD.read_text("utf-8"))


if __name__ == "__main__":
    main()
