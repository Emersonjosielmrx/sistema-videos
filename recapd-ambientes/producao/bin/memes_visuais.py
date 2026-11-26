"""memes_visuais.py — memes VISUAIS no recap longo (dona 29/10: "não vi nenhum meme visual como os do hipercool, que
insere vídeos, memes e figurinhas na tela"). Copiado do D:\\hipercool-videos\\bin\\fx_memes.py:
  - figurinha: o meme estampado por cima do trecho, sem som, quando o narrador fala um gatilho de emoção
    ("eita", "como assim", "coitado"...) — fx_clips._com_figurinha;
  - interrupção: meme em TELA CHEIA com o som dele logo depois de uma fala de emoção forte (choque, deboche,
    vergonha, raiva), no máximo 1 por minuto — anime-pipeline._memes_resumo insere no concat.
Catálogo: config/memes_catalogo.json (o do historias-em-frames); arquivos em workspace/assets/memes_img."""
import json
import os
import random
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "config" / "memes_catalogo.json"
MEMES_IMG = RAIZ / "workspace" / "assets" / "memes_img"

GATILHOS = {
    "choque": ["eita", "caramba", "caraca", "rapaz do céu", "meu deus", "pelo amor de deus", "que isso",
               "misericórdia", "não acredito", "impossível", "olha isso", "levou um susto", "toma um susto",
               "de repente", "sem acreditar", "chocado", "chocada"],
    "confusão": ["como assim", "ué", "hein", "peraí", "entendi nada", "não entende", "sem entender", "confuso"],
    "deboche": ["coitado", "coitada", "tadinho", "tadinha", "já era", "trouxa", "não aprende", "riu da cara",
                "humilhou", "humilhado", "humilhada"],
    "vergonha": ["sem graça", "que vergonha", "envergonhada", "envergonhado", "constrangedor", "corou"],
    "alegria": ["conseguiu", "venceu", "vitória", "comemora", "comemoram", "finalmente"],
    "tristeza": ["chorando", "chora", "triste", "sozinho", "sozinha", "se foi", "lágrimas"],
    "raiva": ["desgraçado", "maldito", "canalha", "cretino", "ousadia", "furioso", "furiosa", "irritado",
              "irritada", "com raiva"],
}
TAGS = {
    "choque": ["choque", "susto", "surpresa", "reação extrema", "pânico"],
    "confusão": ["confusão", "dúvida", "questionamento", "confuso"],
    "deboche": ["deboche", "sarcasmo", "ironia", "julgamento"],
    "vergonha": ["constrangimento", "awkward", "desconforto"],
    "alegria": ["alegria", "felicidade", "sucesso", "vitória"],
    "tristeza": ["tristeza", "choro", "decepção"],
    "raiva": ["raiva", "frustração", "desaprovação"],
}
INTERROMPE = {"choque", "deboche", "vergonha", "raiva"}
# O limite anterior de 3,5 s cortava falas que terminavam depois disso. Mantemos
# apenas uma proteção contra arquivos anômalos; a duração usada no render vem do áudio.
# Faixa apenas para rejeitar arquivos sem fala útil; não limita a duração final.
# 01/11 dona (nV2a: meme de MAIS DE 2 MINUTOS no meio do longo): teto de 12 s. O catálogo tinha a duração errada e o
# montar_clip usava a duração real do arquivo sem teto — agora meme real acima do teto é DESCARTADO (não entra cortado)
INTERROMPE_DUR = (1.0, 12.0)
MEME_TAIL_S = 0.15
_cat = None


def _local(arquivo):
    """O catálogo guarda D:\\hipercool-materiais\\assets\\memes_img\\...; aqui (PC ou Kaggle) é workspace/assets."""
    partes = Path(arquivo.replace("\\", "/")).parts
    if "memes_img" in partes:
        return MEMES_IMG.joinpath(*partes[partes.index("memes_img") + 1:])
    return Path(arquivo)


