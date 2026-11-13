# -*- coding: utf-8 -*-
"""elenco.py — VOZ FIXA POR OBRA E POR PERSONAGEM + motor de voz do português (edge ou Gemini).

Pedido do dono (15/10):
- narrador, protagonista e par principal com voz FIXA na obra (mudam de uma obra pra outra);
- cada personagem com a sua voz, sempre a mesma;
- testar o português só com as vozes edge Multilingual (rápido, sem cota) e variações virtuais delas.

Por que a voz trocava: o registro de vozes do Gemini (workspace/voices-registry.json) é UM SÓ pra todas as obras e
liga a voz ao NOME que a IA escreveu. Quando o roteiro chama o protagonista de "Rapaz" ou "Jovem", ele pegava a voz
daquele nome genérico (de outra obra; "Jovem" era até voz de mulher). Aqui:
  1. normalizar(): apelido conhecido vira o nome oficial; nome genérico ("Rapaz", "Jovem"...) com muitas falas num
     capítulo em que o protagonista (ou o par) não aparece pelo nome vira o protagonista (ou o par);
  2. voz por OBRA (config/elenco/<obra>.json): narrador, protagonista e par têm vozes reservadas; personagem novo
     ganha uma voz livre e fica com ela; figurante genérico usa vozes de figurante (nunca as reservadas).

Motor do português: config/fila.json "tts_motor"; env HIPER_TTS_MOTOR passa por cima.
  "edge"   = tudo no edge (rápido, sem cota) — teste do dono a partir do cap 9 do The Inheritor;
  "misto"  = narrador no edge (70-80% das falas) + personagens no Gemini com voz fixa (~20-30% das falas, poucas
             chamadas -> quase sem limite de cota); personagem não cai pro edge (voz não troca): espera o Gemini;
  "gemini" = tudo no Gemini (como era; ~70 min de voz por capítulo).
Trocar: python bin/elenco.py --motor edge|misto|gemini (ou os botões "VOZ - ..." na pasta Hipercool do desktop).
As outras línguas continuam no idiomas.falar (edge nativo da língua).

PROIBIDAS: só pt-BR-AntonioNeural (voz masculina ruim). Em 16/10 o dono liberou de volta a
pt-BR-FranciscaNeural e a it-IT-IsabellaNeural — ele ouviu as amostras depois de reclamar que os
personagens falavam "como gringo tentando falar português", e a Francisca é das poucas vozes
nativas de pt-BR que o edge ainda tem (as outras duas são Thalita e Antonio).
"""
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from hp_common import PROJECT_DIR, log

PASTA = PROJECT_DIR / "config" / "elenco"
PASTA_PRONUNCIA = PROJECT_DIR / "config" / "pronuncia"
TTS_CACHE = PROJECT_DIR / "workspace" / "tts_cache"

PROIBIDAS = {"pt-BR-AntonioNeural"}  # 16/10: o dono liberou Francisca e Isabella
# Multilingual = falam qualquer língua (o dono ouviu as amostras em pt e aprovou em 15/10)
# As de pt-BR vêm PRIMEIRO: são as únicas sem sotaque. As Multilingual estrangeiras falam português,
# mas com pronúncia de gringo em parte das palavras — foi a reclamação do dono em 16/10.
EDGE_F = ["pt-BR-ThalitaMultilingualNeural", "pt-BR-FranciscaNeural", "en-US-AvaMultilingualNeural",
          "en-US-EmmaMultilingualNeural",
          "de-DE-SeraphinaMultilingualNeural", "fr-FR-VivienneMultilingualNeural"]
EDGE_M = ["en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural", "en-AU-WilliamMultilingualNeural",
          "de-DE-FlorianMultilingualNeural", "fr-FR-RemyMultilingualNeural", "it-IT-GiuseppeMultilingualNeural",
          "ko-KR-HyunsuMultilingualNeural"]
# Variações virtuais (velocidade, tom): a 1ª é a voz pura.
# 16/10: o passo era pequeno demais pra diferenciar personagem. A "mulher desconhecida" do cap 10 pegou a
# Seraphina da Professora com +8%/+4Hz — +4 Hz num f0 de ~200 Hz é ~0,3 semitom, ninguém ouve a diferença.
# Agora o passo mínimo de tom é 12 Hz (~1 semitom) e o de velocidade 6%, dentro do que o edge ainda faz soar
# natural (±20 Hz / ±18% medidos em amostra; acima disso começa a sair voz de desenho).
VARIACOES = [("+0%", "+0Hz"), ("-10%", "-18Hz"), ("+12%", "+18Hz"), ("+15%", "-12Hz"), ("-6%", "+12Hz"),
             ("+6%", "-20Hz"), ("-14%", "+20Hz"), ("+18%", "+6Hz"), ("-4%", "-14Hz"), ("+8%", "+14Hz")]
