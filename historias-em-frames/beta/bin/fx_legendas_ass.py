"""fx_legendas_ass.py — legenda + barra de progresso + marca d'agua + palavras de impacto
num UNICO arquivo ASS, queimado numa passada so (estilo manhwa-react, mr/captions.py).

Antes: cada palavra virava um PNG (104 no video de teste) queimado em lotes de overlay,
mais um re-encode so da marca d'agua. Agora: 1 re-encode, palavra ativa com "pop", tempo
REAL de cada palavra (WordBoundary do edge-tts) e barra de progresso na cor do genero.

Flag: LEGENDA_ASS=1 (default). Se o ASS falhar, o pipeline volta pro caminho antigo (PNG).
Fontes: workspace/assets/fonts (junction -> hipercool-materiais/assets/fonts).
"""
import os
import re
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_DIR / "workspace" / "assets" / "fonts"

# palavras que "saltam" no meio da tela (igual keyword do react), alem dos numeros grandes
IMPACTO = {
    "nunca", "jamais", "impossivel", "impossível", "milhoes", "milhões", "bilhoes", "bilhões",
    "morte", "morreu", "segredo", "verdade", "traição", "traicao", "milagre", "chocante",
    "inacreditavel", "inacreditável", "socorro", "fogo", "sangue", "medo", "sozinho",
    "desapareceu", "sumiu", "venceu", "campeão", "campeao", "rico", "rica", "pobre", "fome",
    "mentira", "assassino", "fantasma", "maldição", "maldicao", "finalmente", "acabou",
}


# Cartoes de engajamento (como os HyperFrames do manhwa-react, mas em ASS: custo zero de
# render). Pergunta por genero no fim; "deixa o like" no meio.
PERGUNTAS = {
    "superacao": "VOCÊ TERIA DESISTIDO NO LUGAR DELE?",
    "motivacional": "QUAL FRASE TE MARCOU MAIS?",
    "terror": "VOCÊ TERIA CORAGEM DE FICAR?",
    "misterio": "QUAL É A SUA TEORIA?",
    "drama": "VOCÊ PERDOARIA?",
    "romance": "VOCÊ ACREDITA EM SEGUNDA CHANCE?",
    "comedia": "DE 0 A 10, QUANTO VOCÊ RIU?",
    "religioso": "VOCÊ ACREDITA EM MILAGRES?",
    "fantasia": "QUE PODER VOCÊ ESCOLHERIA?",
    "curiosidades": "VOCÊ JÁ SABIA DISSO?",
}


def ativo():
    return os.environ.get("LEGENDA_ASS", "1") == "1"


def _ts(t):
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def _esc(txt):
    return str(txt).replace("{", "(").replace("}", ")").replace("\\", "/").replace("\n", " ")


def ass_cor(hex_rgb, alpha="00"):
    """'#RRGGBB' -> '&HAABBGGRR' (formato ASS)."""
    h = (hex_rgb or "#FFD63C").lstrip("#")
    if len(h) != 6:
        h = "FFD63C"
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def _limpa(w):
    w = re.sub(r"^[\"'(\[«“]+|[\"')\]»”]+$", "", w.strip())
    return w.upper()


def _palavras_timeline(entries, offsets, word_times):
    """[(ini_abs, fim_abs, palavra)] no tempo do VIDEO FINAL.
    Usa o tempo real (word_times) quando bate o nº de palavras; senao reparte por tamanho."""
    out = []
    for i, (texto, dur) in enumerate(entries):
        words = (texto or "").split()
        if not words or i >= len(offsets):
            continue
        base = offsets[i]
        wt = word_times[i] if word_times and i < len(word_times) else None
        if wt and len(wt) == len(words):
            for (s, e, _w), w in zip(wt, words):
                out.append((base + float(s), base + float(e), w))
        else:
            dur = max(0.4, float(dur or 0))
            pesos = [max(2, len(w)) for w in words]
            tot = sum(pesos)
            acc = 0.0
            for w, p in zip(words, pesos):
                d = dur * p / tot
                out.append((base + acc, base + acc + d, w))
                acc += d
    return out


def _blocos(palavras, max_palavras=3, max_span=1.4, max_gap=0.6):
    blocos, cur = [], []
    for p in palavras:
        if cur:
            gap = p[0] - cur[-1][1]
            span = p[1] - cur[0][0]
            fim_frase = cur[-1][2].rstrip().endswith((".", "!", "?", ",", ";", ":"))
            if len(cur) >= max_palavras or gap > max_gap or span > max_span or fim_frase:
                blocos.append(cur)
                cur = []
        cur.append(p)
    if cur:
        blocos.append(cur)
    return blocos


