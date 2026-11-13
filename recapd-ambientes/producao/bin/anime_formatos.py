# -*- coding: utf-8 -*-
"""anime_formatos.py — Shorts com VÁRIAS vozes (dono 23/10/2026): duplas (João Grilo + Chicó, Chaves + Quico...),
transmissão do Galvão, Show do Milhão, jornal, escolinha, tribunal, participação especial, batalha, fofoca.
Ideias e aprovações: D:\\video-fila\\IDEIAS_FORMATOS_COM_VOZES.md. Formatos/vozes: config\\formatos_voz.json.

DESLIGADO por padrão: só age quando o vídeo tem roteiro_falas.json ao lado do roteiro.txt (quem cria é
reescrever_roteiro, chamado pelo anime_testes ou pela linha de comando). Sem isso, nada muda.

  1. reescrever_roteiro(roteiro.txt, formato): a IA reescreve a história como DIÁLOGO
     [{"voz", "fala", "estilo"}] -> roteiro_falas.json; o roteiro.txt vira uma fala por linha (o original fica em
     roteiro_narrador.txt), então legenda e cortes seguem frase a frase como sempre.
  2. preparar_formato(falas, audio_dir): cada fala na voz de quem fala — um voz_clonada.py lote POR VOZ (o Applio
     carrega 1x por voz), base Kokoro (homem) ou edge Francisca (mulher/criança), entonação pelo estilo.
  3. anime_segments chama o 2 no lugar do preparar_clone; os microcortes do Short seguem valendo (_fala_do_short).
     Fala que é só um bordão com trecho original em trechos_icones\\<voz>\\trechos.json sai com o áudio REAL
     (_trecho_original, 23/10; FORMATO_TRECHO_ORIGINAL=0 desliga). Sem trecho cadastrado, nada muda.

  python anime_formatos.py roteiro <pasta_do_video> <formato>     # só cria o roteiro_falas.json (teste)
  python anime_formatos.py lista
Na produção (23/10) quem decide o formato do Short é o teste gradual (anime_testes.py, chamado pelo anime_auto).
Falta (próximo passo): legenda com a cor/nome de quem fala, cameo com áudio ORIGINAL.
"""
import difflib
import json
import logging
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

BIN = Path(__file__).resolve().parent
CONFIG = BIN.parent / "config" / "formatos_voz.json"
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
VOZES_PY = Path(r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe")
VOZ_CLONADA_PY = Path(r"D:\hipercool-materiais\bin\voz_clonada.py")
FRANCISCA = "pt-BR-FranciscaNeural"


def config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def falas_do_video(pasta):
    """[{"voz","fala","estilo"}] se o vídeo é de formato (roteiro_falas.json na pasta), senão None."""
    arq = Path(pasta) / "roteiro_falas.json"
    if not arq.exists():
        return None
    try:
        return json.loads(arq.read_text(encoding="utf-8"))["falas"]
    except (OSError, ValueError, KeyError) as e:
        logging.warning(f"[formato] roteiro_falas.json ilegível ({e}) — vídeo segue no modo normal")
        return None


_PALETA = ["#FF9628", "#50BEFF", "#FF6EBE", "#6EE66E", "#BE8CFF", "#FFD63C"]  # sobra quando a voz não tem cor


def _rgb(hexa):
    h = str(hexa).strip().lstrip("#")
    return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4)) if len(h) == 6 else None


def falantes_legenda(falas, impactos=None):
    """23/10: quem fala cada linha, pra legenda: [(cor_rgb, nome, extra)] alinhado às falas, ou None (= legenda normal).
    Só com 2+ vozes no vídeo (formato de uma voz só, ex. Galvão, fica igual ao solo). Cor de config/formatos_voz.json
    (vozes.<voz>.cor_legenda "#RRGGBB"); duas vozes com a mesma cor = a 2ª pega a próxima livre da paleta.
    extra (dona 23/10, "ênfase de tamanho nas palavras" e "palavra muito chave por um segundo na tela quase toda"):
    ver _enfase_e_impacto; desligável em formatos_voz.json "legenda"."""
    vozes = list(dict.fromkeys(x["voz"] for x in falas))
    if len(vozes) < 2:
        return None
    todo = config()
    cfg = todo.get("vozes", {})
    cores, usadas = {}, set()
    for v in vozes:
        c = _rgb(cfg.get(v, {}).get("cor_legenda") or "")
        if c is None or c in usadas:
            c = next((p for p in map(_rgb, _PALETA) if p not in usadas), c or (255, 214, 60))
        cores[v] = c
        usadas.add(c)
    try:
        extras = _enfase_e_impacto([x["fala"] for x in falas], impactos, todo.get("legenda") or {})
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[formato] ênfase/impacto da legenda indisponível ({type(e).__name__}: {e}) — só cor/nome")
        extras = [{} for _ in falas]
    return [(cores[x["voz"]], str(cfg.get(x["voz"], {}).get("nome_legenda") or "").strip(), ex)
            for x, ex in zip(falas, extras)]