GEMINI_F = ["Leda", "Aoede", "Zephyr", "Achernar", "Despina", "Erinome", "Pulcherrima", "Sulafat", "Vindemiatrix"]
GEMINI_M = ["Sadachbia", "Charon", "Puck", "Fenrir", "Orus", "Gacrux", "Iapetus", "Algenib", "Algieba", "Achird"]
NARRADOR = ("narrador", "narradora", "narrator", "voz off", "voz_off", "")
GENERICOS = {"rapaz", "garota", "garoto", "homem", "mulher", "menina", "menino", "desconhecido", "desconhecida",
             "personagem", "alguém", "alguem", "voz", "estranho", "estranha", "jovem", "moça", "moca", "velhote",
             "velho", "velha", "senhor", "senhora", "pessoa", "ela", "ele", "cara", "figura", "homem 1", "homem 2",
             "mulher 1", "mulher 2", "mulher desconhecida", "homem desconhecido", "rapaz desconhecido"}
MOTORES = ("edge", "misto", "gemini")
MIN_FALAS_PROTAGONISTA = 4  # genérico com pelo menos isso num capítulo sem o nome do protagonista = ele


def motor():
    m = os.environ.get("HIPER_TTS_MOTOR", "").strip().lower()
    if not m:
        try:
            m = json.loads((PROJECT_DIR / "config" / "fila.json").read_text(encoding="utf-8")).get("tts_motor", "")
        except (OSError, ValueError):
            m = ""
    return m if m in MOTORES else "gemini"


def obra_de(pasta_paineis):
    """'.../panels/the-inheritor-cap09' -> 'the-inheritor'."""
    return re.sub(r"-cap\d+$", "", Path(pasta_paineis).name)


def _limpo(persona):
    return re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip()


def _e_generico(nome):
    n = _limpo(nome).lower()
    return n in GENERICOS or re.sub(r"\s+\d+$", "", n) in GENERICOS


def virtuais(genero):
    """Todas as vozes virtuais do gênero: primeiro cada voz base pura, depois as variações (base x tom/velocidade)."""
    bases = EDGE_F if genero == "F" else EDGE_M
    return [{"voice": b, "rate": r, "pitch": p} for r, p in VARIACOES for b in bases if b not in PROIBIDAS]


def _arq(obra):
    return PASTA / f"{obra}.json"


def _gravar(obra, el):
    """Grava trocando o arquivo inteiro de uma vez (tmp + replace).

    Este arquivo é a memória de QUEM FALA COM QUAL VOZ: a regra do dono é que o personagem
    nunca troca de voz. Com a escrita direta, um render morto no meio da gravação (acontece:
    o limitador mata, a máquina desliga, o agente interrompe) deixava o JSON truncado — e
    no render seguinte o personagem sem entrada ganhava outra voz. O replace é atômico no
    Windows e no Linux: ou fica o arquivo velho inteiro, ou o novo inteiro."""
    PASTA.mkdir(parents=True, exist_ok=True)
    alvo = _arq(obra)
    tmp = alvo.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(el, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, alvo)


def _n(nome):
    return int(hashlib.md5(nome.encode("utf-8")).hexdigest(), 16)


def carregar(obra):
    """Elenco da obra (cria na 1ª vez: narrador sorteado pela obra, protagonista/par pelos roteiros já feitos)."""
    p = _arq(obra)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            log(f"  [!] elenco {p.name} ilegível — recriando")
    h = _n(obra)
    g = "F" if h % 2 else "M"
    el = {"_leia": ("Vozes fixas desta obra (bin/elenco.py). Pode editar à mão: edge = {voice, rate, pitch} "
                    "(vozes em EDGE_F/EDGE_M; PROIBIDA: Antonio); gemini = nome da voz. "
                    "papel: protagonista | par | personagem | figurante. apelidos = outros nomes que a IA usa."),
          "obra": obra,
          "narrador": {"genero": g, "edge": {**virtuais(g)[h % len(EDGE_F if g == 'F' else EDGE_M)], "rate": "+5%"},
                       "gemini": "Kore" if g == "F" else "Charon"},
          "personagens": {}}
    try:  # protagonista e par = os 2 nomes com mais falas nos roteiros já feitos (um de cada gênero)
        from narration import personagens_anteriores
        conhecidos = personagens_anteriores(obra, 9999)
    except Exception:  # noqa: BLE001
        conhecidos = []
    for papel, gen in (("protagonista", "M"), ("par", "F")):
        c = next((c for c in conhecidos if c[1] == gen), None)
        if c:
            el["personagens"][c[0]] = {"papel": papel, "genero": gen, "apelidos": []}
    _gravar(obra, el)
    log(f"  elenco novo de {obra}: narrador {el['narrador']['edge']['voice']}, "
        f"{', '.join(f'{k} ({v['papel']})' for k, v in el['personagens'].items()) or 'sem protagonista ainda'}")
    return el


