"""anime_gancho.py — gancho na tela (1os ~3 s) + barra de progresso do recap de anime.

Adaptado do historias-em-frames bin/fx_legendas_ass.py (estilos Hook + Bar, 16/10), padrão do hipercool/react:
o vídeo já abre com a frase que prende escrita no topo e uma barra fina embaixo mostra quanto falta.

  gerar_gancho(textos)          frase de 3-6 palavras pelo LLM (sem nome do anime/personagem); "" se falhar.
  extras(gancho)                 fn(vw, vh, dur) -> (estilos, eventos) pro fx_subtitles.burn_subtitles_ass (vídeo longo,
                                 mesma passada da legenda).
  queimar(video_in, out, gancho) passada própria só com gancho + barra (Short: a legenda dele é PNG).
"""
import logging
import os
import re
import subprocess
from pathlib import Path

AMARELO = "&H003CD6FF"   # #FFD63C em BGR (a mesma cor da palavra ativa da legenda)


# 28/10: 11 de 49 Shorts do dia com gancho lixo no topo: "[EMPTY RESPONSE]", "LANGUAGE:", "PORTUGUESE (",
# "EXPERIMENTING", "WINDOW", "MAKES A" (o modelo "pensando" em inglês e a 1ª linha virando gancho; 1 palavra passava
# pela regra do tailandês). Agora: procura a 1ª linha que serve; meta/inglês/1 palavra latina = descarta.
_INGLES = {"THE", "IS", "ARE", "MAKES", "OF", "AND", "TO", "IN", "YOU", "WITH", "THIS", "THAT", "HIS", "HER", "WAS",
           "LANGUAGE", "PORTUGUESE", "BRAZILIAN", "HOOK", "TITLE", "HERE", "OUTPUT", "RESPONSE", "EMPTY", "SURE",
           "EXPERIMENTING", "WINDOW", "OKAY", "LET", "WHAT", "WHEN", "HE", "SHE", "IT", "FOR", "ON", "MY"}


def _frase_valida(linha, minimo, maximo):
    """Linha da IA -> frase em MAIÚSCULAS ou "" (meta, aviso, inglês numa saída em pt, tamanho errado)."""
    txt = re.sub(r"[\"“”*#]", "", str(linha)).strip()
    if not txt or re.search(r"[:\[\]()<>{}|=_/\\]", txt):
        return ""
    palavras = txt.upper().split()
    latino = bool(re.search(r"[A-Za-zÀ-ÿ]", txt))
    if len(palavras) == 1:  # tailandês/japonês não separam palavras; latino com 1 palavra = lixo
        return palavras[0] if not latino and 3 <= len(palavras[0]) <= 45 else ""
    if not minimo <= len(palavras) <= maximo:
        return ""
    lingua = (os.environ.get("ANIME_LANG_NOME") or "português").lower()
    if "portugu" in lingua or "espanhol" in lingua:
        if sum(p.strip(".,!?") in _INGLES for p in palavras) >= 1 and not any(
                p in ("ELE", "ELA", "SEU", "SUA", "DE", "DO", "DA", "QUE", "O", "UM", "UMA") for p in palavras):
            return ""
    return " ".join(palavras)


def _primeira_valida(txt, minimo, maximo):
    for linha in str(txt or "").splitlines()[:6]:
        ok = _frase_valida(linha, minimo, maximo)
        if ok:
            return ok
    return ""


