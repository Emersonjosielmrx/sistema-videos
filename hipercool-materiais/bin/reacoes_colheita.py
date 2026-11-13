"""reacoes_colheita.py — R5 (dono 22/10: "as reações têm que ser baixadas e reusadas pra não ficar baixando toda hora").

Colhe REAÇÕES REAIS dos vídeos de cada narrador parceiro UMA vez e guarda no banco dele (models\\rvc\\vozes\\<voz>\\
humano\\reacao_NN.wav + reacoes.json, o mesmo do reacoes_reais.py); a produção só REUSA. O treino (8 min) quase não
tinha reação (22/10: 0 aproveitáveis nos 13), então a fonte são os vídeos públicos do parceiro:
  1. últimos vídeos do canal (lista pequena)            -> PROXY (ytdlp_vez rótulo "lista")
  2. legenda automática pt com tempo por palavra (KB)   -> PROXY (rótulo "legenda")
  3. acha "caraca/nossa/meu deus/eita/vixe/putz/uau/misericórdia" e risada, sem palavrão por perto
  4. baixa SÓ ~4 s de áudio em volta (--download-sections) -> PROXY (é pequeno; nunca o IP de casa)
  5. separa a voz da trilha (demucs, Python comum) e corta nas pausas reais (silencedetect)
Para quando a voz tem META reações (reuso pra sempre). 1 voz por vez, pausa entre pedidos, para no 1º bloqueio.
Estado em amostras_voz\\reacoes_colheita.json (vídeos já lidos não são pedidos de novo).

    D:\\veo\\venv\\Scripts\\python.exe reacoes_colheita.py [voz ...] [--max-pedidos 40]
"""
import json
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
VOZES = RAIZ / "models" / "rvc" / "vozes"
ESTADO = RAIZ / "amostras_voz" / "reacoes_colheita.json"
TMP = Path(r"D:\tmp\reacoes_colheita")
FFMPEG = str(RAIZ / "bin" / "ffmpeg.exe")
PY_DEMUCS = RAIZ / "python" / "venv" / "Scripts" / "python.exe"
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
META = 4             # reações por voz: depois disso só reusa
VIDEOS_POR_CANAL = 15
PAUSA_S = 8
FORTES = re.compile(r"^(caraca|caramba|nossa|eita|vixe|vish|putz|uau|misericordia|kkk+|ha(ha)+h?)$")
PALAVRAO = re.compile(r"porra|caralh|merda|puta|foda|cacete|bucet|pqp|viad|arromb", re.I)

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
sys.path.insert(0, str(RAIZ / "bin"))


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def _norm(w):
    w = unicodedata.normalize("NFKD", str(w or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", w)


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    tmp = Path(str(p) + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


class Bloqueio(Exception):
    pass


def _ytdlp(args, rotulo, timeout=180):
    """yt-dlp SEMPRE pelo proxy da roda (nunca o IP de casa). Bloqueio do proxy = tira ele da roda e para a rodada."""
    import ytdlp_vez
    for _tentativa in range(3):  # proxy barrado sai da roda e vai o próximo (teste 22/10: 1 proxy barrado parava tudo)
        px = ytdlp_vez.proxy_url()
        if not px:
            raise Bloqueio("sem proxy na lista: não uso o IP de casa")
        with ytdlp_vez.vez(rotulo):
            r = subprocess.run(["yt-dlp", "--proxy", px, "--no-warnings", *args], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout, creationflags=SEM_JANELA)
        time.sleep(PAUSA_S)
        if not ytdlp_vez.bloqueio(r.stderr or ""):
            return r
        ytdlp_vez.proxy_ruim(px, r.stderr)
    raise Bloqueio((r.stderr or "")[-150:])


def _palavras_vtt(vtt):
    """[(t, palavra)] da legenda automática (tags <00:00:01.234><c> palavra</c>)."""
    def seg(t):
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    out, vistos = [], set()
    for linha in Path(vtt).read_text(encoding="utf-8", errors="ignore").splitlines():
        if "<c>" not in linha and not re.search(r"<\d\d:\d\d:\d\d\.\d+>", linha):
            continue
        cab = re.match(r"^(.*?)<(\d\d:\d\d:\d\d\.\d+)>", linha)
        partes = re.findall(r"<(\d\d:\d\d:\d\d\.\d+)><c>\s*([^<]+)</c>", linha)
        if cab and cab.group(1).strip():
            partes = [(None, cab.group(1).strip())] + partes
        t_ant = None
        for t, w in partes:
            tt = seg(t) if t else (t_ant or 0.0)
            chave = (round(tt, 2), w.strip())
            if chave not in vistos and w.strip():
                vistos.add(chave)
                out.append((tt, w.strip()))
            t_ant = tt
    return sorted(out)


def _achar(palavras):
    """[(t, texto)] das reações fortes com 3 palavras limpas de cada lado."""
    achados = []
    for i, (t, w) in enumerate(palavras):
        n = _norm(w)
        dois = n == "meu" and i + 1 < len(palavras) and _norm(palavras[i + 1][1]) == "deus"
        if not (FORTES.match(n) or dois):
            continue
        viz = " ".join(x[1] for x in palavras[max(0, i - 3):i + 4])
        if PALAVRAO.search(viz):
            continue
        achados.append((t, "meu deus" if dois else w))
    return achados


def _limpar(bruto, dst, ganho_db):
    """Separa a voz (demucs 2 stems) e corta a fala do meio nas pausas reais. True se ficou um trecho bom."""
    sep = TMP / "sep"
    subprocess.run([str(PY_DEMUCS), "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", str(sep),
                    str(bruto)], capture_output=True, timeout=600, creationflags=SEM_JANELA)
    voz = next(sep.glob(f"htdemucs/{bruto.stem}/vocals.wav"), None)
    if not voz:
        return False
    import reacoes_reais as rr
    sil = rr._silencios(voz, -40)
    meio = 1.5  # o bruto começa 1,5 s antes da palavra
    antes = [s for s in sil if s[1] <= meio + 0.25]
    depois = [s for s in sil if s[0] >= meio]
    a = max((s[1] for s in antes), default=max(0.0, meio - 0.3)) - 0.03
    b = min((s[0] for s in depois), default=meio + 1.0) + 0.08
    if not 0.2 <= b - a <= 1.6:
        return False
    d = b - a
    subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{max(0.0, a):.3f}", "-t", f"{d:.3f}", "-i", str(voz), "-af",
                    f"volume={ganho_db:.1f}dB,afade=t=in:d=0.015,afade=t=out:st={max(0.0, d - 0.06):.3f}:d=0.06",
                    "-ac", "1", "-ar", "44100", str(dst)], check=True, timeout=60, creationflags=SEM_JANELA)
    return dst.exists() and dst.stat().st_size > 8000


def colher(voz, handle, est, orcamento):
    pasta = VOZES / voz / "humano"
    if not pasta.exists():
        return orcamento
    banco = _ler(pasta / "reacoes.json", {"reacoes": []})
    if len(banco.get("reacoes") or []) >= META:
        return orcamento
    ganho = float(_ler(pasta / "humano.json", {}).get("ganho_db") or 0.0)
    ev = est.setdefault(voz, {"lidos": []})
    TMP.mkdir(parents=True, exist_ok=True)
    r = _ytdlp(["--flat-playlist", "--playlist-end", str(VIDEOS_POR_CANAL), "--print", "id",
                f"https://www.youtube.com/@{handle}/videos"], f"reacoes: lista {voz}")
    orcamento -= 1
    ids = [x.strip() for x in (r.stdout or "").splitlines() if len(x.strip()) == 11]
    log(f"{voz} (@{handle}): {len(ids)} vídeos, {len(banco['reacoes'])} reação(ões) no banco")
    for vid in ids:
        if orcamento <= 0 or len(banco["reacoes"]) >= META:
            break
        if vid in ev["lidos"]:
            continue
        for f in TMP.glob("leg*"):
            f.unlink()
        _ytdlp(["--skip-download", "--write-auto-subs", "--sub-langs", "pt", "--sub-format", "vtt", "-o",
                str(TMP / "leg"), f"https://www.youtube.com/watch?v={vid}"], f"reacoes: legenda {voz}")
        orcamento -= 1
        ev["lidos"].append(vid)
        vtt = next(TMP.glob("leg*.vtt"), None)
        achados = _achar(_palavras_vtt(vtt)) if vtt else []
        log(f"  {vid}: {len(achados)} reação(ões) na legenda " + ", ".join(f"{w}@{t:.0f}s" for t, w in achados[:4]))
        for t, w in achados[:2]:
            if orcamento <= 0 or len(banco["reacoes"]) >= META:
                break
            bruto = TMP / f"{voz}_{vid}_{int(t)}.wav"
            bruto.unlink(missing_ok=True)
            _ytdlp(["-f", "bestaudio", "--download-sections", f"*{max(0, t - 1.5):.2f}-{t + 2.5:.2f}", "-x",
                    "--audio-format", "wav", "-o", str(bruto.with_suffix(".%(ext)s")),
                    f"https://www.youtube.com/watch?v={vid}"], f"reacoes: trecho {voz}", timeout=300)
            orcamento -= 1
            if not bruto.exists():
                continue
            dst = pasta / f"reacao_{len(banco['reacoes']):02d}.wav"
            if _limpar(bruto, dst, ganho):
                banco["reacoes"].append({"arq": dst.name, "texto": w, "video": vid, "t": round(t, 2),
                                         "fonte": "colheita", "em": datetime.now().isoformat(timespec="minutes")})
                _gravar(pasta / "reacoes.json", banco)
                log(f"  + {dst.name}: '{w}' de {vid} @{t:.1f}s")
        _gravar(ESTADO, est)
    return orcamento


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import clone2
    orc = int(sys.argv[sys.argv.index("--max-pedidos") + 1]) if "--max-pedidos" in sys.argv else 40
    # 23/10: o "40" do --max-pedidos entrava aqui como nome de voz -> nenhuma voz casava e a tarefa das 01:30 saía calada
    valor = sys.argv.index("--max-pedidos") + 1 if "--max-pedidos" in sys.argv else -1
    pedidos = [a for i, a in enumerate(sys.argv) if i >= 1 and i != valor and not a.startswith("--")]
    log(f"início: orçamento {orc} pedidos" + (f", só {', '.join(pedidos)}" if pedidos else ", todas as vozes"))
    est = _ler(ESTADO, {})
    for voz, handle in clone2.parceiros():
        if pedidos and voz not in pedidos:
            continue
        try:
            orc = colher(voz, handle, est, orc)
        except Bloqueio as b:
            log(f"bloqueio/sem proxy ({b}): paro a rodada")
            break
        finally:
            _gravar(ESTADO, est)
        if orc <= 0:
            log("orçamento de pedidos da rodada acabou")
            break


if __name__ == "__main__":
    main()