def _achar(el, persona):
    """Nome oficial do personagem (match exato, apelido ou token de nome em comum), ou None."""
    p = _limpo(persona)
    pl = p.lower()
    for nome, d in el["personagens"].items():
        if pl == nome.lower() or pl in (a.lower() for a in d.get("apelidos", [])):
            return nome
    if _e_generico(p):
        return None
    toks = {t for t in re.split(r"[^a-zA-ZÀ-ÿ]+", pl) if len(t) >= 3}
    for nome, d in el["personagens"].items():
        if d.get("papel") == "figurante":
            continue
        if toks & {t for t in re.split(r"[^a-zA-ZÀ-ÿ]+", nome.lower()) if len(t) >= 3}:
            return nome
    return None


def normalizar(obra, locucoes):
    """Troca apelidos pelo nome oficial e genérico pelo protagonista/par quando é claramente ele/ela (ver topo).
    Devolve uma lista NOVA (não mexe no cache do roteiro); a fala trocada guarda persona_orig."""
    el = carregar(obra)
    out = [dict(l) for l in locucoes]
    presentes = {}
    for l in out:
        nome = _achar(el, l.get("persona") or "")
        if nome:
            presentes[nome] = presentes.get(nome, 0) + 1
    contagem = {}
    for l in out:
        p = _limpo(l.get("persona") or "")
        if p.lower() not in NARRADOR and _e_generico(p):
            contagem[(p.lower(), l.get("gender"))] = contagem.get((p.lower(), l.get("gender")), 0) + 1
    trocas = {}
    for papel in ("protagonista", "par"):
        nome = next((n for n, d in el["personagens"].items() if d.get("papel") == papel), None)
        if not nome or presentes.get(nome):
            continue
        gen = el["personagens"][nome]["genero"]
        cands = sorted(((c, k) for k, c in contagem.items() if k[1] == gen and c >= MIN_FALAS_PROTAGONISTA
                        and k[0] not in trocas), reverse=True)
        if cands:
            trocas[cands[0][1][0]] = nome
    n_troca = 0
    for l in out:
        p = _limpo(l.get("persona") or "")
        if p.lower() in NARRADOR:
            continue
        nome = trocas.get(p.lower()) if _e_generico(p) else _achar(el, p)
        if nome and nome != l.get("persona"):
            l["persona_orig"], l["persona"] = l.get("persona"), nome
            l["gender"] = el["personagens"][nome].get("genero", l.get("gender"))
            n_troca += 1
    if trocas:
        log(f"  elenco: genérico vira principal neste capítulo: {trocas}")
    if n_troca:
        log(f"  elenco: {n_troca} fala(s) com o nome oficial do personagem")
    return out


def _reservadas(el, campo):
    vs = [json.dumps(el["narrador"].get(campo), sort_keys=True)]
    for d in el["personagens"].values():
        if d.get(campo):
            vs.append(json.dumps(d[campo], sort_keys=True))
    return set(vs)


def voz(obra, persona, genero):
    """(voz edge {voice, rate, pitch}, voz gemini) fixas do personagem nesta obra (atribui e grava se for novo)."""
    el = carregar(obra)
    p = _limpo(persona)
    if p.lower() in NARRADOR:
        return el["narrador"]["edge"], el["narrador"].get("gemini", "Kore")
    nome = _achar(el, p)
    if not nome:
        nome = p if not _e_generico(p) else f"{p.lower()}|{(genero or 'M').upper()[:1]}"
        el["personagens"][nome] = {"papel": "figurante" if _e_generico(p) else "personagem",
                                   "genero": (genero or "M").upper()[:1], "apelidos": []}
    d = el["personagens"][nome]
    g = "F" if str(d.get("genero") or genero or "M").upper().startswith("F") else "M"
    mudou = False
    if not d.get("edge"):
        usadas = _reservadas(el, "edge")
        # base do narrador, do protagonista e do par é EXCLUSIVA: ninguém mais usa nem variação dela (soaria igual)
        exclusivas = {el["narrador"].get("edge", {}).get("voice")} | {
            x["edge"]["voice"] for x in el["personagens"].values()
            if x.get("papel") in ("protagonista", "par") and x.get("edge")}
        # 16/10: enquanto sobrar base livre, a base de QUALQUER personagem com nome também é exclusiva.
        # Antes só os 3 principais reservavam e a "mulher desconhecida" do cap 10 recebeu a mesma Seraphina
        # da Professora com +8%/+4Hz — inaudível, as duas soavam a mesma pessoa. Sem base livre, volta a
        # repetir base (menos as dos 3 principais), agora com variação bem mais forte (ver VARIACOES).
        tomadas = exclusivas | {x["edge"]["voice"] for x in el["personagens"].values()
                                if x.get("papel") == "personagem" and x.get("edge")}
        bases_g = [b for b in (EDGE_F if g == "F" else EDGE_M) if b not in PROIBIDAS]
        sobra_base = any(b not in tomadas for b in bases_g)
        pool = [v for v in virtuais(g) if v["voice"] not in (tomadas if sobra_base else exclusivas)]
        if d.get("papel") in ("protagonista", "par"):  # principais: voz pura (sem variação), a melhor livre
            pool = [v for v in pool if v["rate"] == "+0%" and v["pitch"] == "+0Hz"]
        elif d.get("papel") == "figurante":  # figurante: só variações (as vozes puras ficam pros personagens com nome)
            pool = [v for v in pool if not (v["rate"] == "+0%" and v["pitch"] == "+0Hz")]
        livres = [v for v in pool if json.dumps(v, sort_keys=True) not in usadas] or pool
        d["edge"] = livres[0] if d.get("papel") != "figurante" else livres[_n(nome) % len(livres)]
        mudou = True
    if not d.get("gemini"):
        pool = GEMINI_F if g == "F" else GEMINI_M
        usadas = {x.get("gemini") for x in el["personagens"].values()} | {el["narrador"].get("gemini")}
        livres = [v for v in pool if v not in usadas] or pool
        d["gemini"] = livres[0] if d.get("papel") != "figurante" else livres[_n(nome) % len(livres)]
        mudou = True
    if mudou:
        _gravar(obra, el)
        log(f"  elenco {obra}: {nome} -> edge {d['edge']['voice']} {d['edge']['rate']} {d['edge']['pitch']} | gemini {d['gemini']}")
    return d["edge"], d["gemini"]


