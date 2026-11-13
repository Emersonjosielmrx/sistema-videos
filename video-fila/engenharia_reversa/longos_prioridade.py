"""Longos de parceiro que a dona marcou como prioridade (29/10): metadados (sem baixar o vídeo) + capa em alta.
1 por vez pela vez única do yt-dlp, pausa entre eles, para no 1º bloqueio. Já feito = pula.
Grava longos_prioridade.jsonl e as capas em D:\\hipercool-materiais\\engenharia_reversa\\capas_longos\\<id>.jpg"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401
import ytdlp_vez  # noqa: E402

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
SAIDA = AQUI / "longos_prioridade.jsonl"
CAPAS = Path(r"D:\hipercool-materiais\engenharia_reversa\capas_longos")
COOKIES = Path(r"D:\recapd-ambientes\producao\cookies.txt")
IDS = ["P-djtsSY2Co", "GFrKL-1J_xQ", "yKfgs7SXOb0", "bXe7-vR7o5M", "SNhb31ZuuFA", "ssMbrCz0fhE", "VgQUQTmYLeQ",
       "X90-SNMMCdg", "XNKCOSdfMrU", "4wufdzeZKgs", "6d2aEsFp6Qk", "nV2aNVwUL-A", "hJaAZWXA7i4", "5FDtWi2JmuE"]
PAUSA = 60


def capa(vid):
    CAPAS.mkdir(parents=True, exist_ok=True)
    destino = CAPAS / f"{vid}.jpg"
    if destino.exists():
        return
    for nome in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            with urllib.request.urlopen(f"https://i.ytimg.com/vi/{vid}/{nome}.jpg", timeout=30) as r:
                destino.write_bytes(r.read())
            return
        except OSError:
            continue


def main():
    feitos = set()
    if SAIDA.exists():
        for ln in SAIDA.read_text(encoding="utf-8").splitlines():
            try:
                feitos.add(json.loads(ln)["id"])
            except (ValueError, KeyError, TypeError):  # linha cortada (rodada morta no meio) não derruba as outras
                pass
    for i, vid in enumerate(IDS):
        capa(vid)
        if vid in feitos:
            continue
        falta = ytdlp_vez.pausado()
        if falta:
            print(f"IP pausado por mais {falta / 60:.0f} min — paro", flush=True)
            return
        cmd = ["yt-dlp", f"https://www.youtube.com/watch?v={vid}", "--skip-download", "--dump-json", "--no-warnings",
               "--no-playlist"]
        if COOKIES.exists():
            cmd += ["--cookies", str(COOKIES)]
        with ytdlp_vez.vez("engenharia reversa: longos prioridade"):
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if r.returncode:
            print(f"FALHOU {vid}: {(r.stderr or '').strip()[-200:]}", flush=True)
            if ytdlp_vez.bloqueio(r.stderr):  # o stderr inteiro: o aviso de robô vem antes do texto de cookies
                import amostra
                amostra.registrar_bloqueio(r.stderr, "longos prioridade")
                print("bloqueio do YouTube — pausei o yt-dlp de todos e paro", flush=True)
                return
        else:
            d = json.loads(r.stdout)
            linha = {k: d.get(k) for k in ("id", "title", "channel", "channel_id", "channel_follower_count",
                                           "view_count", "like_count", "comment_count", "duration", "upload_date",
                                           "description", "tags")}
            linha["capitulos"] = [c.get("title") for c in d.get("chapters") or []]
            with open(SAIDA, "a", encoding="utf-8") as f:
                f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            print(f"ok {vid} {linha['view_count']:,} views {linha['duration']}s {linha['channel']}", flush=True)
        if i < len(IDS) - 1:
            time.sleep(PAUSA)


if __name__ == "__main__":
    main()
