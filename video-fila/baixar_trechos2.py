"""Trechos ORIGINAIS (a voz real do personagem falando o bordão) -> amostras_voz\\trechos_icones\\<voz>\\.
v2 (dono 21/10: "o Chapolin narrou sem nenhuma frase típica e tem tantas prontas no YouTube"; "o Buzz só fala 'ao
infinito', falta 'e além'"): Whisper medium + busca da FRASE INTEIRA (aproximada) em vez de 1 palavra no Whisper tiny;
o corte vai do começo ao fim da frase; vídeo curto cujo título é a frase vale inteiro; até 3 vídeos por frase; até 2
bordões por personagem. yt-dlp 1 por vez com a mesma trava da produção (ytdlp_vez) e pausa (sem rajada).
    python baixar_trechos2.py [voz ...]   (sem voz = todos os personagens sem trecho bom; REFAZER = refaz estes)"""
import difflib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

os.environ.setdefault("MKL_NUM_THREADS", "2")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import psutil  # noqa: E402
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)  # não atrasa o render da produção
import ytdlp_vez  # noqa: E402  (COMUM: 1 yt-dlp por vez no PC)
from faster_whisper import WhisperModel  # noqa: E402

VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
SAIDA = Path(r"D:\hipercool-materiais\amostras_voz\trechos_icones")
TMP = Path(r"D:\tmp\trechos_baixando")
REFAZER = {"buzz_lightyear"}  # trecho cortado antes do fim da frase
FRASES = {  # voz: [(busca, frase que tem que sair inteira)]; o resto usa os bordões do linguagem_v2.json
    # 23/10: bordões dos formatos com várias vozes (anime_formatos usa o áudio ORIGINAL quando a fala é só o bordão)
    "quico": [("quico gentalha gentalha chaves dublado", "gentalha gentalha")],
    "chiquinha": [("chiquinha isso isso isso chaves dublado", "isso isso isso")],
    "chaves_chapolin": [("chaves foi sem querer querendo dublado", "foi sem querer querendo")],
    "professor_girafales": [("professor girafales tá tá tá dona florinda", "dona florinda")],
    "chico_selton": [("chicó não sei só sei que foi assim auto da compadecida", "não sei só sei que foi assim")],
    "joao_grilo": [("joão grilo deixe de ser mentiroso chicó", "deixe de ser mentiroso")],
    "faustao": [("faustão ô loco meu", "ô loco meu")],
    "silvio_santos": [("silvio santos quem quer dinheiro", "quem quer dinheiro")],
    "galvao_bueno": [("galvão bueno haja coração amigo", "haja coração")],
    "pato_donald": [("pato donald dublado isso não é justo", "isso não é justo")],
    "chapolin_colorado": [("chapolin não contavam com minha astúcia", "não contavam com minha astúcia"),
                          ("chapolin colorado sigam-me os bons", "sigam-me os bons")],
    "buzz_lightyear": [("buzz lightyear ao infinito e além dublado", "ao infinito e além")],
    "capitao_nascimento": [("capitão nascimento pede pra sair tropa de elite", "pede pra sair"),
                           ("capitão nascimento missão dada é missão cumprida", "missão dada é missão cumprida")],
    "naruto": [("naruto tô certo dublado", "tô certo"), ("naruto dattebayo dublado", "dattebayo")],
    "lula": [("lula companheiros e companheiras", "companheiros e companheiras")],
    "dinho_mamonas_assassinas": [("mamonas assassinas você me deixa doidão", "me deixa doidão")],
    "seu_madruga": [("seu madruga a vingança nunca é plena", "a vingança nunca é plena")],
    "woody": [("woody tem uma cobra na minha bota dublado", "tem uma cobra na minha bota")],
    "walter_white_breaking_bad": [("walter white eu sou o perigo dublado", "eu sou o perigo")],
    "patolino": [("patolino você é desprezível dublado", "você é desprezível")],
    "homem_de_ferro_tony_stark": [("eu sou o homem de ferro dublado vingadores ultimato", "eu sou o homem de ferro")],
    "patrick_estrela": [("patrick estrela a maionese é um instrumento dublado", "maionese é um instrumento")],
    "seu_sirigueijo_peter_griffin": [("seu sirigueijo dinheiro dublado", "dinheiro")],
    "harry_potter": [("harry potter expelliarmus dublado", "expelliarmus")],
}
SR = 16000


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def baixar(busca, n):
    """n-ésimo resultado da busca (<= 4 min) como wav; (wav, (url, título, duração)) ou (None, motivo)."""
    falta = ytdlp_vez.pausado()
    if falta:  # 22/10: pedido durante o bloqueio do IP só alonga o bloqueio e para a produção dos Shorts
        raise SystemExit(f"yt-dlp em pausa (YouTube barrando o IP) por mais {falta / 60:.0f} min: rode depois")
    for f in TMP.glob("baixado.*"):
        f.unlink()
    with ytdlp_vez.vez("trechos icônicos"):
        r = subprocess.run(["yt-dlp", f"ytsearch5:{busca}", "--playlist-items", str(n), "--match-filter", "duration < 240",
                            "-f", "bestaudio", "-x", "--audio-format", "wav", "--print",
                            "after_move:%(webpage_url)s\t%(title)s\t%(duration)s", "-o", str(TMP / "baixado.%(ext)s"),
                            "--no-warnings"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=600)
    if ytdlp_vez.bloqueio(r.stderr):  # liga a pausa pra todos os projetos e para aqui (não queima os outros bordões)
        ytdlp_vez.pausar(f"trechos icônicos: {(r.stderr or '')[-150:]}")
        raise SystemExit("YouTube barrou o IP: pausa do yt-dlp ligada pra todos; trechos param aqui")
    time.sleep(8)  # sem rajada (17/10 a rajada bloqueou o IP da casa e parou a produção)
    w = TMP / "baixado.wav"
    linha = [l for l in (r.stdout or "").splitlines() if "\t" in l]
    if w.exists() and linha:
        url, tit, dur = (linha[-1].split("\t") + ["", ""])[:3]
        return w, (url, tit, float(dur or 0))
    return None, (r.stderr or "")[-160:].strip() or "nada baixado"


def achar(modelo, wav, frase):
    """(ini, fim, texto) da janela de palavras mais parecida com a frase (>= 0,62), ou None."""
    alvo = norm(frase).split()
    segs, _ = modelo.transcribe(str(wav), language="pt", word_timestamps=True, vad_filter=True,
                                clip_timestamps=[0, 180])
    palavras = [(norm(w.word), w.start, w.end) for s in segs for w in (s.words or []) if norm(w.word)]
    melhor = None
    for i in range(len(palavras)):
        for tam in (len(alvo) - 1, len(alvo), len(alvo) + 1, len(alvo) + 2):
            j = i + max(1, tam)
            if j > len(palavras):
                continue
            jan = " ".join(p[0] for p in palavras[i:j])
            r = difflib.SequenceMatcher(None, jan, " ".join(alvo)).ratio()
            if not melhor or r > melhor[0]:
                melhor = (r, palavras[i][1], palavras[j - 1][2], jan, palavras[i:j])
    if not melhor or melhor[0] < 0.62:
        return None
    # pedaços de fala pelas palavras: vão > 0,5 s entre elas (a pausa dramática do Buzz, mesmo com música por baixo)
    # sai do corte — "Ao infinito... e além!" vira uma frase só
    pedacos = []
    for _w, a, b in melhor[4]:
        if pedacos and a - pedacos[-1][1] <= 0.5:
            pedacos[-1][1] = b
        else:
            pedacos.append([a, b])
    return melhor[1], melhor[2], melhor[3], melhor[0], pedacos


def cortar(src, ini, fim, dst, pedacos=None):
    """Recorta [ini, fim] ou, com pedacos=[[a, b], ...], só a fala de cada pedaço emendada (folga de 0,12 s)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    final = "afade=t=in:d=0.04,areverse,afade=t=in:d=0.1,areverse,loudnorm=I=-18:TP=-1.5"
    if pedacos and len(pedacos) > 1:
        partes = "".join(f"[0:a]atrim=start={max(0, a - 0.12):.2f}:end={b + 0.12:.2f},asetpts=PTS-STARTPTS[p{k}];"
                         for k, (a, b) in enumerate(pedacos))
        filtro = partes + "".join(f"[p{k}]" for k in range(len(pedacos))) + \
            f"concat=n={len(pedacos)}:v=0:a=1,aresample=44100,{final}[s]"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", filtro, "-map", "[s]", "-ac", "1", str(dst)]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.2f}", "-to", f"{fim:.2f}", "-i", str(src), "-ac", "1",
               "-ar", "44100", "-af", "silenceremove=start_periods=1:start_threshold=-45dB," + final, str(dst)]
    subprocess.run(cmd, check=True)


def frases_da(voz):
    if voz in FRASES:
        return FRASES[voz]
    try:
        g = json.loads((VOZES / voz / "linguagem_v2.json").read_text(encoding="utf-8"))
        nome = json.loads((VOZES / voz / "personagem.json").read_text(encoding="utf-8"))["nome"]
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for b in (g.get("bordoes") or [])[:2]:
        b = re.sub(r"[!?.…]+$", "", str(b)).strip()
        if len(norm(b).split()) >= 2:
            out.append((f"{nome} {b} dublado", b))
    return out


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    modelo = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=2,
                          download_root=r"D:\hipercool-materiais\models\whisper")
    pedidos = sys.argv[1:]
    vozes = pedidos or sorted(p.parent.name for p in VOZES.glob("*/personagem.json"))
    prioridade = list(FRASES)  # os que o dono citou primeiro
    vozes.sort(key=lambda v: (prioridade.index(v) if v in prioridade else 99, v))
    rel_arq = SAIDA / "_relatorio_v2.json"
    rel = json.loads(rel_arq.read_text(encoding="utf-8")) if rel_arq.exists() else {}
    for voz in vozes:
        tj = SAIDA / voz / "trechos.json"
        if tj.exists() and voz not in REFAZER and voz not in pedidos:
            continue
        feitos, motivos = [], []
        for busca, frase in frases_da(voz):
            for n in (1, 2, 3):
                try:
                    wav, info = baixar(busca, n)
                except subprocess.TimeoutExpired:
                    wav, info = None, "yt-dlp passou de 10 min"
                if not wav:
                    motivos.append(f"{frase}: {info}")
                    if "not available" in str(info) or "unavailable" in str(info).lower():
                        continue  # esse resultado sumiu: tenta o próximo da busca
                    break  # sem mais resultados
                url, titulo, dur = info
                try:
                    if dur and dur <= 12 and difflib.SequenceMatcher(None, norm(titulo), norm(frase)).ratio() >= 0.6:
                        ini, fim, texto, nota, pedacos = 0.0, dur, f"(vídeo inteiro) {titulo}", 1.0, None
                    else:
                        a = achar(modelo, wav, frase)
                        if not a:
                            motivos.append(f"{frase}: não achada em {titulo[:50]}")
                            continue
                        ini, fim, texto, nota, pedacos = a
                    ini, fim = max(0.0, ini - 0.12), fim + 0.3
                    if fim - ini > 12:
                        motivos.append(f"{frase}: trecho longo demais ({fim - ini:.1f}s) em {titulo[:40]}")
                        continue
                    dst = SAIDA / voz / f"trecho_{len(feitos) + 1}.wav"
                    cortar(wav, ini, fim, dst, pedacos)
                    real = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                                 "csv=p=0", str(dst)], capture_output=True, text=True).stdout or 0)
                    if not 0.6 <= real <= 6.5:  # mede DEPOIS de tirar as pausas
                        dst.unlink(missing_ok=True)
                        motivos.append(f"{frase}: {real:.1f}s depois do corte em {titulo[:40]}")
                        continue
                    fim = ini + real
                    feitos.append({"arquivo": dst.name, "frase": texto, "alvo": frase, "nota": round(nota, 2),
                                   "ini": round(ini, 2), "fim": round(fim, 2), "url": url, "titulo": titulo, "busca": busca})
                    print(f"OK {voz}: '{frase}' -> {fim - ini:.1f}s ({nota:.2f}) {titulo[:50]}", flush=True)
                    break
                except Exception as e:  # noqa: BLE001
                    motivos.append(f"{frase}: erro {type(e).__name__}: {str(e)[:80]}")
        if feitos:
            for velho in (SAIDA / voz).glob("trecho_*.wav"):
                if velho.name not in {f["arquivo"] for f in feitos}:
                    velho.unlink()
            tj.write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
            rel[voz] = f"OK {len(feitos)} trecho(s)"
        else:
            rel[voz] = " | ".join(motivos)[:400] or "sem bordão no guia"
            print(f"-- {voz}: {rel[voz][:200]}", flush=True)
        rel_arq.write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FIM", sum(1 for v in rel.values() if v.startswith("OK")), "de", len(rel), flush=True)


if __name__ == "__main__":
    main()