# ─── texto que vai pra VOZ (a legenda continua com o texto original do roteiro) ──────────────
# 16/10: o filtro de diretivas (_tts_filter.clean_for_tts) só rodava no caminho Gemini. No edge o texto ia
# CRU e no cap 9 a Ava leu "싱긋 (sorriso)" e o Andrew "푹 (impacto) 웩 (reação)" — hangul em voz alta e a
# rubrica do tradutor junto. A limpeza aqui é CIRÚRGICA de propósito: passar o clean_for_tts inteiro mudaria
# 907 das 1118 falas da obra (ele tira o ponto final e junta "!!!" em "!"), trocando a entonação de tudo e
# torrando o tts_cache sem necessidade.
CJK = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af\u4e00-\u9fff\u3040-\u30ff]+")
# rubrica = o que o tradutor escreve entre () ou [] e ninguém fala. Lista FECHADA de propósito:
# "(99% de certeza)" e "(geralmente mais velha e mantida por outrem)" são fala de verdade e continuam.
_RUBRICA = (r"sorriso|sorrindo|risada|rindo|riso|gargalhada|suspiro|suspirando|gemido|gemendo|ofegante|"
            r"respira[çc][ãa]o|arfando|grito|gritando|choro|chorando|solu[çc]o|sussurro|sussurrando|"
            r"impacto|rea[çc][ãa]o|onomatopeia|barulho|sons? de|efeito sonoro|em pensamento|pensando|"
            r"sil[êe]ncio|pausa")
RUBRICA_BLOCO = re.compile(r"[\(\[]\s*(?:" + _RUBRICA + r")[^)\]]{0,40}[\)\]]", re.IGNORECASE)
# "[n]" é a quebra de balão que vem do scan (85 falas nos roteiros em cache); o TTS lia a letra "n"
QUEBRA_SCAN = re.compile(r"[\(\[]\s*n\s*[\)\]]", re.IGNORECASE)
LINGUAS_CJK = ("ja", "zh", "ko", "zh-cn", "zh-tw")


def texto_para_voz(texto, lang="pt"):
    """Texto cru do roteiro -> o que o TTS pode LER. Devolve "" quando a fala era só onomatopeia/rubrica
    (aí o painel vira clip de som, sem voz). A LEGENDA não usa isto: ela continua com o texto do roteiro."""
    t = texto or ""
    t = QUEBRA_SCAN.sub(" ", t)
    if (lang or "pt").lower() not in LINGUAS_CJK:
        t = CJK.sub(" ", t)  # hangul/kanji/kana: a voz não lê coreano no meio do português
    t = RUBRICA_BLOCO.sub(" ", t)
    t = re.sub(r"[\(\[]\s*[\)\]]", " ", t)  # parênteses que sobraram vazios
    t = re.sub(r"\s+", " ", t).strip(" -—")
    # 1 letra basta: fala legítima de uma letra existe no manhwa ("E?!", "Ó!") e com o limiar
    # de 2 ela virava "" — o pipeline trata "" como FALHA de TTS, põe o som de erro e ainda
    # joga a legenda do balão fora. Onomatopeia pura já foi embora nas linhas acima.
    return t if any(ch.isalpha() for ch in t) else ""


