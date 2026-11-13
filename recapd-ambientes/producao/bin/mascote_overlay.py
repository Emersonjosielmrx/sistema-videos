"""mascote_overlay.py — sobrepõe a MASCOTE (garota-propaganda) reagindo à narração.

TAREFA 14. Assets prontos (14 MOVs ProRes 4444 alpha real, 1080x1920, 1.8s) em
workspace/assets/mascote_mov/. A garota sobe de baixo, faz "bob" e solta um balão de reação.

Mecânica = mesma das transições elementais: overlay ffmpeg do MOV alpha sobre o vídeo FINAL,
no timestamp do clip que casou, áudio=copy. Flag MASCOTE_OVERLAY=1 (default OFF).
Regras: só reage à narração do NARRADOR; parcimônia (máx 2-3/vídeo); não cobre legenda/watermark
(a animação já sobe do canto inferior). Anti-repetição de pose consecutiva.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
MOV_DIR = PROJECT_DIR / "workspace" / "assets" / "mascote_mov"

MAX_APARICOES = int(os.environ.get("MASCOTE_MAX", "5"))

# pose -> (arquivo MOV, keywords PT). Ordem = prioridade quando várias casam.
# Emoções fortes ANTES de wave/point (genéricos). wave só com saudação real de abertura
# ("história" foi removido — casava em narração descritiva e roubava o cry/love).
POSE_TABLE = [
    ("love",     "fx_mascot_love.mov",     ["apaixon", "coração", "coracao", "beij", "crush", "casal", "romântic", "romantic", " fofo", "que fofo"]),
    ("cry",      "fx_mascot_cry.mov",      ["chor", "lágrim", "lagrim", "triste", "sofr", "morre", "perdeu", "luto"]),
    ("shock",    "fx_mascot_shock.mov",    ["chocad", "não acredito", "nao acredito", "impossível", "impossivel", "de repente", "plot twist", "revelaç", "revelac"]),
    ("angry",    "fx_mascot_angry.mov",    ["raiva", "furioso", "irritad", "ódio", "odio", "bravo", "revolt", "injust"]),
    ("shy",      "fx_mascot_shy.mov",      ["vergonha", "envergonh", "corou", "tímid", "timid", "encabul", "constrang"]),
    ("cheer",    "fx_mascot_cheer.mov",    ["feliz", "consegui", "vitória", "vitoria", "ganhou", "comemor", "finalmente"]),
    ("popcorn",  "fx_mascot_popcorn.mov",  ["suspense", "aguarde", "expectativa", "vai acontecer", "tensão", "tensao", "clímax", "climax"]),
    ("laugh",    "fx_mascot_laugh.mov",    ["risada", "riu", "engraçad", "engracad", "hilári", "hilari", "cômic", "comic", "piada", "kkk"]),
    ("sleepy",   "fx_mascot_sleepy.mov",   ["cansad", "sono", "dormir", "tédio", "tedio", "entediad"]),
    ("think",    "fx_mascot_think.mov",    ["confus", "não entend", "nao entend", "será que", "sera que", "dúvida", "duvida", "misté", "miste", "enigm"]),
    ("wave",     "fx_mascot.mov",          ["oi pessoal", "olá pessoal", "ola pessoal", "bem-vindo", "bem vindo", "vamos começar", "vamos comecar", "fala galera", "e aí"]),
    ("point",    "fx_mascot_point.mov",    ["olha", "viu", "repare", "perceb", "presta atenção", "presta atencao"]),
]


def _ff():
    f = shutil.which("ffmpeg")
    if f:
        return f
    import glob as _g
    for pat in (str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/**/ffmpeg.exe"),
                "C:/Users/*/AppData/Local/Microsoft/WinGet/**/ffmpeg.exe"):
        h = _g.glob(pat, recursive=True)
        if h:
            return h[0]
    return "ffmpeg"


def _asset(mov):
    p = MOV_DIR / mov
    return str(p) if p.exists() else None


def _da_obra(arq):
    """True se o arquivo é asset da própria mascote (MOV_DIR/VIVO_DIR). Meme de terceiro (ex.: gato real dando joinha,
    8m6TEKqvxfY aos 33 s) vindo de outra pasta quebra a imersão e é descartado."""
    try:
        p = Path(arq).resolve()
    except (OSError, TypeError, ValueError):
        return False
    for d in (MOV_DIR, VIVO_DIR):
        try:
            p.relative_to(d.resolve())
            return True
        except (OSError, ValueError):
            continue
    return False


def _limpar_eventos(eventos):
    """13/11 (8m6TEKqvxfY: sticker travado 9 s atravessando q10-q12): descarta overlay fora da obra e corta o TTL na
    transição do painel quando o evento traz "fim_cena" (segundo absoluto do corte). Sem "fim_cena" = dur como antes."""
    ok = []
    for e in eventos or []:
        if not _da_obra(e.get("vivo") or e.get("file") or ""):
            continue
        fim = e.get("fim_cena")
        if fim is not None:
            dur = min(float(e["dur"]), float(fim) - float(e["t"]))
            if dur < 0.3:  # sobra quase nada antes do corte = não entra
                continue
            if dur < e["dur"]:
                e = {**e, "dur": dur}
        ok.append(e)
    return ok


# 28/10 dona ("ela tem que ter vida e movimento enquanto fala"): gravações do Veo 3 dela falando, já sem fundo
# (bench\mascote_recorte.py -> VP9 com alfa). Nas frases que ELA fala entra a gravação viva (sem o som do Veo: a voz
# é a clonada da narração), escolhida pelo assunto da frase; repete se a fala for maior que a gravação.
VIVO_DIR = PROJECT_DIR / "workspace" / "assets" / "mascote_viva"
_VIVO = [(re.compile(r"coment", re.I), "comenta"), (re.compile(r"valeu|próximo|proximo|tchau|até a próxima|beijo", re.I),
                                                    "tchau"), (re.compile(r"inscre|sininho|like|curt", re.I), "inscreva")]


def gravacao_viva(texto, k=0):
    if not VIVO_DIR.exists():
        return None
    tema = next((nome for rx, nome in _VIVO if rx.search(texto or "")), "inscreva")
    op = sorted(VIVO_DIR.glob(f"{tema}_andando_*.webm")) or sorted(VIVO_DIR.glob("*_andando_*.webm"))
    op = [p for p in op if not p.name.startswith(("amiga_", "reacao_"))]  # 29/10 dona: só ela andando (jaqueta nunca mais)
    op.sort(key=lambda p: any(o in p.name for o in ORIGINAIS))  # 30/10 dona: roupa original só por último
    return str(op[k % len(op)]) if op else None


# 29/10 noite (Fable; dona: "a mascote tem que ter vida"): as gravações de REAÇÃO dela andando (reacao_<tipo>_andando_*,
# mascote_producao) entram depois de uma fala forte da história, no lugar de metade dos memes em tela cheia.
_REACAO = {"choque": ("reacao_choque", "reacao_susto"), "raiva": ("reacao_raiva",),
           "deboche": ("reacao_riso",), "vergonha": ("reacao_riso",), "confusão": ("reacao_susto", "reacao_choque")}


def reacao_viva(emocao, usados=()):
    """(webm, fala, lado) de uma reação dela andando que combina com a emoção e ainda não foi usada no vídeo, ou None."""
    if not VIVO_DIR.exists() or emocao not in _REACAO:
        return None
    # 31/10: o glob "<tipo>_andando_*" achava só 2 das 9 reações deitadas (reacao_choque_andando_gueixa entra, as das
    # amigas também) — no 4wuf a mascote reagiu 1 vez em 18 memes. Agora: toda reação deitada com fala; ainda não usada
    # primeiro, a Maria antes das amigas; acabou = repete (dona 31/10: "a mascote deve aparecer mais").
    cands = [p for pref in _REACAO[emocao] for p in sorted(VIVO_DIR.glob(f"*{pref}*.webm"))
             if _sidecar(p).get("fala") and _paisagem(p)]
    # 02/11 dona ("as reações são sempre a mesma fala, ficou chato"): 1ª regra = FALA ainda não dita neste vídeo (antes
    # só o ARQUIVO não podia repetir — e as 4 roupas + 2 amigas gravaram a mesma frase). Sem fala nova = sem reação.
    ditas = {_sidecar(u).get("fala") for u in usados}
    cands = [p for p in cands if _sidecar(p).get("fala") not in ditas]
    if not cands:
        return None
    import random
    rnd = random.Random(len(usados) * 7919 + len(emocao))
    rnd.shuffle(cands)  # entre as falas novas, sorteia (antes sempre a mesma 1ª em ordem alfabética)
    p = min(cands, key=lambda p: (p.name.startswith("amiga_"), any(o in p.name for o in ORIGINAIS)))
    s = _sidecar(p)
    return str(p), s["fala"], s.get("lado")


# 30/10 dona: "a roupa original pode ter, mas só com os vídeos que já tem, e dar preferência pras outras" — o biquíni
# verde-amarelo comum vai por último em todas as escolhas (e a mascote_producao não grava mais nele)
ORIGINAIS = ("biquini_brasil", "biquini_praia")


def cena_viva(k=0):
    """30/10 dona: cena MUDA dela por cima do vídeo andando (passeio, apontando no canto, pendurada estilo Homem-Aranha,
    avião com faixa "deixa seu like"...) — gravações cena_<tipo>_* da mascote_producao; alterna os tipos. None = sem."""
    if not VIVO_DIR.exists():
        return None
    por_tipo = {}
    for p in sorted(VIVO_DIR.glob("cena_*.webm")):
        por_tipo.setdefault(p.name.split("_")[1], []).append(p)
    if not por_tipo:
        return None
    tipos = sorted(por_tipo)
    op = sorted(por_tipo[tipos[k % len(tipos)]], key=lambda p: any(o in p.name for o in ORIGINAIS))
    return str(op[(k // len(tipos)) % len(op)])


def amiga_viva(k=0, so_pedido=False):
    """As amigas (loira, indígena...) aparecem menos, no lado DIREITO, conversando com ela. so_pedido = só gravações
    de pedido (inscreva/comenta) — no CTA, a reação 'que raiva desse cara!' não combina."""
    op = sorted(VIVO_DIR.glob("amiga_*_andando_*.webm")) if VIVO_DIR.exists() else []
    if so_pedido:
        op = [p for p in op if "reacao" not in p.name] or op
    return str(op[k % len(op)]) if op else None


def _altura(webm, t=4.0):
    """Fração da altura do quadro que a personagem ocupa (alfa) no segundo t. 0 = não deu pra medir."""
    w, h = 160, 90
    try:
        r = subprocess.run([_ff(), "-v", "error", "-c:v", "libvpx-vp9", "-ss", f"{t:.2f}", "-i", str(webm),
                            "-frames:v", "1", "-vf", f"alphaextract,scale={w}:{h}", "-f", "rawvideo",
                            "-pix_fmt", "gray", "-"], capture_output=True, timeout=30)
        px = r.stdout
        linhas = [y for y in range(h) if len(px) == w * h and max(px[y * w:(y + 1) * w]) > 128]
        return (linhas[-1] - linhas[0] + 1) / h if linhas else 0.0
    except Exception:  # noqa: BLE001
        return 0.0


# 31/10 dona (Maria + amiga): as gravações terminam com a personagem no CENTRO do quadro (medido: x≈0,5 em todas),
# então as duas ficavam uma em cima da outra. No par, cada quadro é deslocado PAR_DESLOC da largura pro seu lado.
PAR_DESLOC = 0.22


def _escala_amiga(maria, amiga):
    """Quanto aumentar a amiga pra ficar do tamanho da Maria (amigas saem ~7% menores nas gravações)."""
    hm, ha = _altura(maria), _altura(amiga)
    return min(1.25, max(0.9, hm / ha)) if hm > 0 and ha > 0 else 1.0


def _anda_sempre(entrada, n, dur, total_webm):
    """Filtro da gravação com `dur` s sem CONGELAR: se a fala passa do fim da gravação, o último 1 s vai e volta
    (31/10 dona: 'ela fica parada'; antes era tpad=clone = último quadro parado). Saída sem rótulo final."""
    if dur <= total_webm - 0.05 or total_webm <= 1.2:
        return f"{entrada},trim=duration={dur:.3f},setpts=PTS-STARTPTS"
    # janela do meio (40-65%): ela já chegou e está falando parada; o fim das gravações do Veo tem close no rosto
    a, b = total_webm * 0.40, total_webm * 0.65
    quadros = int(round((b - a) * 30)) * 2
    return (f"{entrada},split[{n}a][{n}b];[{n}b]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS,split[{n}c][{n}d];"
            f"[{n}d]reverse[{n}r];[{n}r][{n}c]concat=n=2:v=1:a=0,loop=loop=-1:size={quadros}:start=0[{n}l];"
            f"[{n}a]trim=end={b:.3f},setpts=PTS-STARTPTS[{n}e];"
            f"[{n}e][{n}l]concat=n=2:v=1:a=0,trim=duration={dur:.3f},setpts=PTS-STARTPTS")


def _sidecar(webm):
    """{"fala": texto que ela fala no clipe, "lado": por onde entra} (mascote_producao grava; antigos à mão)."""
    import json
    try:
        return json.loads(Path(webm).with_suffix(".json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# 30/10: a fala da gravação tem que caber no MOMENTO do vídeo. No u7tN a abertura (1 min) dizia "Se você chegou até
# aqui, já é de casa!" e o fim dizia "qual foi a sua parte favorita até agora?" (o júri leu como fim cortado).
_FORA_DE_HORA = {
    "inicio": re.compile(r"chegou até aqui|até agora|até o fim|gostou da história|tchau|até a próxima|valeu por", re.I),
    "meio": re.compile(r"gostou da história|tchau|até a próxima|valeu por|amanhã tem mais", re.I),
    "fim": re.compile(r"até agora|antes de continuar|daqui pra frente|quem você acha que vai vencer", re.I),
}


def pausa_viva(texto, k=0, posicao=None, usados=()):
    """29/10 dona ("não ouvi a voz dela; tem que ficar em loop atrás e borrado na hora dela falar"): gravação com o
    TEXTO conhecido (sidecar) pro CTA virar uma pausa com a voz DELA. (webm, fala, lado) ou None.
    posicao ("inicio"/"meio"/"fim"): tira as gravações cuja fala não combina com aquele ponto do vídeo (sem nenhuma
    que combine = None, e o CTA sai com a voz clonada de antes). usados: gravações já postas neste vídeo vão por último."""
    if not VIVO_DIR.exists():
        return None
    tema = next((nome for rx, nome in _VIVO if rx.search(texto or "")), "inscreva")
    # 29/10 dona: "a mascote está usando aquela roupa que falei pra não usar mais — use apenas as novas, ela
    # caminhando": só "_andando_"; sem do tema, qualquer andando (a legenda é a fala do próprio clipe)
    # 29/10 noite (Fable): sem gravação do tema, o "qualquer andando" pegava REAÇÃO ("Ai, que raiva desse cara!") no
    # lugar do pedido de inscrição — o reserva agora é só gravação de pedido (inscreva/comenta)
    andando = [p for p in sorted(VIVO_DIR.glob("*_andando_*.webm")) if _sidecar(p).get("fala")
               and not p.name.startswith(("amiga_", "reacao_"))]
    andando.sort(key=lambda p: any(o in p.name for o in ORIGINAIS))  # 30/10 dona: roupa original só por último
    fora = _FORA_DE_HORA.get(posicao or "")
    if fora:
        andando = [p for p in andando if not fora.search(_sidecar(p).get("fala", ""))]
    ok = [p for p in andando if p.name.startswith(f"{tema}_")] or andando
    if not ok:
        return None
    novos = [p for p in ok if str(p) not in usados]
    p = novos[k % len(novos)] if novos else ok[k % len(ok)]
    s = _sidecar(p)
    return str(p), s["fala"], s.get("lado")


PAUSA_MAX_S = 4.0


def _fim_da_fala(audio, margem=0.3):
    """Segundo em que a ÚLTIMA palavra termina (silêncio do fim ignorado) + margem. 03/11 dona: "as reações da mascote
    são muito boas, só que 8 segundos é muito longo; parada é melhor porque a fala é mais curta — cortar o vídeo dela
    pra menos tempo / deixar ela falar e soltar o vídeo". A gravação tem entrada andando, fala, silêncio e saída: a pausa
    agora acaba logo depois da fala. Sem medida = a duração inteira (como antes)."""
    total = _probe_dur(audio)
    # 03/11: as gravações do Veo têm som até o fim (fala + ambiente), o silêncio quase nunca aparece — teto fixo
    # PAUSA_MAX_S (a dona: "deixar ela falar e depois de uns segundos soltar o vídeo e mutar ela"); a voz some em fade
    teto = float(os.environ.get("MASCOTE_PAUSA_MAX_S", PAUSA_MAX_S))
    total = min(total, teto) if teto > 0 else total
    try:
        r = subprocess.run([_ff(), "-hide_banner", "-nostats", "-i", str(audio), "-af",
                            "silencedetect=noise=-32dB:d=0.35", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception:  # noqa: BLE001
        return total
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    # silêncio que começa e não termina = cauda do arquivo: a fala acabou ali
    if len(ini) > len(fim) and ini[-1] > 0.5:
        return min(total, ini[-1] + margem)
    if ini and fim and fim[-1] >= total - 0.05 and ini[-1] > 0.5:
        return min(total, ini[-1] + margem)
    return total


def montar_pausa(fonte, t, webm, wav, out_mp4, w, h, k=0, lado=None, amiga=None):
    """Clipe da pausa: cena nítida com movimento/zoom contínuo (sem desfoque), e ela por cima falando (voz do Veo, já em `wav`).
    Paisagem: tela cheia, variando a cada uso (dona 29/10: "nem sempre no meio — da direita pra esquerda e ficar no
    canto e ao contrário; é só inverter o vídeo"): 0 como gravou, 1 espelhada, 2 parando no canto do lado por onde
    entrou, 3 espelhada + canto. Em pé (gravações antigas): no canto esquerdo, 65% da altura. True/False."""
    dur_m = _fim_da_fala(wav)  # 03/11: só até a última palavra (+0,3 s), não o arquivo inteiro (~8 s)
    if dur_m <= 0:
        return False
    pais = _paisagem(webm)
    amiga = amiga if (amiga and pais and _paisagem(amiga)) else None
    # 31/10 dona: a amiga fala DEPOIS da Maria (antes as duas falavam juntas e uma tampava a outra) — ela entra andando
    # no fim da fala da Maria e o trecho cresce até o fim da fala dela
    ta, dur_a = (max(0.4, dur_m - 0.5), _fim_da_fala(amiga)) if amiga else (0.0, 0.0)
    dur = max(dur_m, ta + dur_a) if amiga else dur_m
    # 30/10: o CTA do fim cai nos últimos segundos do original — faltava imagem, o tpad congelava o último quadro (júri
    # do u7tN: "painel totalmente estático" no fim). Recua o corte pra a cena andar o tempo todo da fala.
    src = _probe_dur(fonte)
    if src > dur + 1.5 and t + dur + 1.0 > src:
        t = max(0.0, src - dur - 1.0)
    flip = pais and k % 2 == 1
    canto = pais and k % 4 >= 2
    sinal = 1 if (lado or "direita") == "direita" else -1
    if flip:
        sinal = -sinal
    L = _probe_dur(webm)
    if pais and amiga:  # par: Maria entra pela esquerda e fica à esquerda; a amiga entra pela direita e fica à direita
        flip = (lado or "esquerda") == "direita"
        mv = _anda_sempre(f"[1:v]scale={w}:{h},fps=30,format=yuva420p{',hflip' if flip else ''}", "mm", dur, L) + "[mv]"
        x = -int(PAR_DESLOC * w)
    elif pais:
        mv = _anda_sempre(f"[1:v]scale={w}:{h},fps=30,format=yuva420p{',hflip' if flip else ''}", "mm", dur, L) + "[mv]"
        x = int(sinal * 0.28 * w) if canto else 0
    else:
        mv = f"[1:v]scale=-2:{int(h * 0.65) // 2 * 2},fps=30,format=yuva420p[mv]"
        x = int(w * 0.01)
    fc = (f"[0:v]fps=30,scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={dur:.3f},"
          f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[bg];{mv};"
          f"[bg][mv]overlay=x={x}:y=H-h:eof_action=repeat:shortest=0[pm]")
    extra = []
    audio_map = "2:a"
    if amiga:
        r = _escala_amiga(webm, amiga)
        aw, ah = int(w * r) // 2 * 2, int(h * r) // 2 * 2
        a_flip = ",hflip" if (_sidecar(amiga).get("lado") or "direita") == "esquerda" else ""
        ax = int(PAR_DESLOC * w) + (w - aw) // 2
        fc += (f";[3:v]scale={aw}:{ah},fps=30,format=yuva420p{a_flip},trim=duration={dur_a:.3f},"
               f"setpts=PTS-STARTPTS+{ta:.3f}/TB[am];"
               f"[pm][am]overlay=x={ax}:y=H-h:eof_action=pass:shortest=0[pm2];"
               f"[3:a]aresample=44100,atrim=duration={dur_a:.3f},adelay={int(ta * 1000)}:all=1[aa];"
               f"[2:a]aresample=44100,apad[ma];"
               f"[ma][aa]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,"
               f"atrim=duration={dur:.3f},afade=t=out:st={max(0.0, dur - 0.4):.3f}:d=0.4[aout]")
        audio_map = "[aout]"
        extra = ["-c:v", "libvpx-vp9", "-i", str(amiga)]
    else:  # 03/11: pausa cortada no teto (4 s) — a voz dela some em 0,4 s em vez de cortar no meio da palavra
        fc += f";[2:a]aresample=44100,atrim=duration={dur:.3f},afade=t=out:st={max(0.0, dur - 0.4):.3f}:d=0.4[aout]"
        audio_map = "[aout]"
    fc += f";[{'pm2' if amiga else 'pm'}]format=yuv420p[vout]"
    cmd = [_ff(), "-y", "-ss", f"{max(0.0, t):.2f}", "-t", f"{max(3.0, dur + 1.0):.3f}", "-i", str(fonte),
           "-c:v", "libvpx-vp9", "-i", str(webm),
           "-i", str(wav), *extra, "-filter_complex", fc, "-map", "[vout]", "-map", audio_map, "-c:v", "libx264",
           "-preset", "ultrafast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", str(out_mp4)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and Path(out_mp4).exists() and Path(out_mp4).stat().st_size > 10000
    except Exception:  # noqa: BLE001
        return False


def reacao_no_canto(clip, webm, out_mp4, w, h, k=0):
    """02/11 dona ("algumas curtas que possam ir sem parar o vídeo, que ela possa fazer do canto sem pegar a tela
    toda"): a reação CURTA (<= 2,5 s) entra POR CIMA do clipe da frase, num canto (35% da altura), sem pausa: a
    história continua com a narração e a fala dela soa por baixo (volume 0,8, narração 0,9). Canto alterna esquerda/
    direita (k). Sai em mp4 do mesmo tamanho/duração do clipe — quem chama troca o clipe por este. True/False."""
    dur_c, total = _probe_dur(clip), _probe_dur(webm)
    if dur_c < 2.0 or total <= 0:
        return False
    # as gravações do Veo têm 8 s (ela entra andando e depois fala): usa só o trecho DA FALA (1º som alto) + 0,3 s antes
    ini, dur_r = _trecho_da_fala(webm, total)
    dur_r = min(dur_r, dur_c - 0.2, 3.2)
    if dur_r < 0.8:
        return False
    t0 = max(0.0, min(dur_c - dur_r - 0.1, dur_c * 0.35))  # entra no 1º terço da frase e sai antes do fim
    # a gravação é a tela toda com ela num pedaço (1º teste: ficou minúscula no canto): recorta a caixa do corpo dela
    # (alfa) no meio do trecho da fala e escala a CAIXA pra 58% da altura do vídeo (45% ainda ficou miúda)
    cx, cy, cw, ch = _caixa_dela(webm, ini + dur_r / 2)
    alt = int(h * 0.58) // 2 * 2
    x = "W*0.01" if k % 2 == 0 else "W-w-W*0.01"
    flip = ",hflip" if k % 2 == 1 else ""  # do lado direito ela olha pro centro
    fc = (f"[1:v]trim=start={ini:.3f}:duration={dur_r:.3f},setpts=PTS-STARTPTS+{t0:.3f}/TB,"
          f"crop=iw*{cw:.3f}:ih*{ch:.3f}:iw*{cx:.3f}:ih*{cy:.3f},scale=-2:{alt},fps=30,"
          f"format=yuva420p{flip},fade=t=in:st={t0:.3f}:d=0.15:alpha=1,"
          f"fade=t=out:st={t0 + dur_r - 0.2:.3f}:d=0.2:alpha=1[mm];"
          f"[0:v][mm]overlay=x='{x}':y=H-h:eof_action=pass:shortest=0[v];"
          f"[1:a]atrim=start={ini:.3f}:duration={dur_r:.3f},asetpts=PTS-STARTPTS,aresample=44100,volume=0.8,"
          f"adelay={int(t0 * 1000)}:all=1,apad[ra];"
          f"[0:a]aresample=44100,volume=0.9[na];"
          f"[na][ra]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]")
    cmd = [_ff(), "-y", "-i", str(clip), "-c:v", "libvpx-vp9", "-i", str(webm), "-filter_complex", fc,
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "aac",
           "-b:a", "192k", "-t", f"{dur_c:.3f}", str(out_mp4)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and Path(out_mp4).exists() and Path(out_mp4).stat().st_size > 10000
    except Exception:  # noqa: BLE001
        return False


def _caixa_dela(webm, t):
    """(x, y, w, h) em fração do quadro: a caixa onde ela está (alfa > 128) no segundo t, com folga. Falhou = quadro todo."""
    w, h = 160, 90
    try:
        r = subprocess.run([_ff(), "-v", "error", "-c:v", "libvpx-vp9", "-ss", f"{t:.2f}", "-i", str(webm),
                            "-frames:v", "1", "-vf", f"alphaextract,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray",
                            "-"], capture_output=True, timeout=30)
        px = r.stdout
        if len(px) != w * h:
            return 0.0, 0.0, 1.0, 1.0
        ys = [y for y in range(h) if max(px[y * w:(y + 1) * w]) > 128]
        xs = [x for x in range(w) if max(px[y * w + x] for y in range(h)) > 128]
        if not ys or not xs:
            return 0.0, 0.0, 1.0, 1.0
        x0, x1 = max(0, xs[0] - 6), min(w, xs[-1] + 7)
        y0 = max(0, ys[0] - 3)
        return x0 / w, y0 / h, (x1 - x0) / w, (h - y0) / h  # até o pé da tela (ela fica apoiada embaixo)
    except Exception:  # noqa: BLE001
        return 0.0, 0.0, 1.0, 1.0


def _trecho_da_fala(webm, total):
    """(início, duração) da fala dentro da gravação: do 1º som acima de -32 dB (menos 0,3 s) até o último + 0,2 s."""
    try:
        r = subprocess.run([_ff(), "-hide_banner", "-c:v", "libvpx-vp9", "-i", str(webm), "-af",
                            "silencedetect=n=-32dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True,
                           timeout=60)
        ss = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
        se = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    except Exception:  # noqa: BLE001
        ss, se = [], []
    # som começa onde o 1º silêncio acaba (se o arquivo começa em silêncio) e termina no último silêncio que dura até o fim
    comeco = se[0] if ss and ss[0] < 0.05 and se else 0.0
    fim = ss[-1] if ss and ss[-1] > comeco + 0.5 and (not se or ss[-1] > se[-1]) else total
    # 02/11 teste: nas gravações do Veo o som (passos/ambiente) quase nunca tem silêncio no começo e o "início da fala"
    # caía em 0 s — ela ainda entrando pela borda (no canto saiu cortada). Sem início claro: a fala começa depois que
    # ela chegou (~40% da gravação, medido nas 8 s do Veo)
    if comeco < total * 0.25:
        comeco = total * 0.40
        fim = min(fim, total - 0.2)
    ini = max(0.0, comeco - 0.3)
    return ini, max(0.0, min(total, fim + 0.2) - ini)


def dupla_viva(emocao, usados=()):
    """02/11 dona ("a amiga foi feita pra interagir com a outra, comentando, e não aparecer falando a mesma coisa"):
    conversa gravada (mascote_producao.DUPLAS): Maria (dupla_N_a) fala e a amiga (…_dupla_N_b) RESPONDE outra coisa.
    -> (webm_maria, webm_amiga) de uma dupla da emoção ainda não usada no vídeo, ou None."""
    if not VIVO_DIR.exists():
        return None
    for a in sorted(VIVO_DIR.glob("dupla_*_a_andando_*.webm")):
        s = _sidecar(a)
        if s.get("emocao") != emocao or str(a) in usados:
            continue
        n = s.get("dupla", "")[5:]
        b = sorted(VIVO_DIR.glob(f"amiga_*_andando_dupla_{n}_b_*.webm"))
        if b and _paisagem(a) and _paisagem(b[0]):
            return str(a), str(b[0])
    return None


def _paisagem(arq):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0:s=x", str(arq)], capture_output=True, text=True, timeout=15)
        w, h = (int(x) for x in r.stdout.strip().split("x"))
        return w > h
    except Exception:  # noqa: BLE001
        return False


# Fallback: clima (mood) → pose, quando nenhuma keyword específica casa. Isso faz a
# mascote VARIAR as poses (antes quase sempre caía na mesma, pois as keywords são raras).
_MOOD_POSE = {
    "romantic_sexy": "love", "romantic": "love",
    "sad_emotional": "cry", "sad": "cry", "emotional": "cry",
    "tense_dramatic": "popcorn", "tense": "popcorn", "suspense": "popcorn",
    "funny_lighthearted": "laugh", "funny": "laugh", "comedic": "laugh",
    "epic_action": "cheer", "action": "cheer", "epic": "cheer",
    "calm_chill": "think", "neutral_chill": "think", "chill": "think",
}


def pick_pose(text, mood=None):
    """Retorna nome da pose (ou None) pela narração. Keyword específica tem prioridade;
    senão, cai pro mood (variedade). point por último (genérico)."""
    t = (text or "").lower()
    if not t.strip():
        return None
    for pose, _mov, kws in POSE_TABLE:
        for k in kws:
            if k in t:
                return pose
    # fallback por mood — amplia a variedade de poses
    if mood is None:
        try:
            import effects_engine as _fx
            mood = _fx.detect_mood_from_text(text)
        except Exception:
            mood = None
    if mood:
        return _MOOD_POSE.get(mood)
    return None


def pick_eventos(clip_texts, clip_personas, abs_starts, sensual=None):
    """Decide quando a mascote aparece. SÓ narrador, anti-repetição, máx MAX_APARICOES.
    Pula painéis +18 (sensual) — não sobrepor mascote em cena que vai ser censurada.
    Retorna lista de {t, pose, file, dur}."""
    # 01/11 dona: "a mascote antiga — delete ela de tudo e troque pela nova": as animações MOV (chibi) não entram
    # mais; a mascote nova entra pelas gravações vivas (reacao_viva/pausa_viva/cortes_mascote)
    if os.environ.get("MASCOTE_ANTIGA") != "1":
        return []
    eventos = []
    last_pose = None
    _sens = set(sensual or [])
    pose_mov = {p: m for p, m, _ in POSE_TABLE}
    n = min(len(clip_texts), len(abs_starts))
    for i in range(n):
        if len(eventos) >= MAX_APARICOES:
            break
        if i in _sens:
            continue  # painel +18 → sem mascote
        persona = (clip_personas[i] if i < len(clip_personas) else "") or ""
        pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona).strip().lower()
        if pclean not in ("narrador", "narradora"):
            continue
        pose = pick_pose(clip_texts[i])
        if pose is None or pose == last_pose:
            continue
        mov = _asset(pose_mov.get(pose, ""))
        if not mov:
            continue
        dur = _probe_dur(mov)
        ev = {"t": abs_starts[i] + 0.1, "pose": pose, "file": mov, "dur": dur}
        if i + 1 < len(abs_starts):
            ev["fim_cena"] = abs_starts[i + 1]  # TTL acaba no corte pro próximo painel
        eventos.append(ev)
        last_pose = pose
    return eventos


def _probe_dur(f):
    try:
        fp = shutil.which("ffprobe") or _ff().replace("ffmpeg", "ffprobe")
        r = subprocess.run([fp, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(f)], capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 1.8


def overlay_mascote(base_mp4, out_mp4, eventos):
    """Sobrepõe os MOVs alpha da mascote no vídeo. Áudio=copy. Retorna True/False."""
    base_mp4, out_mp4 = Path(base_mp4), Path(out_mp4)
    eventos = _limpar_eventos(eventos)
    if not eventos:
        return False
    try:
        fp = shutil.which("ffprobe") or _ff().replace("ffmpeg", "ffprobe")
        r = subprocess.run([fp, "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(base_mp4)],
                           capture_output=True, text=True, timeout=15)
        bw, bh = (int(x) for x in r.stdout.strip().split("x"))
    except Exception:
        return False
    inputs = ["-i", str(base_mp4)]
    for e in eventos:
        inputs += ["-i", str(e["file"])]
    fc = []
    last = "[0:v]"
    for idx, e in enumerate(eventos, start=1):
        t0 = e["t"]
        t1 = t0 + e["dur"]
        fc.append(f"[{idx}:v]scale={bw}:{bh}:flags=bicubic,setpts=PTS-STARTPTS+{t0:.3f}/TB[mv{idx}]")
        out = f"[m{idx}]"
        fc.append(f"{last}[mv{idx}]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})'{out}")
        last = out
    cmd = [_ff(), "-y", *inputs, "-filter_complex", ";".join(fc),
           "-map", last, "-map", "0:a?",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
           "-c:a", "copy", str(out_mp4)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        return r.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 0
    except Exception:
        return False


# ─── recap LONGO deitado (26/10, prompt LONGOS base item 2: "CTA meio + mascote") ─────────────────────────────────
# Os MOVs são verticais 1080x1920 com a garota no canto inferior esquerdo (alfa em x 8–74%, y 58–100%). No 16:9 não
# dá pra esticar o quadro inteiro (o overlay_mascote de cima escala pro tamanho do vídeo): recorta só a região dela e
# põe no canto inferior esquerdo, com ~42% da altura do vídeo.
_RECORTE = (0.08, 0.58, 0.74, 1.0)  # x0, y0, x1, y1 (fração do quadro do MOV)


def eventos_deitado(momentos, maximo=8):
    """momentos = [(t, texto)] -> [{t, pose, file, dur}] sem repetir pose seguida (pose pelo texto; senão rodízio)."""
    pose_mov = {p: m for p, m, _ in POSE_TABLE}
    rodizio = ["point", "cheer", "shock", "popcorn", "laugh", "think"]
    eventos, ultima = [], None
    for k, (t, texto) in enumerate(momentos[:maximo]):
        pose = pick_pose(texto or "")
        if pose is None or pose == ultima:
            pose = next(p for p in rodizio[k % len(rodizio):] + rodizio if p != ultima)
        mov = _asset(pose_mov.get(pose, ""))
        if not mov:
            continue
        d = _probe_dur(mov)
        eventos.append({"t": float(t), "pose": pose, "file": mov, "dur": d, "mov_dur": d})
        ultima = pose
    return eventos


def filtro_mascote_deitado(eventos, bw, bh, entrada_base, primeiro_idx):
    """02/11 (dona: "aproveitar as GPUs / produção"): o mesmo overlay do overlay_mascote_deitado, mas como PEDAÇO de
    filter_complex pra entrar na passada da legenda (que já regrava o vídeo) — tira 1 regravação inteira do longo.
    -> (inputs extras, filtros, rótulo final) ou None se algum evento não é gravação viva (os MOV antigos ficam no
    caminho antigo). Índices de entrada começam em primeiro_idx."""
    if eventos and any(not e.get("vivo") for e in eventos):
        return None
    eventos = _limpar_eventos(eventos)
    if not eventos:
        return None
    inputs, fc, last = [], [], entrada_base
    for n, e in enumerate(eventos):
        idx = primeiro_idx + n
        t0, t1 = e["t"], e["t"] + e["dur"]
        pais = _paisagem(e["vivo"])
        inputs += ([] if pais else ["-stream_loop", "-1"]) + ["-c:v", "libvpx-vp9", "-i", str(e["vivo"])]
        tam = f"{bw}:{bh}" if pais else f"-2:{int(bh * 0.65) // 2 * 2}"
        if pais:
            fc.append(_anda_sempre(f"[{idx}:v]scale={tam},fps=30,format=yuva420p", f"mv{idx}", e["dur"],
                                   _probe_dur(e["vivo"])) + f",setpts=PTS-STARTPTS+{t0:.3f}/TB[mvv{idx}]")
        else:
            fc.append(f"[{idx}:v]scale={tam},fps=30,format=yuva420p,trim=duration={e['dur']:.3f},"
                      f"setpts=PTS-STARTPTS+{t0:.3f}/TB[mvv{idx}]")
        px = "0" if pais else (f"W-w-{int(bw * 0.01)}" if e.get("lado") == "direita" else f"{int(bw * 0.01)}")
        fc.append(f"{last}[mvv{idx}]overlay=x={px}:y=H-h:eof_action=pass:"
                  f"enable='between(t,{t0:.3f},{t1:.3f})'[mm{idx}]")
        last = f"[mm{idx}]"
    return inputs, fc, last


def overlay_mascote_deitado(base_mp4, out_mp4, eventos):
    """Garota-mascote no canto inferior esquerdo do vídeo 16:9 nos momentos dados. Áudio copiado. True/False."""
    base_mp4, out_mp4 = Path(base_mp4), Path(out_mp4)
    eventos = _limpar_eventos(eventos)
    if not eventos:
        return False
    try:
        fp = shutil.which("ffprobe") or _ff().replace("ffmpeg", "ffprobe")
        r = subprocess.run([fp, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0:s=x", str(base_mp4)], capture_output=True, text=True, timeout=15)
        bw, bh = (int(x) for x in r.stdout.strip().split("x"))
    except Exception:
        return False
    x0, y0, x1, y1 = _RECORTE
    alt = int(bh * 0.42) // 2 * 2
    inputs, fc, last = ["-i", str(base_mp4)], [], "[0:v]"
    for idx, e in enumerate(eventos, start=1):
        t0, t1 = e["t"], e["t"] + e["dur"]
        if e.get("vivo"):
            pais = _paisagem(e["vivo"])
            # paisagem (ela entrando andando): toca 1x em tela cheia sem repetir a entrada; 31/10 dona ("ela fica
            # parada"): se a fala passa do fim da gravação, o último 1 s vai e volta em vez do último quadro parado
            inputs += ([] if pais else ["-stream_loop", "-1"]) + ["-c:v", "libvpx-vp9", "-i", str(e["vivo"])]
            tam = f"{bw}:{bh}" if pais else f"-2:{int(bh * 0.65) // 2 * 2}"
            if pais:
                fc.append(_anda_sempre(f"[{idx}:v]scale={tam},fps=30,format=yuva420p", f"v{idx}", e["dur"],
                                       _probe_dur(e["vivo"])) + f",setpts=PTS-STARTPTS+{t0:.3f}/TB[mv{idx}]")
            else:
                fc.append(f"[{idx}:v]scale={tam},fps=30,format=yuva420p,trim=duration={e['dur']:.3f},"
                          f"setpts=PTS-STARTPTS+{t0:.3f}/TB[mv{idx}]")
            px = "0" if pais else (f"W-w-{int(bw * 0.01)}" if e.get("lado") == "direita" else f"{int(bw * 0.01)}")
            fc.append(f"{last}[mv{idx}]overlay=x={px}:y=H-h:eof_action=pass:"
                      f"enable='between(t,{t0:.3f},{t1:.3f})'[m{idx}]")
            last = f"[m{idx}]"
            continue
        inputs += ["-i", str(e["file"])]
        # 28/10 mascote falando: evento maior que a animação = segura o quadro em que ela está inteira (1,33 s; os MOVs
        # entram até ~0,6 s e somem depois de 1,47 s — o último quadro é ela transparente) até o fim da fala e só
        # então toca a saída
        extra = max(0.0, e["dur"] - float(e.get("mov_dur") or e["dur"]))
        base = f"[{idx}:v]crop=iw*{x1 - x0}:ih*{y1 - y0}:iw*{x0}:ih*{y0},scale=-2:{alt},fps=30"
        if extra > 0.05:
            h, n = 1.33, max(1, round(extra * 30))
            fc.append(f"{base},split=3[ma{idx}][mb{idx}][mc{idx}];"
                      f"[ma{idx}]trim=end={h},setpts=PTS-STARTPTS[pa{idx}];"
                      f"[mb{idx}]trim=start={h}:end={h + 0.034},setpts=PTS-STARTPTS,loop=loop={n}:size=1:start=0,"
                      f"setpts=N/30/TB[pb{idx}];"
                      f"[mc{idx}]trim=start={h},setpts=PTS-STARTPTS[pc{idx}];"
                      f"[pa{idx}][pb{idx}][pc{idx}]concat=n=3:v=1:a=0,setpts=PTS-STARTPTS+{t0:.3f}/TB[mv{idx}]")
        else:
            fc.append(f"{base},setpts=PTS-STARTPTS+{t0:.3f}/TB[mv{idx}]")
        fc.append(f"{last}[mv{idx}]overlay=x={int(bw * 0.015)}:y=H-h-{int(bh * 0.01)}:"
                  f"enable='between(t,{t0:.3f},{t1:.3f})'[m{idx}]")
        last = f"[m{idx}]"
    cmd = [_ff(), "-y", *inputs, "-filter_complex", ";".join(fc), "-map", last, "-map", "0:a?",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "veryfast", "-c:a", "copy",
           str(out_mp4)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=max(900, int(_probe_dur(base_mp4) * 1.5)))
        return r.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 0
    except Exception:
        return False