def montar_ass(entries, offsets, word_times, duracao, W, H, cor_genero="#FFD63C",
               handle=None, impacto=True, barra=True, genero=None, cartoes=True, gancho=""):
    """Texto do arquivo ASS (PlayRes = W x H do video). gancho = frase grande no topo nos 1os ~3 s
    (o Short comeca direto na cena; padrao do hook do manhwa-react)."""
    esc = W / 720.0
    destaque = ass_cor("#FFD63C")          # palavra ativa: amarelo da legenda antiga
    acento = ass_cor(cor_genero)           # barra/impacto: cor do genero
    cap_y = int(H * 0.70)                  # acima da UI do Shorts (o fundo ~20% e coberto)
    styles = [
        f"Style: Cap,Montserrat Black,{int(56 * esc)},&H00FFFFFF,{destaque},&H00000000,&H90000000,"
        f"-1,0,0,0,100,100,1,0,1,{int(5 * esc)},{int(2 * esc)},5,30,30,0,1",
        f"Style: Key,Bangers,{int(118 * esc)},{acento},&H00FFFFFF,&H00000000,&H90000000,"
        f"0,0,0,0,100,100,3,0,1,{int(7 * esc)},{int(4 * esc)},5,40,40,0,1",
        f"Style: Mark,Montserrat ExtraBold,{int(24 * esc)},&H66FFFFFF,&H00FFFFFF,&H88000000,&H00000000,"
        f"-1,0,0,0,100,100,0,0,1,{max(1, int(2 * esc))},0,9,20,20,20,1",
        "Style: Bar,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        # BorderStyle=3: caixa opaca atras do texto na cor do "contorno" (pilula/cartao)
        f"Style: Pill,Montserrat Black,{int(28 * esc)},&H00120A08,&H00FFFFFF,{acento},&H64000000,"
        f"-1,0,0,0,100,100,1,0,3,{int(12 * esc)},{int(3 * esc)},5,20,20,0,1",
        f"Style: Card,Montserrat Black,{int(40 * esc)},&H00FFFFFF,&H00FFFFFF,&HD0120A08,&H64000000,"
        f"-1,0,0,0,100,100,1,0,3,{int(20 * esc)},{int(4 * esc)},5,50,50,0,1",
        f"Style: Hook,Bangers,{int(84 * esc)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,"
        f"0,0,0,0,100,100,2,0,1,{int(7 * esc)},{int(3 * esc)},8,40,40,0,1",
    ]
    ev = []
    palavras = _palavras_timeline(entries, offsets, word_times)
    blocos = _blocos(palavras)
    for bi, bloco in enumerate(blocos):
        toks = [_limpa(p[2]) for p in bloco]
        prox = blocos[bi + 1][0][0] if bi + 1 < len(blocos) else duracao
        for i, (ini, fim, _w) in enumerate(bloco):
            end = bloco[i + 1][0] if i + 1 < len(bloco) else min(fim + 0.25, prox, duracao)
            if end - ini < 0.05:
                end = ini + 0.05
            partes = []
            for j, tok in enumerate(toks):
                if not tok:
                    continue
                if j == i:
                    pop = "\\t(0,70,\\fscx114\\fscy114)\\t(70,150,\\fscx100\\fscy100)"
                    partes.append(f"{{\\c{destaque}{pop}}}{_esc(tok)}{{\\r}}")
                else:
                    partes.append(_esc(tok))
            txt = f"{{\\an5\\pos({W // 2},{cap_y})}}" + " ".join(partes)
            ev.append(f"Dialogue: 2,{_ts(ini)},{_ts(end)},Cap,,0,0,0,,{txt}")

    # palavras de impacto: saltam no meio da tela (max 4, intervalo >= 6s, nao no inicio)
    if impacto:
        ult, n = -99.0, 0
        for ini, _fim, w in palavras:
            tok = re.sub(r"[^\wÀ-ú]", "", w.lower())
            grande = tok.isdigit() and len(tok) >= 3
            if (tok in IMPACTO or grande) and ini - ult >= 6.0 and 2.0 < ini < duracao - 2.0:
                k = (f"{{\\an5\\pos({W // 2},{int(H * 0.42)})\\fscx0\\fscy0\\frz-4"
                     f"\\t(0,110,\\fscx120\\fscy120\\frz2)\\t(110,190,\\fscx100\\fscy100\\frz0)\\fad(0,160)}}")
                ev.append(f"Dialogue: 4,{_ts(ini)},{_ts(min(ini + 1.2, duracao))},Key,,0,0,0,,"
                          f"{k}{_esc(_limpa(w))}")
                ult, n = ini, n + 1
                if n >= 4:
                    break

    # cartoes de engajamento: "deixa o like" (~45%) e pergunta pra comentar (~72%),
    # longe do final (cartao de promo/outro ocupam os ultimos ~10s)
    if cartoes and duracao > 24:
        t_like = duracao * 0.45
        x_ok = W // 2
        ev.append(f"Dialogue: 5,{_ts(t_like)},{_ts(t_like + 2.6)},Pill,,0,0,0,,"
                  f"{{\\an5\\move({-W // 2},{int(H * 0.17)},{x_ok},{int(H * 0.17)},0,220)\\fad(0,250)}}"
                  f"CURTIU? DEIXA O LIKE")
        t_q = min(duracao * 0.72, duracao - 11.0)
        if t_q > t_like + 4:
            perg = PERGUNTAS.get((genero or "").lower(), "E VOCÊ, O QUE FARIA?")
            ev.append(f"Dialogue: 5,{_ts(t_q)},{_ts(t_q + 3.4)},Card,,0,0,0,,"
                      f"{{\\an5\\pos({W // 2},{int(H * 0.24)})\\fscx0\\fscy0"
                      f"\\t(0,160,\\fscx108\\fscy108)\\t(160,240,\\fscx100\\fscy100)\\fad(0,300)}}"
                      f"{_esc(perg)}\\N{{\\fs{int(26 * esc)}\\c{acento}}}COMENTA AQUI EMBAIXO")

    # barra de progresso (fundo escuro + barra que cresce no tempo)
    if barra and duracao > 1:
        h = max(4, int(6 * esc))
        rect = f"m 0 0 l {W} 0 l {W} {h} l 0 {h}"
        ev.append(f"Dialogue: 0,{_ts(0)},{_ts(duracao)},Bar,,0,0,0,,"
                  f"{{\\an7\\pos(0,{H - h})\\p1\\alpha&H99&\\c&H000000&}}{rect}{{\\p0}}")
        ev.append(f"Dialogue: 1,{_ts(0)},{_ts(duracao)},Bar,,0,0,0,,"
                  f"{{\\an7\\pos(0,{H - h})\\p1\\c{acento}\\fscx0\\t(0,{int(duracao * 1000)},\\fscx100)}}"
                  f"{rect}{{\\p0}}")
    if handle:
        ev.append(f"Dialogue: 1,{_ts(0)},{_ts(duracao)},Mark,,0,0,0,,{{\\an9\\pos({W - 18},18)}}{_esc(handle)}")
    if gancho:
        # WrapStyle 2 nao quebra linha sozinho: ate 3 linhas de ~16 letras, abaixo da faixa do @ (rede desfoca 5,5%)
        linhas, cur = [], ""
        for w in str(gancho).upper().split():
            if cur and len(cur) + 1 + len(w) > 16:
                linhas.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        linhas = (linhas + [cur])[:3] if cur else linhas[:3]
        ev.append(f"Dialogue: 3,{_ts(0)},{_ts(min(3.2, duracao))},Hook,,0,0,0,,"
                  f"{{\\an8\\pos({W // 2},{int(H * 0.11)})\\fad(0,300)}}" + "\\N".join(_esc(x) for x in linhas))

    head = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
            "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding",
            *styles, "", "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    return "\n".join(head + ev) + "\n", len(ev)