# ─── pronúncia dos nomes (config/pronuncia/<obra>.json) ──────────────────────────────────────
# 16/10: a transcrição Groq do áudio do cap 10 mostrou "o Ezeu esquentou" (= Yeseul, pela Thalita) e
# "Você disse que é Yueni" (= Ye-Eun, pelo Andrew): cada voz lia o nome coreano de um jeito e o público
# (e a transcrição do YouTube) não reconhecia ninguém. O edge-tts escapa o texto (mkssml), então não dá
# pra usar <phoneme>: a única saída é reescrever o nome do jeito que se fala, SÓ no texto da voz.
_PRON_CACHE = {}


def carregar_pronuncia(obra):
    """config/pronuncia/<obra>.json + o geral -> dict. {} quando não há nada.

    O arquivo da obra guarda os NOMES dela (Joo Inhyuk -> Jú In-hiúk). O _geral.json guarda palavra
    comum que o TTS erra em qualquer obra — em 16/10 o dono ouviu o cap 2 e apontou que "herança"
    saía errada em TODAS as vozes, inclusive nas nativas. O da obra manda quando os dois têm a mesma
    palavra."""
    if obra in _PRON_CACHE:
        return _PRON_CACHE[obra]
    d = {}
    for nome in ("_geral", obra):
        p = PASTA_PRONUNCIA / f"{nome}.json"
        if not (nome and p.exists()):
            continue
        try:
            novo_d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            log(f"  [!] pronúncia {p.name} ilegível — ignorada")
            continue
        for lang, mapa in novo_d.items():
            if isinstance(mapa, dict):
                d.setdefault(lang, {}).update(mapa)
    _PRON_CACHE[obra] = d
    return d


def aplicar_pronuncia(texto, obra, lang="pt", voice=None):
    """Troca o nome escrito pela grafia que o TTS lê certo. SÓ no texto que vai pra voz — nunca na
    legenda/karaokê, que precisa mostrar o nome de verdade. Sem mapa da língua, não mexe em nada
    (respelling de português numa voz hindi seria pior que o problema)."""
    d = carregar_pronuncia(obra) if obra else {}
    mapa = dict(d.get(lang or "pt") or {})
    mapa.update((d.get("por_voz") or {}).get(voice or "", {}))
    for nome in sorted(mapa, key=len, reverse=True):  # "Inhyuk" antes de "Hyuk"
        texto = re.sub(rf"(?<!\w){re.escape(nome)}(?!\w)", lambda _m, n=nome: mapa[n], texto,
                       flags=re.IGNORECASE)
    return texto


# ─── entonação e nível por fala ──────────────────────────────────────────────────────────────
# 16/10: o edge ignora CAIXA ALTA e as Multilingual não têm estilo, então "VOU GOZAR!!" saía com a mesma
# energia de "Imagina só..." (pico -5,8 x -5,7 dB; no mix do cap 10 o grito ficou 2 dB ABAIXO da narração).
# Nos 11 caps da obra isso vale pra 39 gritos e 195 falas com reticência — e só 2 falas do narrador têm
# reticência, então a narração (70% do áudio) não muda de ritmo.
ALVO_LUFS = -20.0     # todo wav de fala sai neste nível; o master final continua a -14 LUFS (fx_acabamento)
GANHO_GRITO_DB = 3.0  # o grito fica 3 dB ACIMA do resto da fala, que é o que a auditoria pediu
# corta a cauda de silêncio do edge (~1,1 s depois de fala curta) deixando 0,25 s de respiro:
# 18 dos 82 clips do cap 10 eram um grito de 0,6 s seguido de 1,2 s de painel parado (4 seguidos no fim).
TRIM_CAUDA = "areverse,silenceremove=start_periods=1:start_silence=0.25:start_threshold=-45dB,areverse"


# ─── curva do capítulo: acelera chegando no impacto, respira depois ──────────────────────────
# O dono (16/10): "eles vão acelerando conforme vai chegando ao clímax, como narração de futebol".
# Antes disto, TODA fala saía no mesmo nível e no mesmo ritmo — só a pontuação da própria frase
# mudava alguma coisa. Os números abaixo são de propósito pequenos: a soma com a prosódia da frase
# (grito: +10 de rate, +3 dB) não pode estourar, e a fala tem de continuar natural.
# 16/10, 2ª dose: o dono ouviu as amostras e pediu "bem mais forte a diferença entre as falas".
# Dobrei a amplitude e entrou o TOM, que é o que mais muda a sensação de emoção — voz que só acelera
# soa apressada; voz que acelera E sobe de tom soa empolgada.
SUBIDA_FALAS = 7      # quantas falas antes do impacto já começam a acelerar
PICO_RATE = 18        # % de velocidade a mais na fala do impacto
# 16/10, 3ª dose: o dono ouviu e disse que no clímax "a fala ficou fina e aguda". Subir o tom na
# voz Multilingual não soa empolgação, soa criança. O tom agora quase não sobe no pico — quem carrega
# a emoção é a velocidade, o volume e o ritmo dentro da frase (ver _ritmo_humano).
PICO_PITCH = 1        # Hz a mais de tom na fala do impacto
PICO_GANHO_DB = 4.0   # dB a mais na fala do impacto
RESPIRO_FALAS = 3     # falas DEPOIS do impacto que saem mais lentas, graves e baixas
RESPIRO_RATE = -12
RESPIRO_PITCH = -4
RESPIRO_GANHO_DB = -3.0