# 21/11 dona (longos): "os memes antigos vou remover alguns pra dar lugar aos NOVOS, que têm prioridade". Os 20 novos
# com fala (memes_img/memes_novos, até então só no resumo) entram no catálogo com a emoção de cada um e, nas
# interrupções do meio do vídeo, são escolhidos ANTES dos antigos enquanto houver novo sem usar. MEMES_NOVOS_PRIORIDADE=0
# volta ao sorteio só entre os antigos. Os que a dona remove (bin/revisar_memes.py) ficam em config/memes_removidos.json
# e saem de todo sorteio (fx_detect.meme_proibido). Nada é apagado do disco.
NOVOS_DIR = MEMES_IMG / "memes_novos"
EMOCAO_NOVOS = {
    "01": "confusão", "02": "raiva", "03": "deboche", "04": "vergonha", "05": "deboche", "06": "choque",
    "07": "raiva", "08": "alegria", "09": "raiva", "10": "choque", "11": "choque", "12": "alegria", "13": "deboche",
    "14": "confusão", "15": "choque", "16": "deboche", "17": "deboche", "18": "deboche", "19": "deboche", "20": "deboche",
}


def _novos():
    import os
    if os.environ.get("MEMES_NOVOS_PRIORIDADE", "1") == "0":
        return []
    try:
        lista = json.loads((NOVOS_DIR / "memes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    from fx_detect import meme_proibido
    out = []
    for m in lista:
        arq = NOVOS_DIR / m["arquivo"]
        ficha = fichas().get(m["arquivo"]) or {}
        # 26/11: os memes aprovados em 26/11 (numero 21 em diante) nao estao em EMOCAO_NOVOS: a emocao vem da ficha
        emo = EMOCAO_NOVOS.get(m["arquivo"][:2]) or ficha.get("emocao")
        if ficha.get("palavrao") and os.environ.get("MEMES_PALAVRAO", "1") == "0":
            continue  # 26/11: MEMES_PALAVRAO=0 tira os memes com palavrao na fala (padrao: entram, a dona aprovou)
        if arq.exists() and emo and not meme_proibido(arq):
            out.append({"file": str(arq), "kind": "video", "duration": m.get("dur"), "has_audio": True,
                        "desc": m.get("frase", ""), "tags": TAGS.get(emo, [])[:1], "ok": True, "novo": True})
    return out


def catalogo():
    global _cat
    if _cat is None:
        try:
            raw = json.loads(CATALOGO.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        _cat = _novos()
        for m in raw.values():
            if m.get("ok"):
                local = _local(m["file"])
                from fx_detect import meme_proibido  # 31/10 dona: Roda Regina / trecho de música = fora
                if (local.exists() and local.suffix.lower() not in (".avif", ".webp")
                        and not meme_proibido(local) and not meme_proibido(m.get("title") or m.get("nome") or "")):
                    _cat.append({**m, "file": str(local)})
        # 22/11 dona (longos): "quero usar APENAS os memes novos; os antigos continuam sendo muito usados". ANIME_MEMES_SO_NOVOS
        # (config/longo.json, só vale nos longos): "1" = só os 20 novos em tudo (vídeo e imagem); "video" = só novos nos
        # vídeos e as imagens antigas continuam. Vazio/0 = como antes. Sem nenhum novo achado (pasta ausente) = não filtra,
        # pra nunca ficar sem meme. Os arquivos antigos NÃO saem da pasta (os Shorts do hipercool usam os mesmos).
        import os
        modo = os.environ.get("ANIME_MEMES_SO_NOVOS", "").strip().lower()
        if modo in ("1", "video") and any(m.get("novo") for m in _cat):
            _cat = [m for m in _cat if m.get("novo")
                    or (modo == "video" and Path(m["file"]).suffix.lower() in IMAGENS)]
    return _cat


def emocao(texto):
    t = " " + re.sub(r"[^\wà-ú ]", " ", (texto or "").lower()) + " "
    for e, termos in GATILHOS.items():
        if any(f" {g} " in t for g in termos) and not (e == "choque" and " por que isso" in t):
            return e
    return None


def escolher(emo, usados, so_com_som=False, rnd=random, texto=None):
    cand = [m for m in catalogo() if m["file"] not in usados
            and (not so_com_som or (m.get("has_audio") and Path(m["file"]).suffix.lower() == ".mp4"
                                    and INTERROMPE_DUR[0] <= float(m.get("duration") or 0) <= INTERROMPE_DUR[1]))]
    # 23/11: com a frase do narrador, o meme sai pela FICHA (o que a frase pede), não por sorteio dentro da emoção
    if texto is not None and _contexto_ligado():
        if triste(texto):  # 24/11 (revisão): cena de morte não cai no sorteio de baixo
            return None
        m = _por_contexto(texto, cand, emo, rnd)
        if m:
            usados.add(m["file"])
            return m
    da_emocao = [m for m in cand if any(t.lower() in TAGS.get(emo, []) for t in m.get("tags", []))]
    pool = da_emocao or ([] if so_com_som else cand)
    novos = [m for m in pool if m.get("novo")]  # 21/11 dona: os novos (com fala) primeiro
    if novos:
        pool = novos
    if not pool:
        return None
    pool = _menos_usados(pool)
    m = rnd.choice(pool)
    usados.add(m["file"])
    return m


# ── 23/11 (dona: "usar os melhores memes da forma mais inteligente possível nos vídeos") ─────────────────────────────
# Antes: a emoção da frase vinha de uma lista de gatilhos e o meme era SORTEADO entre os da mesma emoção (9 dos 20 novos
# são "deboche": "aham sei" saía depois de uma vitória). 4 dos 20 (01, 08, 12, 14 — confusão/alegria) nunca entravam no
# meio do vídeo, só no resumo. Agora cada meme novo tem FICHA (memes_novos/fichas.json: expressões da narração que pedem
# ele + onde nunca entra) e a escolha é por PONTOS: casa com a frase (e a anterior, mais fraco) > casa com a emoção;
# meme usado nos últimos vídeos perde ponto (histórico em workspace/memes_historico.json); frase de morte/luto = sem meme.
# MEMES_CONTEXTO=0 volta ao sorteio por emoção (como antes). Nada muda nos arquivos de meme.
FICHAS = NOVOS_DIR / "fichas.json"
HISTORICO = RAIZ / "workspace" / "memes_historico.json"
HIST_VIDEOS = 6  # quantos vídeos para trás contam na penalidade
TRISTE = ("morreu", "morre", "morte", "morto", "morta", "mortos", "faleceu", "funeral", "enterro", "luto", "velório",
          "desviver", "deixou de viver", "não sobrou nada", "estourado no meio", "partido ao meio", "viraram comida",
          "virou comida", "devorado", "devorada", "decapitado", "decapitada", "massacre", "massacrou", "vazio no coração", "coração partido", "desolado", "desolada", "desamparado", "partiu desta", "não sobreviveu", "perdeu a mãe", "perdeu o pai", "orfão", "órfã",
          "câncer", "doença terminal", "se despediu pela última", "sacrificou", "sacrifício")
_fichas = None
_hist_cache = None


def _contexto_ligado():
    import os
    return os.environ.get("MEMES_CONTEXTO", "1") != "0"


def _norm(s):
    import unicodedata
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " " + re.sub(r"[^a-z0-9]+", " ", s).strip() + " "


def fichas():
    global _fichas
    if _fichas is None:
        try:
            raw = json.loads(FICHAS.read_text(encoding="utf-8"))
            _fichas = {k: v for k, v in raw.items() if not k.startswith("_") and isinstance(v, dict)}
        except (OSError, ValueError, AttributeError):
            _fichas = {}
    return _fichas


def _ficha(m):
    return fichas().get(Path(m["file"]).name)


def fora_do_resumo(nome):
    # 26/11: meme com palavrao na fala ou so de som (ficha resumo=false) nao entra na ABERTURA do video
    try:
        return (fichas().get(str(nome)) or {}).get("resumo") is False
    except Exception:  # noqa: BLE001
        return False


TRISTE_PREFIXO = ("assassinad", "suicid", "estupr", "abusad", "abuso", "morr", "mort", "matou", "mataram", "matar",
                  "faleceu", "falecid")


def triste(texto):
    """Cena de morte/luto/abuso: nenhum meme. Palavra inteira (não pega 'morrendo de rir'); os de TRISTE_PREFIXO
    valem como começo de palavra (assassinado/assassinada)."""
    # 24/11 (revisão): "morreu de rir/vergonha", "matou a saudade/fome" não é cena triste
    t = re.sub(r" (?:morr\w*|matou|mata) (?:de|a) (?:rir|vergonha|saudade|medo|fome|curiosidade|tedio|inveja|raiva) ",
               " ", _norm(texto))
    return any(_norm(p) in t for p in TRISTE) or any(" " + p in t for p in TRISTE_PREFIXO)


def _casa(texto, termos):
    """Quantas expressões da lista aparecem no texto (palavra inteira; acento e caixa não contam)."""
    t = _norm(texto)
    return sum(1 for termo in termos if _norm(termo) in t)


def _forca_ficha(texto, termos):
    """24/11 (teste a seco): expressão de 2+ palavras ("na verdade", "caiu na armadilha") é específica e vale 2 sozinha;
    palavra solta ("mentiu", "arrogante") vale 1. Soma. Assim 'claro'/'chegou' soltos não bastam, mas a expressão sim."""
    t = _norm(texto)
    return sum((2 if len(_norm(termo).split()) >= 2 and _norm(termo) not in _FRACAS else 1)
               for termo in termos if _norm(termo) in t)


# 24/11 (roteiros reais): expressões de 2 palavras comuns em QUALQUER narração — valem 1 (como palavra solta)
_FRACAS = {_norm(x) for x in (
    "era ele", "era ela", "então era", "na verdade", "com certeza", "de fato", "é mesmo", "que coisa", "como sempre",
    "do nada", "virou um", "agora sim", "lá vem", "mexeu com", "como assim", "não acredito", "tá bom", "que seja",
    "com raiva", "mais forte", "qualquer um", "eu faria", "não liga", "tanto faz", "está perdido", "jura que",
    "é claro", "quem diria", "como esperado", "tinha razão", "se acha", "grande coisa", "sério mesmo", "num golpe")}


def _historico():
    global _hist_cache
    if _hist_cache is None:
        try:
            _hist_cache = json.loads(HISTORICO.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _hist_cache = []
        if not isinstance(_hist_cache, list):
            _hist_cache = []
    return _hist_cache


def _uso_recente(nome):
    """0 = não usado nos últimos HIST_VIDEOS vídeos; até 1 = usado no último."""
    pen = 0.0
    for i, video in enumerate(reversed(_historico()[-HIST_VIDEOS:])):
        if nome in (video.get("memes") or []):
            pen = max(pen, 1.0 - i / HIST_VIDEOS)
    return pen


def _menos_usados(pool):
    """Do pool, fica só com os menos usados nos últimos vídeos (sorteio continua entre eles)."""
    if not _contexto_ligado() or len(pool) < 2:
        return pool
    menor = min(_uso_recente(Path(m["file"]).name) for m in pool)
    return [m for m in pool if _uso_recente(Path(m["file"]).name) <= menor + 1e-9]


def _pontos(m, texto, anterior, emo):
    f = _ficha(m)
    if not f:
        return None
    if _casa(texto, f.get("nunca", [])) or _casa(anterior, f.get("nunca", [])):
        return None
    h = _forca_ficha(texto, f.get("cabe", []))
    # 24/11 (revisão): palavra comum solta ("claro", "chegou", "de novo") casava em quase toda frase. Agora 1 expressão
    # só vale se a emoção da frase bate com a ficha; 2+ expressões valem sozinhas.
    # 24/11 (roteiro real): ficha com ZERO expressões casadas passava só por ter a mesma emoção da frase ("furioso" ->
    # "não suporto mais", que não tem "furioso"). Agora precisa casar pelo menos 1 expressão da PRÓPRIA ficha.
    if h == 0 or (h < 2 and not (emo and f.get("emocao") == emo)):
        return None
    p = 3.0 * h  # 24/11: a frase anterior não soma mais (o "foda-se" ia pro "rei teve a ousadia" por "regras" da anterior)
    if emo and f.get("emocao") == emo:
        p += 1.5
    return p


def _por_contexto(texto, cand, emo, rnd, anterior=""):
    if triste(texto) or triste(anterior):
        return None
    notas = []
    for m in cand:
        p = _pontos(m, texto, anterior, emo)
        if p is None or p < 1.5:  # nada da ficha e nem a emoção: não é o meme desta frase
            continue
        p -= 2.0 * _uso_recente(Path(m["file"]).name)
        notas.append((p + rnd.random() * 0.3, m))  # desempate leve: mesma frase não dá sempre o mesmo
    if not notas:
        return None
    notas.sort(key=lambda x: -x[0])
    return notas[0][1] if notas[0][0] > 0 else None


def pede_meme(texto, anterior=""):
    """(emoção, força): força 2 = a frase casa com a ficha de algum meme; 1 = só gatilho de emoção forte; 0 = não."""
    if triste(texto):
        return None, 0
    emo = emocao(texto)
    if _contexto_ligado() and fichas():
        hits = max(_forca_ficha(texto, f.get("cabe", [])) for f in fichas().values())
        if hits >= 2 or (hits and emo):  # 24/11: 1 palavra solta sem emoção na frase não pede meme
            return emo, 2
        # 24/11 (roteiro real): "de repente" é narração neutra em recap ("de repente, uma garota aparece"); sozinho
        # disparava sorteio. Com o contexto ligado, choque SÓ por "de repente" não pede meme.
        if emo == "choque" and not emocao(re.sub(r"(?i)de repente", " ", texto or "")):
            return emo, 0
    return emo, (1 if emo in INTERROMPE else 0)


def registrar_uso(workspace, memes):
    """Guarda quais memes entraram neste vídeo (para o próximo variar). Falha aqui nunca derruba o render."""
    global _hist_cache
    try:
        nomes = sorted({Path(str(m.get("file") if isinstance(m, dict) else m)).name for m in memes if m})
        if not nomes:
            return
        hist = [h for h in _historico() if h.get("video") != str(workspace)]
        import time
        hist.append({"video": str(workspace), "quando": time.strftime("%Y-%m-%d %H:%M"), "memes": nomes})
        HISTORICO.parent.mkdir(parents=True, exist_ok=True)
        _hist_cache = hist[-50:]  # 24/11: o próximo vídeo do mesmo processo também vê este
        HISTORICO.write_text(json.dumps(_hist_cache, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def escolher_interrupcoes(textos, inicio=8, cada=12, rnd=random):
    """[(índice da frase, meme)] — depois de frase com emoção FORTE, no mínimo `cada` frases (~1 min) entre elas.
    23/11: com MEMES_CONTEXTO (padrão), a frase também vale quando casa com a ficha de um meme (inclusive os de
    confusão/alegria que antes nunca entravam), o meme é o que a frase pede e cena de morte/luto fica sem meme."""
    out, usados, ultimo = [], set(), -10 ** 6
    ctx = _contexto_ligado() and bool(fichas())
    for k, texto in enumerate(textos):
        if k < inicio or k > len(textos) - 4 or k - ultimo < cada:
            continue
        if not ctx:
            emo = emocao(texto)
            if emo not in INTERROMPE:
                continue
            m = escolher(emo, usados, so_com_som=True, rnd=rnd)
        else:
            anterior = textos[k - 1] if k else ""
            emo, forca = pede_meme(texto, anterior)
            if forca == 0:
                continue
            cand = [m for m in catalogo() if m["file"] not in usados and m.get("has_audio")
                    and Path(m["file"]).suffix.lower() == ".mp4"
                    and INTERROMPE_DUR[0] <= float(m.get("duration") or 0) <= INTERROMPE_DUR[1]]
            m = _por_contexto(texto, cand, emo, rnd, anterior)
            if m:
                usados.add(m["file"])
            # 24/11 (teste com roteiro real): frase que casava com uma ficha cujo meme já foi usado caía no sorteio
            # ("furioso" sem o "ah morre diabo" virou "não suporto mais"). Agora só o gatilho forte SEM ficha nenhuma
            # sorteia; casou com ficha e o meme não está livre = sem meme (melhor sem meme que meme errado).
            # 24/11 (2º roteiro real, 1158 frases): o sorteio por gatilho ("coitado", "de repente") dava 10 de 18 memes,
            # quase todos fora de hora ("o coitado começa a chorar" -> "mentira hahaha"). Com MEMES_SORTEIO_GATILHO=0
            # (padrão) só entra meme quando a frase casa com uma ficha; =1 volta o sorteio por gatilho.
            elif forca == 1 and not triste(anterior) and os.environ.get("MEMES_SORTEIO_GATILHO", "0") == "1":  # gatilho forte sem ficha que case: como antes (sorteio na emoção, menos usados)
                m = escolher(emo, usados, so_com_som=True, rnd=rnd)
        if m:
            out.append((k, m))
            ultimo = k
    return out


IMAGENS = (".jpg", ".jpeg", ".png", ".gif")
IMAGEM_S = 1.2


def escolher_imagens(textos, ocupados=(), inicio=8, cada=10, rnd=random):
    """Dona 31/10: a figurinha no canto não ajudava — meme de IMAGEM agora ocupa a tela toda, rápido (IMAGEM_S), depois
    de frase com qualquer emoção, no mínimo `cada` frases entre eles e fora das frases que já têm meme/série."""
    imgs = [m for m in catalogo() if Path(m["file"]).suffix.lower() in IMAGENS]
    out, usados, ultimo = [], set(), -10 ** 6
    ocupados = set(ocupados)
    for k, texto in enumerate(textos):
        if k < inicio or k > len(textos) - 4 or k - ultimo < cada or any(abs(k - o) < 3 for o in ocupados):
            continue
        emo = emocao(texto)
        if not emo:
            continue
        cand = [m for m in imgs if m["file"] not in usados]
        da_emo = [m for m in cand if any(t.lower() in TAGS.get(emo, []) for t in m.get("tags", []))]
        # 24/11 (plano F9-E): sem imagem da emoção da frase, era SORTEIO CEGO entre todas; agora fica sem imagem.
        # MEMES_IMAGEM_SORTEIO=1 volta ao antigo. Frase triste também fica sem imagem.
        pool = da_emo if (_contexto_ligado() and os.environ.get("MEMES_IMAGEM_SORTEIO", "0") != "1") else (da_emo or cand)
        if _contexto_ligado() and triste(texto):
            continue
        if not pool:
            continue
        m = rnd.choice(pool)
        usados.add(m["file"])
        out.append((k, m))
        ultimo = k
    return out


def montar_imagem(meme, out_path, w, h, sfx=None, fps=30):
    """Imagem em tela cheia por IMAGEM_S: fundo dela borrado + ela inteira entrando com um soco de zoom (1,25 -> 1)."""
    import subprocess
    d = IMAGEM_S
    entrada = ["-loop", "1", "-t", f"{d:.2f}", "-i", meme["file"]]
    if Path(meme["file"]).suffix.lower() == ".gif":
        entrada = ["-ignore_loop", "0", "-t", f"{d:.2f}", "-i", meme["file"]]
    audio = (["-i", str(sfx)] if sfx else ["-f", "lavfi", "-t", f"{d:.2f}", "-i", "anullsrc=r=44100:cl=stereo"])
    # 21/11 dona (longos): o whoosh do meme de imagem também mais baixo (ANIME_SFX_TRANS_VOL, vazio = como antes)
    try:
        import os
        vol = float(os.environ.get("ANIME_SFX_TRANS_VOL") or 1)
    except ValueError:
        vol = 1.0
    vol_f = f"volume={vol:g}," if sfx and 0 < vol < 1 else ""
    vf = (f"[0:v]fps={fps},format=yuv420p,split[a][b];"
          f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2[fundo];"
          f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease,"
          f"scale='trunc(iw*(1+0.25*max(0,1-t/0.18))/2)*2':'trunc(ih*(1+0.25*max(0,1-t/0.18))/2)*2':eval=frame[meio];"
          f"[fundo][meio]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v];"
          f"[1:a]{vol_f}aresample=44100,aformat=channel_layouts=stereo,apad,atrim=duration={d:.2f},"
          f"afade=t=out:st={d - 0.2:.2f}:d=0.2[au]")
    cmd = ["ffmpeg", "-y", "-v", "error", *entrada, *audio, "-filter_complex", vf, "-map", "[v]", "-map", "[au]",
           "-t", f"{d:.2f}", "-r", str(fps), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return Path(out_path).exists() and Path(out_path).stat().st_size > 1000


def montar_clip(meme, out_path, w, h, fps=30):
    """Meme em tela cheia, mantendo a fala inteira do áudio original."""
    import subprocess
    dur = 0.0
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             meme["file"]], capture_output=True, text=True, timeout=15)
        dur = float((probe.stdout or "").strip().splitlines()[0])
    except (ValueError, IndexError, OSError, subprocess.SubprocessError):
        dur = 0.0
    if dur <= 0:
        dur = float(meme.get("duration") or 2.0)
    if dur > INTERROMPE_DUR[1] + 0.5:  # duração real passa do teto (catálogo mentia): o meme não entra
        import logging
        logging.warning(f"[meme] {Path(meme['file']).name} tem {dur:.0f} s de verdade (teto {INTERROMPE_DUR[1]:.0f} s) — fora")
        return False
    # Pequena sobra evita cortar a última sílaba por arredondamento do AAC.
    dur += MEME_TAIL_S
    vf = (f"[0:v]fps={fps},split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"boxblur=20:2[fundo];[b]scale={w}:{h}:force_original_aspect_ratio=decrease[meio];"
          f"[fundo][meio]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", meme["file"],
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
           "-af", "loudnorm=I=-16:TP=-2", "-ar", "44100", "-ac", "2", "-t", f"{dur:.2f}", "-r", str(fps),
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