def gerar_gancho(textos, timeout_tokens=40):
    """Gancho curto pelo começo da narração. Nunca o nome da obra/personagem (regra do dono, 15/10)."""
    trecho = " ".join(t for t in textos[:12] if t)[:1200]
    if not trecho:
        return ""
    lingua = os.environ.get("ANIME_LANG_NOME") or "português do Brasil"  # versões em outra língua (anime_idiomas)
    prompt = (f"Abaixo está o começo da narração de um recap. Escreva UM gancho em {lingua}, "
              "de 3 a 6 palavras, em MAIÚSCULAS, que faça quem está rolando o feed parar e continuar assistindo "
              "(promessa, mistério ou choque do que vai acontecer). A frase precisa fazer sentido sozinha pra quem "
              "não conhece a história. Exemplos do tom: 'ELE ERA O MAIS FRACO ATÉ HOJE', 'O PODER QUE ELE "
              "ESCONDIA', 'ELA ESCONDIA ISSO DE TODOS' — use o fato DESTA história, não copie os exemplos e não "
              "comece com 'NINGUÉM ESPERAVA'. NUNCA escreva o nome do anime nem de personagens. "
              "Sem aspas, sem emoji, sem ponto final. Responda só a frase.\n\nNARRAÇÃO:\n" + trecho)
    if os.environ.get("CORTES_NINGUEM_ESPERAVA") == "A":
        # 30/10 variante T11 (bin\variantes.py): A = prompt de antes de 30/10 (exemplo 'NINGUÉM ESPERAVA ESSE PODER',
        # sem proibição); B (ou sem env) = o de cima, que proíbe essa abertura
        prompt = (f"Abaixo está o começo da narração de um recap. Escreva UM gancho em {lingua}, "
                  "de 3 a 6 palavras, em MAIÚSCULAS, que faça quem está rolando o feed parar e continuar assistindo "
                  "(promessa, mistério ou choque do que vai acontecer). A frase precisa fazer sentido sozinha pra quem "
                  "não conhece a história. Exemplos do tom: 'ELE ERA O MAIS FRACO ATÉ HOJE', 'NINGUÉM ESPERAVA ESSE "
                  "PODER', 'ELA ESCONDIA ISSO DE TODOS'. NUNCA escreva o nome do anime nem de personagens. "
                  "Sem aspas, sem emoji, sem ponto final. Responda só a frase.\n\nNARRAÇÃO:\n" + trecho)
    # 28/10: 40 tokens (timeout_tokens) com o Argon "pensando" = pedaço do raciocínio em inglês ou [EMPTY RESPONSE]
    # -> folga de 600 e 2 tentativas antes de sair sem gancho
    for tentativa in range(2):
        try:
            import claude_client
            txt = claude_client.generate_text(prompt, max_tokens=max(timeout_tokens, 600), temperature=0.7,
                                              video=True) or ""
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[gancho] LLM falhou ({type(e).__name__}) — sem gancho")
            return ""
        # nunca cortar no meio ("ELE NÃO SABIA O QUE VINHA A", 16/10): longa demais = sem gancho
        ok = _primeira_valida(txt, 2, 8)
        if ok:
            return ok
        logging.warning(f"[gancho] resposta descartada ({tentativa + 1}ª): {str(txt)[:60]!r}")
    return ""


def gerar_titulo_tarja(titulo_original, narracao=""):
    """Título da TARJA BRANCA do parceiro (dono 17/10: "um título extremamente chamativo, tipo 'essa garota fez
    isso', 'ele era o único que...', como os títulos tendenciosos do hipercool"). 4 a 9 palavras, sem nome de obra
    nem de personagem. Vazio se o LLM falhar (aí fica o estilo antigo)."""
    lingua = os.environ.get("ANIME_LANG_NOME") or "português do Brasil"
    prompt = (f"Escreva UM título em {lingua} para uma tarja que fica no vídeo inteiro de um Short de resumo. "
              "Tem que ser EXTREMAMENTE chamativo e tendencioso, curiosidade/choque, de 4 a 9 palavras. Modelos do "
              "tom: 'ESSA GAROTA FEZ O QUE NINGUÉM TEVE CORAGEM', 'ELE ERA O ÚNICO QUE PODIA VER ISSO', 'ELA "
              "ESCONDEU ISSO DE TODO MUNDO POR ANOS', 'NINGUÉM ACREDITOU NO QUE ELE FEZ'. NUNCA nome da obra nem de "
              "personagem. Português CORRETO (ortografia e concordância; nada de palavra inventada nem palavras grudadas). "
              "Sem aspas, sem emoji, sem hashtag. Responda só o título.\n\n"
              f"TÍTULO ORIGINAL (outra língua): {titulo_original}\nCOMEÇO DA HISTÓRIA: {narracao[:700]}")
    try:
        import claude_client
        txt = claude_client.generate_text(prompt, max_tokens=600, temperature=0.8, video=True) or ""  # 28/10: era 50
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[tarja] LLM falhou ({type(e).__name__})")
        return ""
    return _primeira_valida(txt, 3, 10)