def curva_climax(indice, impactos):
    """(delta de velocidade %, delta de tom Hz, delta de ganho dB) pela posição na curva do capítulo.

    `impactos`: índices (base 0) das falas que o editorial marcou como momento forte.
    Chegando no impacto a voz acelera, sobe de tom e de volume aos poucos; logo depois dele cai nos
    três, que é o respiro — sem a queda o capítulo inteiro vira grito e cansa igual ao volume
    constante que o dono reclamou."""
    if not impactos or indice is None:
        return 0, 0, 0.0
    if any(0 < indice - k <= RESPIRO_FALAS for k in impactos):
        return RESPIRO_RATE, RESPIRO_PITCH, RESPIRO_GANHO_DB
    faltam = [k - indice for k in impactos if 0 <= k - indice <= SUBIDA_FALAS]
    if not faltam:
        return 0, 0, 0.0
    d = min(faltam)                       # 0 = é a própria fala do impacto
    f = (SUBIDA_FALAS - d) / SUBIDA_FALAS  # 0,0 longe -> 1,0 no impacto
    f = f * f                             # cresce devagar e dispara no fim, como locutor de futebol
    return int(round(PICO_RATE * f)), int(round(PICO_PITCH * f)), round(PICO_GANHO_DB * f, 2)


def _desloca(valor, delta, mini, maxi, sufixo):
    try:
        base = int(str(valor).rstrip("%Hz") or 0)
    except ValueError:
        base = 0
    return f"{max(mini, min(maxi, base + delta)):+d}{sufixo}"


def prosodia(texto, v, indice=None, impactos=None):
    """(voz ajustada, ganho em dB) pela pontuação da fala E pela posição no capítulo.

    Pontuação: grito ("!!" ou CAIXA ALTA com "!") sai mais rápido, mais agudo e 3 dB acima; fala com
    reticência sai mais devagar.
    Posição: `curva_climax` acelera e levanta a voz chegando no impacto e dá um respiro depois — foi
    o que o dono pediu em 16/10 ("como narração de futebol").
    A chave do cache já inclui rate/pitch, então isto não invalida o que está gravado com a voz pura."""
    dr_curva, dp_curva, dg_curva = curva_climax(indice, impactos)
    letras = [c for c in texto if c.isalpha()]
    caixa_alta = len(letras) >= 3 and sum(c.isupper() for c in letras) / len(letras) >= 0.8
    grito = "!!" in texto or (caixa_alta and "!" in texto)
    arrasta = not grito and ("..." in texto or "…" in texto)
    if not grito and not arrasta:
        if not dr_curva and not dp_curva and not dg_curva:
            return v, 0.0
        return ({**v, "rate": _desloca(v.get("rate"), dr_curva, -20, 25, "%"),
                 "pitch": _desloca(v.get("pitch"), dp_curva, -25, 25, "Hz")}, dg_curva)
    dr, dp = (10, 6) if grito else (-8, 0)
    dr += dr_curva
    dp += dp_curva
    novo = {**v, "rate": _desloca(v.get("rate"), dr, -20, 25, "%"),
            "pitch": _desloca(v.get("pitch"), dp, -25, 25, "Hz")}
    return novo, (GANHO_GRITO_DB if grito else 0.0) + dg_curva


def _pos_processar(origem, destino, ganho_db=0.0):
    """Leva o wav do cache pro clip CORTANDO a cauda de silêncio e NIVELANDO a -20 LUFS (+ganho do grito).
    O cache guarda o wav cru de propósito: assim dá pra mudar o nivelamento sem regerar voz nenhuma.
    Ganho fixo medido (não loudnorm dinâmico) pra não bombear em fala de 0,6 s."""
    sem_janela = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(origem), "-af",
                            TRIM_CAUDA + ",ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                           capture_output=True, text=True, timeout=60, encoding="utf-8",
                           errors="replace", creationflags=sem_janela)
        erro = r.stderr or ""
        m = re.search(r"I:\s*(-?[\d.]+) LUFS", erro)
        ganho = ganho_db + (ALVO_LUFS - float(m.group(1)) if m and float(m.group(1)) > -60 else 0.0)
        ganho = max(-12.0, min(12.0, ganho))
        pico = re.search(r"Peak:\s*(-?[\d.]+) dBFS", erro)
        if pico:  # nunca estourar: 1 dB de folga do 0 dBFS
            ganho = min(ganho, -1.0 - float(pico.group(1)))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(origem), "-af",
                        f"{TRIM_CAUDA},volume={ganho:+.1f}dB", "-ar", "24000", "-ac", "1", str(destino)],
                       check=True, timeout=60, creationflags=sem_janela)
        return
    except Exception as e:  # noqa: BLE001
        log(f"  [!] nivelamento da fala falhou ({str(e)[:80]}) — usando o wav cru")
    shutil.copy2(origem, destino)