def enfase_solo(linhas, impactos=None):
    """27/10: ênfase/impacto para Shorts SOLO (1 voz) — mesma seleção de palavras, cor amarela de karaokê, sem nome."""
    todo = config()
    try:
        extras = _enfase_e_impacto(linhas, impactos, todo.get("legenda") or {})
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[formato] ênfase/impacto solo indisponível ({type(e).__name__}: {e})")
        return None
    cor = (255, 214, 60)
    if (todo.get("legenda") or {}).get("cor_por_personagem", True):
        try:
            for ex, cores in zip(extras, _cores_dos_nomes(linhas)):
                if cores:
                    ex["cores"] = cores
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[formato] cor por personagem indisponível ({type(e).__name__}: {e})")
    return [(cor, "", ex) for ex in extras]


# 28/10 (dona 27/10: "cor por personagem"): o Short solo é 1 voz e o roteiro não marca falas, então quem ganha cor é o
# NOME de cada personagem (a mesma cor o vídeo inteiro): maiúscula fora do começo de frase, repetida ou >= 4 letras.
_CORES_NOMES = [(80, 190, 255), (255, 110, 190), (110, 230, 110), (190, 140, 255)]  # amarelo é o karaokê
_NAO_NOME = set("""Eu Ele Ela Eles Elas Você Vocês Mas Então Quando Depois Aí Só Isso Esse Essa Aquele Aquela Meu Minha
Seu Sua Nosso Nossa Deus Brasil Francamente Gente Cara Mano Não Sim Porque Como Onde Nunca Sempre Hoje Ontem Agora""".split())


def _cores_dos_nomes(linhas):
    from fx_subtitles import _strip_lead_punct
    palavras = [[w for w in (_strip_lead_punct(x) for x in str(t or "").split()) if w] for t in linhas]
    conta = {}
    for ws in palavras:
        for j, w in enumerate(ws):
            nome = re.sub(r"[^\wÀ-ÿ]", "", w)
            inicio = j == 0 or ws[j - 1][-1:] in ".!?:"
            if (len(nome) >= 3 and nome[0].isupper() and not nome.isupper() and not inicio
                    and nome not in _NAO_NOME):
                conta[nome] = conta.get(nome, 0) + 1
    nomes = [n for n, c in sorted(conta.items(), key=lambda x: -x[1]) if c >= 2 or len(n) >= 4][:len(_CORES_NOMES)]
    cor_de = {n: _CORES_NOMES[k] for k, n in enumerate(nomes)}
    out = []
    for ws in palavras:
        out.append({j: cor_de[re.sub(r"[^\wÀ-ÿ]", "", w)] for j, w in enumerate(ws)
                    if re.sub(r"[^\wÀ-ÿ]", "", w) in cor_de})
    return out


_STOP = set("""a o as os um uma uns umas de da do das dos em na no nas nos por pra pro pras pros para com sem que se
e ou mas mais muito muita ele ela eles elas eu tu voce voces nos me te lhe isso isto aquilo esse essa este esta
aquele aquela seu sua seus suas meu minha teu tua ja nao sim foi era ser ter tem tinha tava esta estava aqui ali
la entao quando como onde porque pois ate tambem so bem tao the of and""".split())
_NUMEROS = set("dois duas tres quatro cinco seis sete oito nove dez onze doze vinte trinta cem cento duzentos "
               "trezentos mil milhao milhoes bilhao bilhoes".split())
_FORTES = set("horrivel gigante enorme louco loucura mortal impossivel maior melhor pior monstro fogo sangue "
              "inteirinho todinho nunca jamais sumiu sumiram morreu explodiu".split())