def _ts(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _linhas(gancho, retrato):
    """WrapStyle 2 não quebra sozinho: até 3 linhas de 16 letras no retrato; no deitado 2 linhas de 34 (27/10: com 3
    linhas de 26 o gancho ocupava ~35% da altura no centro e cobria o rosto — júri e sessão Claude)."""
    max_c, max_l = (16, 3) if retrato else (34, 2)
    linhas, cur = [], ""
    for w in gancho.split():
        if cur and len(cur) + 1 + len(w) > max_c:
            linhas.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return (linhas + [cur])[:max_l] if cur else linhas[:max_l]


def cor_da_cena(video, t=1.5):
    """01/11 dona (referência sPyd8I220GI: letra verde na cena verde, azul na azul): a cor dominante da cena, viva e
    clara, em &H00BBGGRR do ASS. Sem cor dominante (cena cinza) ou erro = amarelo da legenda."""
    try:
        import colorsys
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf",
                              "scale=64:36,format=rgb24", "-f", "rawvideo", "-"], capture_output=True, timeout=60).stdout
        hist = [0.0] * 12
        for i in range(0, len(raw) - 2, 3):
            h, s, v = colorsys.rgb_to_hsv(raw[i] / 255, raw[i + 1] / 255, raw[i + 2] / 255)
            if s > 0.25 and v > 0.2:
                hist[int(h * 12) % 12] += s * v
        if max(hist) <= 0:
            return AMARELO
        r, g, b = (int(c * 255) for c in colorsys.hsv_to_rgb((hist.index(max(hist)) + 0.5) / 12, 0.85, 1.0))
        return f"&H00{b:02X}{g:02X}{r:02X}"
    except Exception:  # noqa: BLE001
        return AMARELO


# 01/11 dona ("palavra por palavra, no máximo duas, cada uma com uma cor, fonte e tamanho diferente, e um efeito
# como o do choque, água ou fogo só nela, na aparição e no desaparecimento"). Fontes da pasta assets/fonts (fontsdir).
FONTES_ABRE = ("Impact", "Bangers", "Luckiest Guy", "Montserrat Black")
CORES_ABRE = ("&H0000FFFF", "&H00FFFFFF", "&H002020FF", "&H00FFFF00", "&H00008CFF", "&H00FF40FF", "&H007FFF00")
TAMANHOS_ABRE = (1.0, 1.3, 0.95, 1.15, 1.4)
ESCALA_FONTE = {"Bangers": 1.3, "Montserrat Black": 0.85}  # tamanho visual parelho (a Bangers sai pequena)
# elemento: (cor do brilho em volta, entrada, saída) — {d} = duração do trecho em ms
ELEMENTOS_ABRE = {
    "choque": ("&H00FFF0A0",  # azul elétrico: pisca como curto-circuito e treme
               "\\alpha&HFF&\\t(0,40,\\alpha&H00&)\\t(40,80,\\alpha&HB0&)\\t(80,120,\\alpha&H00&)"
               "\\t(120,150,\\alpha&H60&)\\t(150,180,\\alpha&H00&)",
               "\\t({d1},{d2},\\alpha&HB0&)\\t({d2},{d3},\\alpha&H00&)\\t({d3},{d},\\alpha&HFF&\\fscx130\\fscy70)"),
    "fogo": ("&H000060FF",  # laranja: sobe queimando e some subindo em chama
             "\\fscy40\\alpha&H80&\\t(0,180,\\fscy112\\alpha&H00&)\\t(180,260,\\fscy100)",
             "\\t({d2},{d},\\fscy170\\fscx85\\alpha&HFF&\\blur14)"),
    "agua": ("&H00FF9C30",  # azul água: gira entrando como onda e se desfaz em ondulação
             "\\frx85\\blur12\\alpha&H60&\\t(0,260,\\frx0\\blur0\\alpha&H00&)",
             "\\t({d2},{d},\\frx-80\\fscx120\\blur16\\alpha&HFF&)"),
}