def _microcortes(wav_path):
    """Dono 22/10: microcortes — toda pausa entre e dentro das falas fica com 0,07 s, a fala NÃO acelera, o
    <wav>.words.json acompanha (narracao_curva.microcortes, comum). LIGADO em toda fala (pt, línguas, 16:9): o dono
    aprovou em 22/10 o teste do cap 14 com o cache (214 s -> 194 s, "não senti diferença"). HIPER_MICROCORTES=0 desliga.
    Falhou = a fala segue como estava."""
    if os.environ.get("HIPER_MICROCORTES", "1") == "0":
        return
    try:
        import narracao_curva
        r = narracao_curva.microcortes(wav_path)
        if r:
            log(f"  [microcortes] {Path(wav_path).name}: {r[0]:.2f}s -> {r[1]:.2f}s")
    except Exception as e:  # noqa: BLE001
        log(f"  [!] microcortes falhou ({str(e)[:80]}) — fala segue sem")


def duracao_clip(texto, dur_voz):
    """Quanto o clip da fala DEVERIA durar: a voz + respiro, mas nunca menos que o tempo de ler o balão.
    PRONTA PRA USO, ainda não ligada: quem decide a duração é o fx_clips.build_clip (ffprobe do wav)."""
    return max(round(float(dur_voz or 0) + 0.4, 2), round(1.2 + 0.06 * len((texto or "").strip()), 2), 1.5)


def _edge_para_wav(texto, v, cache, rotulo=""):
    """Baixa a fala do edge e grava o wav 24k mono do cache. 4 tentativas com espera crescente: o edge
    devolve "No audio was received" de vez em quando (7 falas perdidas no cap 1 th, 2 no cap 2 hi).
    Na última falha avisa o limitador, que é quem segura a fila quando o serviço está ruim."""
    import edge_tts
    mp3 = Path(cache).with_suffix(".mp3")

    async def _baixar():
        """Consome o stream (WordBoundary) pra gravar o áudio E o tempo real de cada palavra no sidecar
        <cache>.words.json (22/10, padrão do comum edge_tts_engine._generate_edge_tts) — é o que dá ênfase e
        ritmo por palavra no narracao_curva.humanizar. Stream sem WordBoundary falha = .save() de sempre."""
        palavras = []
        try:
            com = edge_tts.Communicate(texto, v["voice"], rate=v["rate"], pitch=v["pitch"], boundary="WordBoundary")
            with open(mp3, "wb") as f:
                async for ch in com.stream():
                    if ch.get("type") == "audio":
                        f.write(ch["data"])
                    elif ch.get("type") in ("WordBoundary", "SentenceBoundary"):
                        ini = ch.get("offset", 0) / 1e7  # 100 ns -> s
                        palavras.append([round(ini, 3), round(ini + ch.get("duration", 0) / 1e7, 3), ch.get("text", "")])
        except Exception:  # noqa: BLE001 — Communicate NOVO: reusar o que já fez stream() dá "stream can only be called once"
            palavras = []
            await edge_tts.Communicate(texto, v["voice"], rate=v["rate"], pitch=v["pitch"]).save(str(mp3))
        return palavras

    for tent in range(4):
        try:
            palavras = asyncio.run(_baixar())
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "24000", "-ac", "1", str(cache)],
                           check=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if palavras:
                try:
                    Path(str(cache) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False),
                                                                encoding="utf-8")
                except OSError:
                    pass
            break
        except Exception as e:  # noqa: BLE001
            log(f"  [!] edge {v['voice']} falhou ({tent + 1}/4){f' [{rotulo}]' if rotulo else ''}: {str(e)[:100]}")
            time.sleep(3 * (tent + 1))
        finally:
            mp3.unlink(missing_ok=True)
    try:
        import limitador
        if Path(cache).exists():
            limitador.ok("tts")
        else:
            limitador.falhou("tts", f"edge {v['voice']}: {texto[:40]}")
    except Exception:  # noqa: BLE001
        pass
    return Path(cache).exists()


def _voz_humana(chave):
    """Chave do bloco "voz_humana" de config/fila.json (mesmo bloco que narration.voz_humana lê; aqui de novo
    pra não importar narration dentro do elenco). Env HIPER_HUMANIZAR=1/0 passa por cima (amostras/teste)."""
    env = os.environ.get("HIPER_HUMANIZAR", "").strip()
    if env in ("0", "1") and chave == "humanizar_comum":
        return env == "1"
    try:
        cfg = json.loads((PROJECT_DIR / "config" / "fila.json").read_text(encoding="utf-8"))
        return bool((cfg.get("voz_humana") or {}).get(chave, False))
    except (OSError, ValueError):
        return False