_VERBO_ACAO = re.compile(r"^\w{3,}(ou|eu|iu|aram|eram|iram)$")  # pingou, bateu, sumiu, arrastaram: verbo de ação


def _nota_palavra(w, anterior, gatilho):
    """Quanto a palavra pesa na fala: número, palavra de virada (o mesmo gatilho do narracao_curva), nome próprio,
    exclamação, CAIXA ALTA. Palavra curta/de ligação = 0."""
    nucleo = re.sub(r"[^\w]+$", "", w)
    chave = "".join(_sem_acento(nucleo))
    if not chave or chave in _STOP or (len(chave) < 3 and not chave.isdigit()):
        return 0.0
    s = 3.0 if (any(c.isdigit() for c in chave) or chave in _NUMEROS) else 0.0
    s += 2.0 if gatilho and gatilho.match(nucleo) else 0.0
    s += 1.5 if chave in _FORTES else 0.0
    s += 1.0 if _VERBO_ACAO.match(chave) else 0.0
    if nucleo[:1].isupper() and anterior is not None and not anterior.endswith((".", "!", "?", "…", ":")):
        s += 1.5  # nome no meio da frase
    s += 1.0 if w.endswith("!") else 0.0
    s += 1.0 if len(nucleo) >= 3 and nucleo.isupper() else 0.0
    return s + min(len(chave), 10) / 20


def _enfase_e_impacto(linhas, impactos, cfg):
    """[{enfase: [índices das palavras MAIORES], impacto: [índice, nota] | None, escala, imp_max, imp_intervalo}]
    alinhado às linhas. Índice = posição na lista de palavras que a legenda usa (split + _strip_lead_punct).
    Ênfase: até 2 palavras por fala com nota >= 1.5 (número, virada, nome, palavra forte, verbo de ação, "!").
    Impacto: só nas frases de impacto que o narracao_curva já escolheu pra curva da voz (_impactos.json: LLM 1x por
    vídeo, senão a heurística dele) — sem chamada nova; nunca a 1ª fala (o gancho já está na tela); dentro da frase,
    a palavra de maior nota. Quantos e o intervalo mínimo a legenda decide pelo tempo."""
    from fx_subtitles import _strip_lead_punct
    gatilho = None
    try:
        import narracao_curva
        gatilho = narracao_curva._GATILHO
        if not impactos:
            impactos = narracao_curva._heuristica(linhas, narracao_curva._quantos(len(linhas)))
    except Exception as e:  # noqa: BLE001
        logging.info(f"[formato] narracao_curva indisponível pra ênfase ({type(e).__name__}) — só números/nomes")
    enf_ok, imp_ok = cfg.get("enfase_ligada", True), cfg.get("impacto_ligado", True)
    comum = {"escala": float(cfg.get("enfase_escala", 1.3)), "imp_max": int(cfg.get("max_impactos_por_video", 2)),
             "imp_intervalo": float(cfg.get("impacto_intervalo_min_s", 8))}
    out = []
    for i, t in enumerate(linhas):
        ws = [w for w in (_strip_lead_punct(x) for x in str(t or "").split()) if w]
        notas = [(_nota_palavra(w, ws[j - 1] if j else None, gatilho), j) for j, w in enumerate(ws)]
        fortes = sorted([n for n in notas if n[0] >= 1.5], reverse=True)
        imp = None
        if imp_ok and i > 0 and i in set(impactos or []) and notas:
            n, j = max(notas)
            imp = [j, round(n, 2)] if n > 0.5 else None
        enf = sorted({j for _n, j in fortes[:2]} | ({imp[0]} if imp else set())) if enf_ok else []
        out.append(dict(comum, enfase=enf, impacto=imp))
    return out


def _bordoes(voz):
    try:
        g = json.loads((VOZES / voz / "linguagem_v2.json").read_text(encoding="utf-8"))
        fora = {x.lower() for x in g.get("bordoes_estranhos") or []}
        evitar = [str(x) for x in g.get("evitar") or []][:3]
        # dona 23/10 ("um bordão basta pra identificar"): UM só — com 2 opções a IA usava as duas (ensaio 23/10)
        return [x for x in (g.get("bordoes_iconicos") or g.get("bordoes") or []) if x.lower() not in fora][:1], evitar
    except (OSError, ValueError):
        return [], []