# lugares (fração da tela) por onde os cartões da abertura passeiam — nunca a faixa de baixo da legenda normal
POS_DEITADO = ((0.50, 0.26), (0.26, 0.30), (0.74, 0.34), (0.30, 0.56), (0.70, 0.58), (0.50, 0.46), (0.22, 0.44),
               (0.78, 0.24))
POS_RETRATO = ((0.50, 0.28), (0.50, 0.50), (0.36, 0.38), (0.64, 0.42), (0.50, 0.60), (0.44, 0.22))
GIROS = (-6, 4, -3, 7, 0, -5, 3)


# palavras que ganham decoração visual — ícone Unicode simples acima da palavra
DECORACAO = {
    "bruxa": "\U0001f9d9", "bruxo": "\U0001f9d9", "feiticeira": "\U0001f9d9", "mago": "\U0001f9d9",
    "magia": "\u2728", "mágico": "\u2728",
    "prisioneiro": "\u26d3", "preso": "\u26d3", "correntes": "\u26d3", "presa": "\u26d3",
    "rei": "\U0001f451", "rainha": "\U0001f451", "imperador": "\U0001f451", "coroa": "\U0001f451",
    "morte": "\U0001f480", "morreu": "\U0001f480", "morto": "\U0001f480", "morta": "\U0001f480", "matou": "\U0001f480",
    "amor": "\u2764", "amou": "\u2764", "apaixonou": "\u2764", "apaixonada": "\u2764",
    "fogo": "\U0001f525", "queimou": "\U0001f525", "chamas": "\U0001f525",
    "espada": "\u2694", "guerreiro": "\u2694", "guerreira": "\u2694", "luta": "\u2694",
    "demônio": "\U0001f479", "demônia": "\U0001f479", "monstro": "\U0001f479",
    "deus": "\u26a1", "deusa": "\u26a1", "divino": "\u26a1",
    "assassino": "\U0001f5e1", "assassina": "\U0001f5e1",
}


_ICONE_DECO = {"\U0001f9d9": "chapeu", "✨": "estrela", "⛓": "corrente", "\U0001f451": "coroa",
               "\U0001f480": "caveira", "❤": "coracao", "\U0001f525": "fogo", "⚔": "espadas",
               "\U0001f479": "caveira", "⚡": "raio", "\U0001f5e1": "espadas"}


