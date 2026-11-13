"""Amostra de Shorts dos parceiros para medir o VÍDEO (29/10). Para cada parceiro (os que mais viraram Shorts nossos
primeiro), baixa devagar os N mais vistos e os N menos vistos da lista que o Cortes já guardou (discover_canal), em
até 480p, com o .info.json (data de publicação, para tirar os novos demais da conta).

Regras: 1 download por vez pela vez única (ytdlp_vez), PAUSA entre downloads, não baixa com o IP pausado e PARA a
rodada no 1º bloqueio (avisa o ytdlp_vez para todo mundo esperar). Sem proxy (a banda é da voz). Já baixado = pula.

    python amostra.py [--n 3] [--max 40] [--pausa 120] [--ensaio]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401
import ytdlp_vez  # noqa: E402

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
CACHE = Path(r"D:\recapd-ambientes\producao\workspace\cache\discover_canal")
SAIDA = Path(r"D:\hipercool-materiais\engenharia_reversa\amostras")
COOKIES = Path(r"D:\recapd-ambientes\producao\cookies.txt")
LOG = AQUI / "amostra.log"
MARCA_BLOQUEIO = AQUI / "bloqueio_er.json"
MIN_LIVRE_GB = 5
HORAS_SEM_BAIXAR = 12  # D41: depois de um bloqueio causado pela ER, a produção fica com o IP


def log(msg):
    linha = f"{time.strftime('%d/%m %H:%M:%S')} {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def registrar_bloqueio(stderr, rotulo):
    """30/10: bloqueio que ESTA pasta causou. Pausa o yt-dlp do PC com o motivo marcado "engenharia reversa" (antes ia
    só a cauda do stderr, e o continuo nunca reconhecia o bloqueio como da ER) e guarda a hora em bloqueio_er.json,
    porque a pausa global é sobrescrita pelo próximo projeto que levar bloqueio."""
    ytdlp_vez.pausar(f"engenharia reversa: {rotulo}: {(stderr or '').strip()[-150:]}")
    try:
        MARCA_BLOQUEIO.write_text(json.dumps({"em": time.time(), "quando": time.strftime("%d/%m %H:%M"),
                                              "rotulo": rotulo}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def bloqueio_recente(horas=HORAS_SEM_BAIXAR):
    """True se a ER causou bloqueio do YouTube há menos de `horas` (marca própria ou a pausa global com motivo da ER)."""
    try:
        if time.time() - float(json.loads(MARCA_BLOQUEIO.read_text(encoding="utf-8")).get("em") or 0) < horas * 3600:
            return True
    except (OSError, ValueError, AttributeError):
        pass
    try:
        d = json.loads(Path(ytdlp_vez.PAUSA).read_text(encoding="utf-8"))
        return "engenharia reversa" in str(d.get("motivo", "")) and time.time() - float(d.get("ate") or 0) < horas * 3600
    except (OSError, ValueError, AttributeError, TypeError):
        return False


def nome_parceiro(url):
    m = re.search(r"/@([^/]+)", url) or re.search(r"/channel/([^/]+)", url)
    return (m.group(1) if m else re.sub(r"\W+", "_", url))[:40]


def listas():
    """{parceiro: itens com views, sem 'Parte N'}"""
    out = {}
    for f in CACHE.glob("*.json"):
        try:
            itens = [i for i in json.loads(f.read_text(encoding="utf-8")) if i.get("views") and not i.get("parte")]
        except (OSError, ValueError):
            continue
        if len(itens) >= 30:
            out[nome_parceiro(itens[0].get("parceiro") or f.stem)] = itens
    return out


def uso_nosso():
    """quantos Shorts nossos saíram de cada parceiro (para ir primeiro nos que importam)"""
    c = Counter()
    for ln in Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl").read_text("utf-8").splitlines():
        try:
            r = json.loads(ln)
            if r.get("projeto") == "parceiro":
                d = json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
                c[d.get("fonte", "").rstrip("/").split("/")[-1]] += 1
        except Exception:  # noqa: BLE001
            pass
    return c


def baixar(item, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    cmd = ["yt-dlp", item["url"], "-f", "bv*[height<=480]+ba/b[height<=480]/b", "-S", "res,vcodec:h264",
           "--merge-output-format", "mp4", "-o", str(pasta / "video.%(ext)s"), "--write-info-json",
           "--no-warnings", "--no-playlist"]
    if COOKIES.exists():
        cmd += ["--cookies", str(COOKIES)]
    with ytdlp_vez.vez("engenharia reversa: amostra"):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="quantos de cima e quantos de baixo por parceiro")
    ap.add_argument("--max", type=int, default=40, help="downloads nesta rodada")
    ap.add_argument("--pausa", type=int, default=120, help="segundos entre downloads")
    ap.add_argument("--ensaio", action="store_true")
    a = ap.parse_args()
    if not a.ensaio and bloqueio_recente():  # vale também para o semanal.bat (a rodada maior, --max 30)
        log(f"a ER causou bloqueio do YouTube há menos de {HORAS_SEM_BAIXAR} h (D41) — não baixo nesta rodada")
        return
    ls = listas()
    uso = uso_nosso()
    ordem = sorted(ls, key=lambda p: -sum(uso[i["id"]] for i in ls[p]))
    fila = []
    # ronda: 1 de cima + 1 de baixo de cada parceiro, depois o 2º de cada... (para todos ganharem par cedo)
    for k in range(a.n):
        for p in ordem:
            itens = sorted(ls[p], key=lambda i: -i["views"])
            for grupo, it in (("cima", itens[k]), ("baixo", itens[-1 - k])):
                fila.append((p, grupo, it))
    feitos = 0
    for p, grupo, it in fila:
        pasta = SAIDA / p / f"{grupo}_{it['id']}"
        if any(pasta.glob("video.mp4")):
            continue
        if feitos >= a.max:
            break
        if a.ensaio:
            log(f"[ensaio] {p} {grupo} {it['views']:,} {it['title'][:60]}")
            feitos += 1
            continue
        livre = shutil.disk_usage("D:\\").free / 1e9
        if livre < MIN_LIVRE_GB:  # 29/10: D: chegou a 1,7 GB — amostra nunca disputa espaço com a produção
            log(f"D: com {livre:.1f} GB livres (< {MIN_LIVRE_GB}) — paro a rodada")
            break
        falta = ytdlp_vez.pausado()
        if falta:
            log(f"IP pausado por mais {falta / 60:.0f} min — paro a rodada (sem proxy)")
            break
        r = baixar(it, pasta)
        if r.returncode:
            log(f"FALHOU {p} {it['id']}: {(r.stderr or '').strip()[-200:]}")
            # 30/10: o "Sign in to confirm you're not a bot" vem ANTES do texto longo sobre cookies; olhar só a cauda
            # (300 caracteres) deixou passar o bloqueio de 04:21 e a rodada seguiu tentando
            if ytdlp_vez.bloqueio(r.stderr):
                registrar_bloqueio(r.stderr, f"amostra {p}")
                log("bloqueio do YouTube — pausei o yt-dlp de todos e paro a rodada")
                break
        else:
            (pasta / "lista.json").write_text(json.dumps({**it, "grupo": grupo, "parceiro_nome": p},
                                                         ensure_ascii=False), encoding="utf-8")
            log(f"ok {p} {grupo} {it['views']:,} {it['id']}")
        feitos += 1
        time.sleep(a.pausa)
    log(f"rodada acabou: {feitos} tentados")


if __name__ == "__main__":
    main()