def _probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height:format=duration", "-of", "default=nw=1",
                        str(path)], capture_output=True, text=True, timeout=20)
    kv = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
    return int(kv["width"]), int(kv["height"]), float(kv["duration"])


def queimar(video_in, video_out, entries, offsets, word_times, cor_genero="#FFD63C",
            handle=None, tmp_dir=None, genero=None, gancho=""):
    """Gera o ASS e queima numa passada (audio copiado). Retorna (ok, n_eventos)."""
    try:
        W, H, dur = _probe(video_in)
    except Exception:
        return False, 0
    texto, n = montar_ass(entries, offsets, word_times, dur, W, H, cor_genero=cor_genero, handle=handle,
                          genero=genero, gancho=gancho)
    tmp = Path(tmp_dir or Path(video_out).parent)
    ass = tmp / "legendas.ass"
    ass.write_text(texto, encoding="utf-8")
    fonts = os.path.relpath(FONTS_DIR, tmp).replace("\\", "/")
    # cwd = pasta do .ass: caminho relativo, sem o "D:" que quebra o filtergraph
    cmd = ["ffmpeg", "-y", "-i", str(Path(video_in).resolve()),
           "-vf", f"ass=legendas.ass:fontsdir={fonts},format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "30",
           "-c:a", "copy", "-movflags", "+faststart", str(Path(video_out).resolve())]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900, cwd=str(tmp))
        ok = r.returncode == 0 and Path(video_out).exists() and Path(video_out).stat().st_size > 10000
        return ok, n
    except Exception:
        return False, n