def _sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def _voz_do_elenco(nome, elenco):
    """A IA escreve "Chicó", "chico", "Chaves" em vez da chave: acha a voz do elenco (só se for uma só), senão None."""
    n = "_".join(_sem_acento(nome))
    if n in elenco:
        return n
    achou = [v for v in elenco if n and (v.startswith(n) or n in v.split("_") or n.startswith(v))]
    return achou[0] if len(achou) == 1 else None


_COMUNS = {"voce", "nao", "olha", "que", "isso", "diz", "pra", "ele", "deixe", "sabe", "quem", "bem", "num", "sei",
           "cala", "foi", "uii", "ei", "ma", "mah", "aqui", "esta", "certo"}


def _palavras_bordao(t):
    """Palavras sem acento, repetição seguida junta ("Gentalha, gentalha!" = "gentalha"), menos o "isso, isso, isso"."""
    out = []
    for w in _sem_acento(t):
        if out and out[-1] == w and w != "isso":
            continue
        out.append(w)
    return out


def _chave(b):
    """Pedaço que identifica o bordão na fala: a 1ª palavra se ela for rara ("gentalha", "silencio", "errou"), senão
    as 3 primeiras ("voce nao vai", "foi sem querer"). Revisão 23/10: "você não" e "olha o" sozinhos são fala comum."""
    p = _palavras_bordao(b)
    if not p:
        return None
    if len(p) == 1 or (len(p[0]) >= 5 and p[0] not in _COMUNS):
        return p[0]
    return " ".join(p[:3])