def legenda_criativa(cartoes, vw, vh, cor_cena=AMARELO, eh_abertura=True):
    """01/11 dona (3a versao): abertura = 2 palavras eletrizantes; enfase = 1 palavra grande que fica mais tempo,
    pode correr com a legenda normal. Anteriores esmaecendo. Decoracao visual (emoji acima)."""
    if os.environ.get("ANIME_LEGENDA_MIX", "1") != "0":  # 01/11 dona: MIX do projeto Veo/MS Energy é o padrão
        try:
            import legenda_mix
            try:
                from fx_subtitles import _PESADAS
                pesada = _PESADAS.search
            except Exception:  # noqa: BLE001
                pesada = None
            return legenda_mix.gerar(cartoes, vw, vh, cor_cena, eh_abertura, pesada, ELEMENTOS_ABRE,
                                     lambda w: _ICONE_DECO.get(DECORACAO.get(w)))
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[gancho] legenda MIX falhou ({type(e).__name__}: {e}) — versão anterior")
    retrato = vh > vw
    base = int((0.11 if retrato else 0.20) * vh)
    estilos = [f"Style: Cria,Impact,{base},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,"
               f"0,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1"]
    cores = [cor_cena] + [c for c in CORES_ABRE if c != cor_cena]
    elems, posicoes = list(ELEMENTOS_ABRE), (POS_RETRATO if retrato else POS_DEITADO)
    if eh_abertura:
        pares = []
        for cart in cartoes:
            ps, fim = list(cart[:-1]), cart[-1]
            for i in range(0, len(ps), 2):
                pares.append(ps[i:i + 2] + [ps[i + 2][0] if i + 2 < len(ps) else fim])
        cartoes = pares
    linhas, k = [], 0
    for c, cart in enumerate(cartoes):
        palavras, fim = cart[:-1], float(cart[-1])
        if not palavras:
            continue
        prox = float(cartoes[c + 1][0][0]) if c + 1 < len(cartoes) and cartoes[c + 1][:-1] else None
        if prox is not None and prox - fim < 0.6:
            fim = max(fim, prox - 0.02)
        brilho, entra, sai_m = ELEMENTOS_ABRE[elems[c % len(elems)]]
        px, py = posicoes[c % len(posicoes)]
        y, alt_ant = py * vh, 0.0
        for j, (t0, w) in enumerate(palavras):
            t0 = float(t0)
            w_raw = re.sub(r"[^\w!?%-]+$", "", w).upper() or w.upper()
            w_low = w_raw.lower()
            fonte, cor = FONTES_ABRE[k % len(FONTES_ABRE)], cores[k % len(cores)]
            tam = int(base * TAMANHOS_ABRE[k % len(TAMANHOS_ABRE)] * ESCALA_FONTE.get(fonte, 1.0))
            giro = GIROS[k % len(GIROS)] if eh_abertura else 0
            k += 1
            larg = len(w_raw) * tam * 0.56
            x = min(max(px * vw, larg / 2 + vw * 0.03), vw - larg / 2 - vw * 0.03)
            y += (alt_ant + tam) * 0.46 if j else 0
            alt_ant = tam
            yy = min(y, vh * 0.72)
            min_dur = 0.6 if (not eh_abertura and len(palavras) == 1) else 0.25
            t1 = max(fim, t0 + min_dur)
            d = int((t1 - t0) * 1000)
            sai = sai_m.format(d=d, d1=max(0, d - 180), d2=max(0, d - 140), d3=max(0, d - 100))
            fade_ant = ""
            if not eh_abertura and j > 0:
                fade_ant = "\\alpha&H80&\\t(0,%d,\\alpha&H00&)" % min(300, d // 2)
            pos = "\\an5\\pos(%d,%d)\\frz%d\\fn%s\\fs%d" % (int(x), int(yy), giro, fonte, tam)
            bg = max(6, tam // 7)
            linhas.append("Dialogue: 4,%s,%s,Cria,,0,0,0,,{%s\\1a&HFF&\\bord%d\\3c%s\\blur%d%s%s%s}%s" % (
                _ts(t0), _ts(t1), pos, bg, brilho, bg, fade_ant, entra, sai, w_raw))
            linhas.append("Dialogue: 5,%s,%s,Cria,,0,0,0,,{%s\\1c%s\\bord%d\\3c&H00000000&\\shad%d%s%s%s}%s" % (
                _ts(t0), _ts(t1), pos, cor, max(2, tam // 30), max(2, tam // 25), fade_ant, entra, sai, w_raw))
            deco = _ICONE_DECO.get(DECORACAO.get(w_low))
            if deco:  # 01/11: a fonte da nuvem não tem emoji (saía quadradinho) — ícone desenhado (anime_cartoes)
                import anime_cartoes as _ac
                dy = int(yy - tam * 0.95)
                for _ly, _tags, _des in _ac.icone(deco, 0, 0, int(tam * 0.8), 6):
                    linhas.append("Dialogue: 6,%s,%s,Cria,,0,0,0,,{%s\\pos(%d,%d)%s%s%s}%s" % (
                        _ts(t0), _ts(t1), _tags, int(x), dy, fade_ant, entra, sai, _des))
    return estilos, linhas


def extras(gancho_in, video=None, na_legenda=False):
    """na_legenda=True (legenda ASS do longo): a abertura criativa vem da própria legenda falada (fx_subtitles +
    legenda_criativa) e o gancho escrito, que não bate com a fala, não entra."""
    def fn(vw, vh, dur):
        gancho = gancho_in
        retrato = vh > vw
        fs = int((84 if retrato else 46) * min(vw, vh) / 720)
        # deitado (27/10): faixa escura translúcida atrás (BorderStyle 3) em vez de letra grande — legível e fora do rosto
        borda = "1,{0},2".format(max(3, fs // 12)) if retrato else "3,{0},0".format(max(6, fs // 6))
        fundo = "&H90000000" if retrato else "&H70000000"
        fonte = os.environ.get('ANIME_SUB_FONT_ASS') or 'Impact'
        estilos = [
            f"Style: Hook,{fonte},{fs},&H00FFFFFF,&H00FFFFFF,&H00000000,{fundo},"
            f"0,0,0,0,100,100,1,0,{borda},8,40,40,0,1",
            "Style: Bar,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        ]
        ev = []
        # 01/11 dona: "as palavras não batem com a legenda" — com a abertura criativa na legenda, sem gancho escrito
        if na_legenda and float(os.environ.get("ANIME_LEGENDA_CRIATIVA_S", "8") or 0) > 0:
            gancho = ""
        if gancho:
            # GANCHO_Y (fração, 25/10): Short de parceiro com a tarja no alto — o gancho desce pra não cobri-la
            y = int(vh * float(os.environ.get("GANCHO_Y") or (0.11 if retrato else 0.025)))
            ev.append(f"Dialogue: 3,{_ts(0)},{_ts(min(3.2, dur))},Hook,,0,0,0,,"
                      f"{{\\an8\\pos({vw // 2},{y})\\fad(0,300)}}" + "\\N".join(_linhas(gancho, retrato)))
        if dur > 5:
            h = max(6, vh // 160)
            rect = f"m 0 0 l {vw} 0 l {vw} {h} l 0 {h}"
            ev.append(f"Dialogue: 2,{_ts(0)},{_ts(dur)},Bar,,0,0,0,,"
                      f"{{\\an7\\pos(0,{vh - h})\\p1\\c{AMARELO}\\fscx0\\t(0,{int(dur * 1000)},\\fscx100)}}{rect}{{\\p0}}")
        return estilos, ev
    return fn


# 28/10 teste T5 (dona: "Remotion faz o que no ffmpeg é muito difícil; mixar"): o corte continua no ffmpeg e só o
# GANCHO dos 3 s vira camada do Remotion (claude-code-video\remotion\src\_cortes\gancho — fora de src\videos, que a
# linha CLAUDE-CODE-VIDEO limpa a cada vídeo e apagava o gancho (28/10): palavra por palavra
# com carimbo, a mais forte amarela, tremor), fundo transparente (ProRes 4444) sobreposto aqui. Só com RAM livre
# >= 3 GB (o Chrome do render usa ~1 GB); falhou/estourou = gancho de sempre (ASS). Mata a ÁRVORE no prazo (o Chrome
# do Remotion travou a linha CLAUDE-CODE-VIDEO por 2h20 em 26/10 com capture_output).
REMOTION = Path(r"D:\claude-code-video\remotion")
REMOTION_PRAZO_S = 240


def _ram_livre_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 1024 ** 3
    except Exception:  # noqa: BLE001
        return 0.0


def _camada_remotion(gancho, y, out_mov):
    try:
        return _camada_remotion_(gancho, y, out_mov)
    except Exception as e:  # noqa: BLE001 — PC2/PC3 não têm o Remotion; qualquer erro = gancho de sempre
        logging.warning(f"[gancho] Remotion indisponível ({type(e).__name__}: {e}) — gancho de sempre")
        return False


def _camada_remotion_(gancho, y, out_mov):
    if not (REMOTION / "node_modules").exists():
        return False
    if _ram_livre_gb() < 3.0:
        logging.info("[gancho] Remotion pulado (RAM livre < 3 GB) — gancho de sempre")
        return False
    import json
    palavras = gancho.split()
    forte = max(range(len(palavras)), key=lambda k: len(palavras[k])) if palavras else 0
    props = Path(out_mov).with_suffix(".props.json")
    props.write_text(json.dumps({"texto": gancho, "y": y, "forte": forte, "entrada": "carimbo"}, ensure_ascii=False),
                     encoding="utf-8")
    logf = Path(out_mov).with_suffix(".remotion.log")
    cmd = ["cmd", "/c", "npx", "remotion", "render", "src/_cortes/gancho/index.ts", "Main", str(out_mov),
           f"--props={props}", "--codec=prores", "--prores-profile=4444", "--image-format=png",
           "--pixel-format=yuva444p10le", "--concurrency=2", "--log=error"]
    try:
        for tentativa in (1, 2):  # 28/10: o Chrome do render às vezes cai na hora (rc 0xC0000409); a 2ª passa
            with open(logf, "w", encoding="utf-8") as lf:
                p = subprocess.Popen(cmd, cwd=str(REMOTION), stdout=lf, stderr=subprocess.STDOUT,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                try:
                    p.wait(timeout=REMOTION_PRAZO_S)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
                    logging.warning(f"[gancho] Remotion passou de {REMOTION_PRAZO_S} s — gancho de sempre")
                    return False
            ok = p.returncode == 0 and Path(out_mov).exists() and Path(out_mov).stat().st_size > 10000
            if ok:
                return True
            logging.warning(f"[gancho] Remotion falhou (rc {p.returncode}; {logf}; tentativa {tentativa})")
        return False
    finally:
        props.unlink(missing_ok=True)


def queimar(video_in, video_out, gancho):
    """Passada só com gancho + barra (vídeo curto). Retorna True se gravou video_out."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:format=duration", "-of", "json", str(video_in)],
                           capture_output=True, text=True, timeout=60)
        import json
        d = json.loads(r.stdout)
        vw, vh = int(d["streams"][0]["width"]), int(d["streams"][0]["height"])
        dur = float(d["format"]["duration"])
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[gancho] ffprobe falhou ({e})")
        return False
    camada = None
    if gancho and vh > vw and os.environ.get("CORTES_GANCHO_REMOTION") == "B":
        y = float(os.environ.get("GANCHO_Y") or 0.11)
        mov = Path(video_out).with_suffix(".gancho.mov")
        if not (REMOTION / "node_modules").exists():
            usado = "fora"  # 29/10: PC2 não tem Remotion — 22 de 33 sorteios B viravam A_falhou e sujavam o T5
        elif _camada_remotion(gancho, y, mov):
            camada = mov
            gancho = ""  # o ASS fica só com a barra de progresso
            usado = "B"
        else:
            usado = "A_falhou"
        from fx_subtitles import marcar_usado
        marcar_usado(Path(video_out).parent, "gancho_remotion", usado)
    estilos, ev = extras(gancho, video_in)(vw, vh, dur)
    if not ev and not camada:
        return False
    ass = Path(video_out).with_suffix(".gancho.ass")
    ass.write_text(
        "[Script Info]\nScriptType: v4.00+\n" f"PlayResX: {vw}\nPlayResY: {vh}\n" "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding\n" + "\n".join(estilos) + "\n\n[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(ev) + "\n",
        encoding="utf-8")
    entrada = ["ffmpeg", "-y", "-i", str(Path(video_in).resolve())]
    fps60 = ",fps=60" if os.environ.get("ANIME_60FPS", "1") != "0" else ""  # 01/11 dona: YouTube vê 1080p60
    fontes = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "fonts"
    sub = f"subtitles={ass.name}" + (f":fontsdir='{fontes.as_posix().replace(':', chr(92) + ':')}'"
                                     if fontes.is_dir() else "")
    if camada:
        entrada += ["-i", str(camada.resolve())]
        filtro = ["-filter_complex", f"[0:v]{sub}[b];[1:v]scale={vw}:{vh}[g];"
                                     f"[b][g]overlay=0:0:eof_action=pass:format=auto{fps60}[v]",
                  "-map", "[v]", "-map", "0:a?"]
    else:
        filtro = ["-vf", f"{sub}{fps60}"]
    cmd = entrada + filtro + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "60", "-pix_fmt", "yuv420p",
                              "-c:a", "copy", "-movflags", "+faststart", str(Path(video_out).resolve())]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1800, cwd=str(ass.parent))
        return Path(video_out).exists() and Path(video_out).stat().st_size > 10000
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[gancho] passada falhou ({type(e).__name__})")
        return False
    finally:
        ass.unlink(missing_ok=True)
        if camada:
            camada.unlink(missing_ok=True)