def falar_edge(texto, wav_path, v, rotulo="", obra=None, lang="pt", indice=None, impactos=None, total=None):
    """wav 24 kHz mono com a voz edge v={voice, rate, pitch}; cache por voz+texto. True/False.
    O texto passa por texto_para_voz (sem hangul/rubrica) e pelo dicionário de pronúncia da obra, o
    grito/arrasto entra no rate/pitch, e o wav sai do cache sem a cauda de silêncio e nivelado.
    total = quantas falas tem o capítulo (22/10: o humanizar usa pra dosar a curva)."""
    if v["voice"] in PROIBIDAS:
        raise ValueError(f"voz proibida pelo dono: {v['voice']}")
    bruto = (texto or "").strip()
    falado = texto_para_voz(bruto, lang)
    if not falado:
        log(f"  [som] {rotulo}: fala sem nada pra ler (onomatopeia/rubrica), sem voz: {bruto[:40]}")
        return False
    v, ganho = prosodia(falado, v, indice, impactos)
    falado = aplicar_pronuncia(falado, obra, lang, v["voice"])
    chave = hashlib.sha256(f"edge:{v['voice']}:{v['rate']}:{v['pitch']}:{falado}".encode()).hexdigest()[:16]
    cache = TTS_CACHE / f"{chave}.wav"
    if cache.exists():
        log(f"  TTS[edge]: {rotulo} ({v['voice'].split('-')[2]}) — [CACHE] {falado[:50]}...")
    else:
        if not _edge_para_wav(falado, v, cache, rotulo):
            return False
        log(f"  TTS[edge]: {rotulo} ({v['voice'].split('-')[2]} {v['rate']} {v['pitch']}) — {falado[:50]}...")
    _pos_processar(cache, wav_path, ganho)
    # 22/10 (chave voz_humana.humanizar_comum, desligada até o dono ouvir a amostra): o mesmo humanizar que o
    # dono aprovou no recapd em 20/10 — respiração, pausa antes do impacto, ênfase e ritmo dentro da frase,
    # com o <wav>.words.json (legenda) corrigido junto. Falhou = a fala fica como saiu do _pos_processar.
    if indice is not None and _voz_humana("humanizar_comum"):
        try:
            sidecar = Path(str(cache) + ".words.json")
            if sidecar.exists():
                shutil.copy2(sidecar, str(wav_path) + ".words.json")
            import narracao_curva
            narracao_curva.humanizar(wav_path, falado, indice, impactos,
                                     total if total else (indice + 1))
        except Exception as e:  # noqa: BLE001
            log(f"  [!] humanizar falhou ({str(e)[:80]}) — fala segue sem")
    _microcortes(wav_path)
    return True


def usa_gemini(persona):
    """Esta fala vai pro Gemini no motor atual? (misto: só personagem; narrador fica no edge)."""
    m = motor()
    return m == "gemini" or (m == "misto" and _limpo(persona).lower() not in NARRADOR)


def falar(obra, texto, wav_path, persona, genero, force_tts=False, indice=None, impactos=None, total=None):
    """Fala em português pelo motor configurado, com a voz fixa do personagem na obra.

    indice/impactos: posição desta fala no capítulo e as falas de impacto do editorial — é o que dá
    a CURVA (acelera chegando no clímax, respira depois). Sem eles, a voz sai como antes.
    total: quantas falas tem o capítulo (22/10, dosa o humanizar da voz_humana.humanizar_comum)."""
    v_edge, v_gem = voz(obra, persona, genero)
    if not usa_gemini(persona):
        return falar_edge(texto, wav_path, v_edge, persona or "Narrador", obra=obra,
                          indice=indice, impactos=impactos, total=total)
    from tts_stage import tts_panel
    ok = tts_panel(texto, wav_path, persona=persona or "Narrador", gender=genero, voz=v_gem, force_tts=force_tts)
    if ok:
        _microcortes(wav_path)
    return ok


def trocar_motor(novo):
    """Grava o motor do português em config/fila.json (vale do próximo capítulo em diante)."""
    if novo not in MOTORES:
        raise SystemExit(f"motor inválido: {novo} (use {', '.join(MOTORES)})")
    p = PROJECT_DIR / "config" / "fila.json"
    c = json.loads(p.read_text(encoding="utf-8"))
    c["tts_motor"] = novo
    p.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    return novo


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Voz do português: motor e elenco fixo por obra")
    ap.add_argument("--motor", choices=MOTORES, help="troca o motor (vale do próximo capítulo em diante)")
    a = ap.parse_args()
    if a.motor:
        trocar_motor(a.motor)
    explica = {"edge": "TUDO no edge (rápido, sem limite)",
               "misto": "narrador no edge + personagens no Gemini (voz fixa de cada um)",
               "gemini": "TUDO no Gemini (como era, mais lento)"}
    print(f"Voz do português agora: {motor().upper()} = {explica[motor()]}")
    print("Vale a partir do próximo capítulo que renderizar.")