def _lista_bordoes(voz, cfg):
    """Bordões da voz: linguagem_v2 (sem os que soam estranhos) e depois os "bordoes" do formatos_voz.json."""
    try:
        g = json.loads((VOZES / voz / "linguagem_v2.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        g = {}
    fora = {x.lower() for x in g.get("bordoes_estranhos") or []}
    out = []
    for b in (g.get("bordoes_iconicos") or []) + (g.get("bordoes") or []) + (cfg["vozes"].get(voz, {}).get("bordoes") or []):
        if b and b.lower() not in fora and b not in out:
            out.append(b)
    return out


def _chaves_bordao(voz, cfg):
    return {k for k in (_chave(b) for b in _lista_bordoes(voz, cfg)) if k and len(k) >= 4}


def _donos(elenco, cfg):
    d = {}
    for v in elenco:
        for k in _chaves_bordao(v, cfg):
            d.setdefault(k, set()).add(v)
    return d


def _tem(k, texto_norm):
    return f" {k} " in f" {texto_norm} "  # palavra inteira: "errou" não casa em "ferrou"


def _bordao_do_prompt(voz, elenco, cfg):
    """O bordão que a IA recebe pra esta voz: o 1º que é SÓ dela no elenco (revisão 23/10: Chaves e Chiquinha recebiam
    os dois o "Isso, isso, isso!" e o bordão deixava de dizer quem fala)."""
    donos = _donos(elenco, cfg)
    lista = _lista_bordoes(voz, cfg)
    for b in lista:
        if donos.get(_chave(b), {voz}) == {voz}:
            return b
    return lista[0] if lista else None


def _excesso_bordoes(falas, elenco, cfg):
    """Dona 23/10: UM bordão por personagem no vídeo inteiro, e o DELE. {voz: vezes} de quem passou disso; bordão de
    outro personagem conta como excesso (ensaio 23/10: a Chiquinha falou o "Gentalha!" do Quico)."""
    donos = _donos(elenco, cfg)
    vezes = {}
    for x in falas:
        t = " ".join(_palavras_bordao(x["fala"]))
        for k, quem in donos.items():
            n = f" {t} ".count(f" {k} ")
            if n:
                vezes[x["voz"]] = vezes.get(x["voz"], 0) + (n if x["voz"] in quem else n + 1)
    return {v: n for v, n in vezes.items() if n > 1}


_INTERJ = {"hmp", "ei", "uii", "ui", "ai", "oh", "ah", "eh", "ue", "oxe", "vixe", "hum"}


def _tirar_bordoes_demais(falas, elenco, cfg):
    """A IA insiste em encher os personagens do Chaves de bordão (ensaio 23/10: 2-4 cada mesmo pedindo de novo). Fica
    o 1º bordão PRÓPRIO de cada voz; frase que é só outro bordão (ou o de outro personagem) sai, junto com a interjeição
    que sobra dele ("Hmp!"). Bordão no meio de uma frase longa fica (cortar mudaria o sentido). Fala com menos de 2
    palavras de verdade depois do corte (vazia ou só "Hmp!") volta ao que era."""
    donos = _donos(elenco, cfg)
    usou = set()
    for x in falas:
        partes = [p for p in re.split(r"(?<=[.!?…])\s+", x["fala"]) if p.strip()]
        juntas = []  # bordão com pontuação dentro ("Ei! Ei! Isso não é justo!"): junta as partes que ele atravessa
        for p in partes:
            t_par = " ".join(_palavras_bordao(p))
            for atras in (2, 1):
                if len(juntas) < atras:
                    continue
                antes = " ".join(juntas[-atras:])
                t_ant, t_jun = " ".join(_palavras_bordao(antes)), " ".join(_palavras_bordao(antes + " " + p))
                if any(_tem(k, t_jun) and not _tem(k, t_ant) and not _tem(k, t_par) for k in donos):
                    juntas[-atras:] = [antes + " " + p]
                    break
            else:
                juntas.append(p)
        novas, cortou = [], False
        for p in juntas:
            t = " ".join(_palavras_bordao(p))
            ks = [k for k in donos if _tem(k, t)]
            if not ks:
                if cortou and t in _INTERJ:  # o "Hmp!" que sobrou do bordão cortado
                    continue
                novas.append(p)
                cortou = False
                continue
            proprio = all(x["voz"] in donos[k] for k in ks)
            if proprio and x["voz"] not in usou:
                usou.add(x["voz"])
                novas.append(p)
                cortou = False
            elif len(t.split()) > max(len(k.split()) for k in ks) + 3:  # frase de verdade com o bordão dentro
                novas.append(p)
                cortou = False
            else:
                cortou = True
        sobra = [w for w in _palavras_bordao(" ".join(novas)) if w not in _INTERJ]
        if novas != partes and sobra:  # nunca deixa a fala vazia nem só com interjeição
            x["fala"] = " ".join(novas)
    return falas


# palavrão que o anti-ban (viralizador) não troca e a IA do formato às vezes solta (ensaio 23/10: "nem fudendo"). O que
# já estava na história do solo não conta (revisão 23/10: "Akira Fudo", "arrombou a porta")
_PALAVRAO = re.compile(r"\b(fud(?:e|er|eu|endo|ido|ida)s?\b|fod[aeiã]\w*|porr[ao]s?\b|caralh\w*|merd\w*|put[ao]s?\b|"
                       r"putaria|cacet[ea]s?\b|bost[ao]s?\b|buceta|cuz[aã]o|arrombad[oa]s?\b|viad[ao]s?\b)", re.I)


def reescrever_roteiro(roteiro_txt, formato):
    """Roteiro do narrador -> diálogo do formato. Grava roteiro_falas.json e troca o roteiro.txt (original salvo).
    Até 3 tentativas: vale a que tem todo o elenco falando, nenhuma fala perdida e menos bordão repetido."""
    import anime_script
    import anime_tts
    import claude_client
    cfg = config()
    f = cfg["formatos"][formato]
    elenco = list(f["elenco"])
    roteiro_txt = Path(roteiro_txt)
    narr = roteiro_txt.parent / "roteiro_narrador.txt"
    # 2ª rodada na mesma pasta (linha de comando): a história é a do narrador, não o diálogo da rodada anterior
    historia = narr.read_text(encoding="utf-8") if narr.exists() and (roteiro_txt.parent / "roteiro_falas.json").exists() \
        else roteiro_txt.read_text(encoding="utf-8")
    palavras = len(historia.split())
    ja_na_historia = {w.lower() for w in re.findall(r"\w+", historia)}
    linhas = []
    for v in elenco:
        ev = _bordoes(v)[1]
        b = _bordao_do_prompt(v, elenco, cfg)
        linhas.append(f"- {v}" + (f" (bordão dele, UMA vez só no vídeo: {b})" if b else "")
                      + (f" (NÃO: {'; '.join(ev)})" if ev else ""))
    # 23/10 (revisão): o tamanho segue a história do solo (já calibrada pela duração do original), não um fixo de 40-60 s
    prompt = (f"FORMATO: {f['nome']}\n{f['como']}\n\nELENCO (use exatamente estes nomes em \"voz\"):\n" + "\n".join(linhas)
              + f"\n\n{cfg['regras']}\n\nTAMANHO: cerca de {palavras} palavras no total (o mesmo da história)."
              + f"\n\nHISTÓRIA:\n{historia}")
    melhor, nota_melhor, aviso = None, None, ""
    for tentativa in range(3):
        resp = claude_client.generate_text(prompt + aviso, max_tokens=2500, temperature=0.7, timeout=240) or ""
        m = re.search(r"\[.*\]", resp, re.S)
        try:
            brutas = [x for x in json.loads(m.group(0)) if isinstance(x, dict) and str(x.get("fala", "")).strip()]
        except (AttributeError, ValueError):
            brutas = []
        falas = []
        for x in brutas:
            voz = _voz_do_elenco(x.get("voz"), elenco)
            if voz:
                # 1 fala = 1 linha (quebra de linha desalinharia fala x voz) e o MESMO anti-ban do solo: a legenda
                # queimada e o gancho saem deste texto, o áudio também (revisão 23/10: legenda "sangue", voz "suco")
                falas.append({**x, "voz": voz, "fala": anime_tts._seguro(re.sub(r"\s+", " ", str(x["fala"])).strip())})
        perdidas = len(brutas) - len(falas)
        faltam = [v for v in elenco if v not in {x["voz"] for x in falas}]
        falas = _tirar_bordoes_demais(falas, elenco, cfg)
        excesso = _excesso_bordoes(falas, elenco, cfg)
        palavrao = sorted({m.group(0) for x in falas for m in _PALAVRAO.finditer(x["fala"])
                           if m.group(0).lower() not in ja_na_historia})
        # erro/recusa da IA nunca pode virar fala de personagem (mesma trava do anime_script, 23/10)
        ok = (len(falas) >= 3 and not perdidas and not faltam and not palavrao
              and not any(anime_script.resposta_de_erro(x["fala"]) for x in falas))
        nota = sum(n - 1 for n in excesso.values())
        if ok and (nota_melhor is None or nota < nota_melhor):
            melhor, nota_melhor = falas, nota
        if ok and not nota:
            break
        logging.warning(f"[formato] roteiro {formato} tentativa {tentativa + 1}: {len(falas)} falas, perdidas {perdidas}, "
                        f"sem fala {faltam}, bordão repetido/trocado {excesso}, palavrão {palavrao}"
                        + (" — de novo" if tentativa < 2 else ""))
        aviso = ("\n\nATENÇÃO, a tentativa anterior errou: "
                 + (f"use SÓ estes nomes em \"voz\": {', '.join(elenco)}. " if perdidas else "")
                 + (f"todos do elenco têm de falar ({', '.join(faltam)} ficou sem fala). " if faltam else "")
                 + (f"NADA de palavrão ({', '.join(palavrao)}). " if palavrao else "")
                 + ("".join(f"{v} usou bordão {n} vezes (ou o bordão de outro); " for v, n in excesso.items())
                    + "cada personagem tem UM bordão no vídeo inteiro, o DELE, o resto é fala normal. " if excesso else ""))
    if melhor is None:
        raise RuntimeError(f"[formato] a IA não devolveu o diálogo do formato {formato}")
    falas = melhor
    pasta = roteiro_txt.parent
    if not narr.exists():  # o anime_auto apaga o de outra rodada antes do roteiro
        narr.write_text(historia, encoding="utf-8")
    (pasta / "roteiro_falas.json").write_text(json.dumps(
        {"formato": formato, "nome": f["nome"], "gerado": time.strftime("%d/%m %H:%M"), "falas": falas},
        ensure_ascii=False, indent=1), encoding="utf-8")
    roteiro_txt.write_text("\n".join(x["fala"].strip() for x in falas) + "\n", encoding="utf-8")
    logging.info(f"[formato] {f['nome']}: {len(falas)} falas ({', '.join(sorted({x['voz'] for x in falas}))})")
    return falas


def aplicar_efeito_voz(voz, wav):
    """Efeito próprio da voz, gravado no cadastro dela (personagem.json "efeito_ffmpeg"), ex.: a Aracy da Top Therm é
    conhecida pela voz de velha falhando = tremido (dono 23/10). Sem efeito ou falhou = o wav fica como veio."""
    try:
        efeito = json.loads((VOZES / voz / "personagem.json").read_text(encoding="utf-8")).get("efeito_ffmpeg")
    except (OSError, ValueError):
        return
    if not efeito:
        return
    wav = Path(wav)
    tmp = wav.with_name(wav.stem + ".efeito.wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", efeito, str(tmp)], check=True, timeout=60,
                       creationflags=0x08000000)
        tmp.replace(wav)
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        logging.warning(f"[voz] efeito de {voz} não entrou ({str(e)[:80]})")


TRECHOS = Path(r"D:\hipercool-materiais\amostras_voz\trechos_icones")  # o mesmo do anime_tts (abertura do solo)


def _trecho_original(voz, fala, out):
    """Dona 23/10 ("pode até deixar baixado o original de algumas quando for algo muito característico"): fala que é
    (quase) SÓ um bordão com trecho original em trechos_icones\\<voz>\\trechos.json (ou no da voz de que o modelo veio,
    personagem.json "modelo_de") sai com o áudio REAL no lugar da voz clonada. Grava out + words.json (as palavras da
    fala no tempo do trecho, pra legenda). Sem trecho / fala com mais conteúdo / falhou = None (segue clonada)."""
    if os.environ.get("FORMATO_TRECHO_ORIGINAL", "1") == "0":
        return None
    palavras = [w for w in _palavras_bordao(fala) if w not in _INTERJ]
    if not palavras:
        return None
    try:
        de = json.loads((VOZES / voz / "personagem.json").read_text(encoding="utf-8")).get("modelo_de")
    except (OSError, ValueError):
        de = None
    for v in [voz] + ([de] if de and de != voz else []):
        try:
            lista = json.loads((TRECHOS / v / "trechos.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for t in lista or []:
            alvo = str(t.get("alvo") or t.get("frase") or "")
            if alvo.startswith("("):  # "(som)", "(vídeo inteiro)": não dá pra saber se é a fala
                continue
            a = [w for w in _palavras_bordao(alvo) if w not in _INTERJ]
            if not a or abs(len(a) - len(palavras)) > 1 or \
                    difflib.SequenceMatcher(None, " ".join(palavras), " ".join(a)).ratio() < 0.85:
                continue
            src = TRECHOS / v / t["arquivo"]
            try:
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ar", "44100", "-ac", "2", str(out)],
                               check=True, capture_output=True, timeout=60, creationflags=0x08000000)
                r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(out)], capture_output=True, text=True, timeout=30, creationflags=0x08000000)
                dur = float(r.stdout.strip())
                if not 0.4 <= dur <= 8:
                    raise ValueError(f"{dur:.1f}s")
                # tempo de cada palavra proporcional ao tamanho dela no trecho (o mesmo formato do words.json do edge)
                ws = re.findall(r"\w+(?:[-']\w+)*", fala)
                tot, ini, fim, acc, wj = sum(len(w) + 1 for w in ws), 0.05, max(0.1, dur - 0.1), 0, []
                for w in ws:
                    a0 = ini + (fim - ini) * acc / tot
                    acc += len(w) + 1
                    wj.append([round(a0, 3), round(ini + (fim - ini) * acc / tot, 3), w])
                Path(str(out) + ".words.json").write_text(json.dumps(wj, ensure_ascii=False), encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                Path(out).unlink(missing_ok=True)
                logging.warning(f"[formato] trecho original de {v} não entrou ({str(e)[:80]}) — voz clonada")
                return None
            logging.info(f"[formato] fala '{fala[:50]}' com o áudio ORIGINAL de {v} ({t['arquivo']}, {dur:.1f}s)")
            return t
    return None


def _esperar_ram():
    try:
        import psutil
        t0 = time.time()
        while psutil.virtual_memory().available < 3 * 1024 ** 3 and time.time() - t0 < 45 * 60:
            logging.info(f"[formato] RAM baixa ({psutil.virtual_memory().available / 1024 ** 3:.1f} GB) — esperando 60 s")
            time.sleep(60)
    except ImportError:
        pass


def preparar_formato(falas, audio_dir):
    """Cada fala vira audio_<i>.wav na voz de quem fala. Falhou = levanta (vídeo com voz faltando não sai)."""
    import anime_tts
    import edge_tts_engine
    import narracao_curva
    cfg = config()
    audio_dir = Path(audio_dir)
    bases = audio_dir / "_base_formato"
    bases.mkdir(parents=True, exist_ok=True)
    por_voz, depois = {}, []
    for i, x in enumerate(falas):
        out = audio_dir / f"audio_{i}.wav"
        if out.exists() and out.stat().st_size > 500:
            continue
        voz = x["voz"]
        if _trecho_original(voz, x["fala"], out):  # bordão com o áudio real: nivela igual, sem o efeito da voz clonada
            depois.append((out, None, None))
            continue
        pv = cfg["vozes"].get(voz, {"base": "K", "st": 0})
        es = cfg["estilos"].get(x.get("estilo", "normal"), cfg["estilos"]["normal"])
        extra = {"tom_extra": int(pv["st"]) + int(es["st"]), "f0_escala": es["f0_escala"], "final_st": es["final_st"],
                 "index_rate": 0.7}
        texto = anime_tts._seguro(x["fala"].strip())  # o mesmo anti-ban/romanos do clone solo
        sidecar = None
        if pv["base"] == "K":
            item = {"saida": str(out), "tom_base": "1_kokoro", "texto": texto, "velocidade": es["velocidade"], **extra}
        else:
            bruto = bases / f"audio_{i}.wav"
            rate = f"{int(round((es['velocidade'] - 1) * 100)):+d}%"
            # o edge_tts_engine troca a Francisca pela Thalita fora da voz clonada (sem VOZ_CLONADA no env): aqui ela é
            # a base do clone, calibrada pra Francisca (revisão 23/10: a Chiquinha saía da Thalita)
            antes = os.environ.get("VOZ_CLONADA")
            os.environ["VOZ_CLONADA"] = voz
            try:
                ok = edge_tts_engine.speak(texto, voice=FRANCISCA, out_wav=str(bruto), persona="Narrador", rate=rate)
            finally:
                if antes is None:
                    os.environ.pop("VOZ_CLONADA", None)
                else:
                    os.environ["VOZ_CLONADA"] = antes
            if not ok:
                raise RuntimeError(f"[formato] edge falhou na fala {i}")
            item = {"saida": str(out), "tom_base": "2_edge_francisca", "entrada": str(bruto), **extra}
            sidecar = Path(str(bruto) + ".words.json")
        por_voz.setdefault(voz, []).append(item)
        depois.append((out, sidecar, voz))
    for voz, itens in por_voz.items():
        lista = bases / f"lista_{voz}.json"
        lista.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        _esperar_ram()
        for tentativa in (1, 2):
            with open(bases / "formato.log", "a", encoding="utf-8") as fh:
                r = subprocess.run([str(VOZES_PY), str(VOZ_CLONADA_PY), "lote", voz, str(lista)], stdout=fh,
                                   stderr=subprocess.STDOUT, timeout=4 * 3600, creationflags=0x00000020 | 0x08000000)
            faltam = [i["saida"] for i in itens if not Path(i["saida"]).exists()]
            if r.returncode == 0 and not faltam:
                break
            if tentativa == 1:
                logging.warning(f"[formato] lote {voz} rc={r.returncode}, faltam {len(faltam)} — nova tentativa em 90 s")
                time.sleep(90)
        if r.returncode != 0 or faltam:
            raise RuntimeError(f"[formato] lote {voz} falhou (ver {bases / 'formato.log'})")
        logging.info(f"[formato] {len(itens)} falas com a voz de {voz}")
    for out, sidecar, voz in depois:
        if sidecar and sidecar.exists():
            sidecar.replace(Path(str(out) + ".words.json"))
        narracao_curva.pos_processar(out, 0.0, 0.05)
        if voz:
            aplicar_efeito_voz(voz, out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.path.insert(0, str(BIN))
    if len(sys.argv) < 2 or sys.argv[1] == "lista":
        for k, f in config()["formatos"].items():
            print(f"{k:20s} {f['nome']}  ({', '.join(f['elenco'])})")
    elif sys.argv[1] == "roteiro":
        falas = reescrever_roteiro(Path(sys.argv[2]) / "roteiro.txt", sys.argv[3])
        for x in falas:
            print(f"{x['voz']:20s} [{x.get('estilo', 'normal')}] {x['fala']}")
