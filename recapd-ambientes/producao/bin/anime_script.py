"""anime_script.py — transforma a transcrição crua num roteiro PT-BR próprio.

Módulo isolado. Pega o texto CRU da transcrição (qualquer língua, longo) e
produz um roteiro de narração em PT-BR:
  - REESCRITO com voz própria (não é tradução literal do recap alheio).
  - CONDENSADO (o recap nosso é bem mais curto que o original).
  - 1 frase por linha (cada linha vira um clipe/narração no pipeline).
  - PROTECAO ANTI-BAN: termos que dao strike no YouTube sao suavizados
    (viralizador.anti_ban). Gírias virais opcionais via VIRAL_SLANG=1.

Usa claude_client.generate_text (o proxy/gateway já configurado no projeto).
Processa a transcrição em BLOCOS pra não estourar o contexto do modelo.
"""
import hashlib
import json
import logging
import os
import random
import re
import sys
from pathlib import Path

# viralizador.py vive no mesmo diretório — garante que o import funcione
sys.path.insert(0, str(Path(__file__).resolve().parent))

import claude_client
import viralizador

# ── Fila/cache de roteiro (reaproveita gerações do LLM) ──────────────────
# Cada roteiro gerado pelo LLM é caro (várias chamadas por vídeo). Se o render
# falhar depois, sem cache o roteiro seria REFEITO do zero na próxima rodada,
# queimando chamadas de novo. Aqui guardamos o roteiro por chave = hash da
# transcrição + target_lines + versão do prompt. O cache vive em
# workspace/roteiro_cache/ — que é junction compartilhado pelos 3 ambientes
# (producao/beta/experimental), então um gera e os outros reaproveitam.
_CACHE_DIR = Path(__file__).resolve().parent.parent / "workspace" / "roteiro_cache"
# Bump quando _SYSTEM/regras mudarem, pra invalidar roteiros velhos.
# v2: prompt de bloco pede FIDELIDADE (não condensar) + removido corte global
#     roteiro[:target_lines]. Invalida roteiros curtos gerados na v1.
# v3 (19/10): jeito de falar dos narradores BR medidos pelo hipercool (_jeito_do_nicho).
# v5 (21/10): 1ª frase com fato (não só apresentação), sem bordão depois do trecho real, nichos com o nome certo.
_PROMPT_VERSION = "v17"  # 04/11: sem cara de IA (lista de clichês). v16 04/11: continuidade entre blocos (3 últimas frases) + sem trava de tamanho. v15 # 01/11 noite: L-09 narrador "parça" + L-07 vitória cedo + 2 comentários por trecho  # 01/11: comentário pessoal/ironia do narrador por trecho no longo + concordância da 1ª pessoa feminina. v12 28/10: + tom de desabafo informal na 1ª pessoa (aprendizado 5a106596). v11 (26/10): dorama/filme
# em 1ª pessoa, sem "prota" nem bordão/abertura/tirada do narrador
# (v7)  # 22/10: personagem narra o vídeo INTEIRO como ele (persona v2: bordões reais + manias)
# (v6)  # 22/10: regras de ORALIDADE (contrações, pergunta retórica, sem conectivo de redação, sem letra esticada)


def _cache_key(transcript, target_lines):
    h = hashlib.sha256()
    h.update(_PROMPT_VERSION.encode("utf-8"))
    if _narrador_v2():  # roteiro no jeito do narrador (clone 2.0): um por narrador
        h.update(f"\x00narrador={_narrador_v2()}".encode("utf-8"))
    h.update(b"\x00")
    h.update(str(target_lines).encode("utf-8"))
    h.update(b"\x00")
    h.update(transcript.encode("utf-8", errors="replace"))
    return h.hexdigest()[:32]


def _cache_get(transcript, target_lines):
    if os.environ.get("ROTEIRO_CACHE", "1") == "0":
        return None
    f = _CACHE_DIR / f"{_cache_key(transcript, target_lines)}.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        linhas = data.get("roteiro") or []
        if any(resposta_de_erro(l) for l in linhas):  # 23/10: erro/recusa da IA guardado como roteiro — não reusa
            logging.warning(f"[script] cache {f.name} tinha ERRO/RECUSA da IA — descartado")
            f.unlink(missing_ok=True)
            return None
        if linhas:
            logging.info(f"[script] CACHE HIT — reaproveitando roteiro ({len(linhas)} "
                         f"frases), sem chamar o LLM. ({f.name})")
            return linhas
    except Exception as e:
        logging.warning(f"[script] cache corrompido ({f.name}): {e} — regerando")
    return None


def _cache_put(transcript, target_lines, linhas):
    if os.environ.get("ROTEIRO_CACHE", "1") == "0" or not linhas:
        return
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        f = _CACHE_DIR / f"{_cache_key(transcript, target_lines)}.json"
        f.write_text(json.dumps({
            "prompt_version": _PROMPT_VERSION,
            "target_lines": target_lines,
            "n_frases": len(linhas),
            "roteiro": linhas,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        logging.info(f"[script] roteiro salvo no cache ({f.name}) — próxima rodada reaproveita.")
    except Exception as e:
        logging.warning(f"[script] falha ao salvar cache: {e}")

# nomes = PARCEIRO_TIPO das fontes (parceiro.json) e nichos dos canais de "fatos" (anime_voz_clonada.nicho_do_video)
_NICHOS_SEM_PROTAGONISTA = {"fatos", "curiosidades", "historia_mitologia", "animais", "esportes", "financas",
                            "pesca", "jogos", "geral"}
# dono 25/10: doramas e filmes narram em 1ª pessoa (protagonista conta a história) e nunca usam "prota"
_NICHOS_PRIMEIRA_PESSOA = {"dorama", "filme_sem_voz"}


_FEM_1P = re.compile(r"\b(obrigada|sozinha|eu mesma|grávida|gravida|(?:eu|que)\s+(?:era|sou|fui)\s+(?:só\s+)?(?:uma|a)\s+"
                     r"(?:garota|mulher|menina|moça|moca|esposa|mãe|mae|filha|princesa|noiva|namorada|secretária|"
                     r"empregada|estudante pobre))\b|\b(?:eu|me)\s+(?:\w+\s+){0,2}?(?:estava|estou|"
                     r"fiquei|fico|sou|era|fui|senti|sinto|sentia|vi|acordei|nasci|cresci)\s+(?:muito\s+|tão\s+|tao\s+)?"
                     r"(\w{3,}a)\b", re.I)
_MASC_1P = re.compile(r"\b(obrigado|sozinho|eu mesmo)\b|\b(?:eu|me)\s+(?:\w+\s+){0,2}?(?:estava|estou|fiquei|fico|sou|era|"
                      r"fui|senti|sinto|sentia|vi|acordei|nasci|cresci)\s+(?:muito\s+|tão\s+|tao\s+)?(\w{3,}o)\b", re.I)
_NAO_ADJ = {"casa", "escola", "festa", "empresa", "cama", "porta", "sala", "rua", "noite", "hora", "vida", "agora",
            "minha", "uma", "nada", "toda", "cada", "embora", "fora", "obra", "tudo", "muito", "pouco", "logo", "isso",
            "disso", "nisso", "como", "quando", "também", "tambem", "assim", "aqui", "ali", "lado", "dentro", "acordo"}


def narradora_feminina(texto):
    """01/11 dona: dorama em 1ª pessoa com protagonista MULHER estava saindo com voz de homem. True quando a
    concordância do 'eu' no roteiro é feminina ('eu estava cansada', 'sozinha', 'obrigada') mais que masculina."""
    f = sum(1 for m in _FEM_1P.finditer(texto) if (m.group(2) or "x").lower() not in _NAO_ADJ)
    mm = sum(1 for m in _MASC_1P.finditer(texto) if (m.group(2) or "x").lower() not in _NAO_ADJ)
    return f >= 2 and f > mm


def primeira_pessoa():
    tipo = os.environ.get("PARCEIRO_TIPO")
    return os.environ.get("NICHO_CLONE", tipo) in _NICHOS_PRIMEIRA_PESSOA or tipo in _NICHOS_PRIMEIRA_PESSOA


def _system():
    tipo = os.environ.get("PARCEIRO_TIPO", "anime")
    nicho = os.environ.get("NICHO_CLONE", tipo)
    if nicho in _NICHOS_SEM_PROTAGONISTA or tipo == "fatos":
        contexto = (
            "Você é roteirista de um canal brasileiro de curiosidades e conteúdo informativo. Recebe a "
            "transcrição CRUA (possivelmente em outra língua) de um vídeo já existente e reescreve com "
            "VOZ PRÓPRIA e ORIGINAL em português brasileiro — NUNCA traduz literalmente nem copia a narração "
            "alheia. Explique o assunto de forma envolvente, condensada e clara. NÃO existe 'protagonista' "
            "nem 'prota' — é um vídeo informativo, não uma história de anime/manhwa. Refira-se ao tema ou "
            "às pessoas/coisas do vídeo pelo nome ou descrição.")
    elif nicho in _NICHOS_PRIMEIRA_PESSOA or tipo in _NICHOS_PRIMEIRA_PESSOA:
        contexto = (
            "Você é roteirista de um canal brasileiro de dorama/filme. Recebe a "
            "transcrição CRUA (possivelmente em outra língua) de um vídeo já existente e reescreve com "
            "VOZ PRÓPRIA e ORIGINAL em português brasileiro — NUNCA traduz literalmente nem copia a narração "
            "alheia. Narre em 1ª PESSOA, como se o PROTAGONISTA estivesse contando a própria história "
            "(use 'eu', 'minha', 'me'). Se a protagonista for MULHER, o 'eu' é feminino em TODA concordância "
            "('eu estava cansada', 'fiquei sozinha', 'obrigada'); se for homem, masculino. Chame os outros personagens pelo papel deles: 'o herdeiro', "
            "'o homem rico', 'o empresário', 'a garota pobre', 'meu chefe', 'minha vizinha' — NUNCA use "
            "'prota', 'protagonista' nem 'nosso garoto'. Conte de forma envolvente, condensada e clara.")
    else:
        contexto = (
            "Você é roteirista de um canal brasileiro de conteúdo animado. Recebe a "
            "transcrição CRUA (possivelmente em outra língua) de um vídeo animado já "
            "existente e reescreve com VOZ PRÓPRIA e ORIGINAL em português brasileiro — "
            "NUNCA traduz literalmente nem copia a narração alheia. Conte a história de "
            "forma envolvente, condensada e clara.")
    return (
        contexto + " Frases curtas e faladas (para narração "
        "em voz alta), uma ideia por frase. Não invente fatos que não estão na "
        "transcrição.\n\n"
        "REGRAS DE CONTEÚDO E FORMATAÇÃO (VIOLAÇÃO GERA FALHA CRÍTICA):\n"
        "1. NÃO use marcações teatrais, colchetes, parênteses ou nomes de personagens como título (Ex: não use 'Narrador:', '[Música]', '(Suspense)').\n"
        "2. NÃO faça introduções nem se despeça (NÃO DIGA 'Aqui está o roteiro', nem termine com 'Espero ter ajudado'). Vá DIRETO para a primeira frase da história.\n"
        "3. Retorne APENAS AS FRASES da história, limpas, uma por linha.\n\n"
        "ATENÇÃO MÁXIMA: Se a transcrição for apenas ruídos sem sentido, "
        "sons soltos sem palavras (ex: só música com risadas), ou texto totalment "
        "incompreensível (mais de 80% caracteres ilegíveis), "
        "você DEVE responder EXATAMENTE a palavra: [ERRO: LIXO], e abortar o roteiro."
    )

# Repertório medido em 15 canais BR de recap (hipercool, D:\hipercool-materiais\referencias_narradores). Pode não
# existir em outra máquina: aí o roteiro sai só com o _SYSTEM.
_REPERTORIO = Path(r"D:\hipercool-videos\config\repertorio_narrador.json")
_TIPOS_COM_PIADA = {"anime", "manhwa"}


def _jeito_do_nicho():
    """Acréscimo ao _system(): como os narradores do nicho falam, o que entrega roteiro automático, o que o público
    não fala e (anime/manhwa) 2 moldes de piada sorteados, 1 usado por trecho."""
    try:
        rep = json.loads(_REPERTORIO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    tipo = os.environ.get("PARCEIRO_TIPO", "anime")
    nicho = os.environ.get("NICHO_CLONE", tipo)
    sem_protagonista = nicho in _NICHOS_SEM_PROTAGONISTA or tipo == "fatos"
    primeira_pessoa = nicho in _NICHOS_PRIMEIRA_PESSOA or tipo in _NICHOS_PRIMEIRA_PESSOA
    linhas = ["\n\nCOMO OS NARRADORES BR DE RECAP FALAM (medido em 15 canais grandes):"]
    if primeira_pessoa:
        linhas.append("- Narre em 1ª PESSOA no PRESENTE, como se o protagonista estivesse contando a própria história "
                      "('eu chego', 'eu percebo', 'meu coração dispara'). Os outros personagens são descritos pelo PAPEL: "
                      "'o herdeiro', 'o homem rico', 'a garota pobre', 'meu chefe'. NUNCA use 'prota', 'protagonista' "
                      "nem 'nosso garoto'. Fala comum de outro personagem vira discurso indireto ('ele me diz que...').")
    else:
        linhas.append("- Conte no PRESENTE, em 3ª pessoa, com fato concreto em toda frase; fala comum de personagem vira "
                      "discurso indireto ('ele pergunta se...', 'ela diz que...').")
    if sem_protagonista:
        linhas.append("- Soe como gente contando pra um amigo, não como texto de livro lido. Refira-se ao assunto "
                      "pelo nome ou descrição — NÃO existe 'protagonista', 'prota' nem 'garoto' neste vídeo.")
    elif primeira_pessoa:
        linhas.append("- Soe como gente contando pra um amigo, não como texto de livro lido.")
    else:
        linhas.append("- Soe como gente contando pra um amigo, não como texto de livro lido. De vez em quando chame o "
                      "protagonista pelo apelido do nicho ('o prota', 'nosso garoto', 'o cara') em vez do nome.")
    linhas.append("- Pontue normalmente (vírgulas e pontos): a pontuação vira pausa na voz. Os exemplos abaixo vêm de "
                  "legenda automática e não têm pontuação — não copie isso.")
    # 22/10 (dono: "se percebe que é IA — parece que a pessoa está LENDO"): o que mais entrega leitura é a
    # PROSA ESCRITA. Regras de fala de verdade:
    linhas += [
        "- FALA DE VERDADE, não redação: use as contrações faladas do Brasil (tá, pra, cê, né, tô, cadê). "
        "Frases de 5 a 14 palavras; ficou maior, QUEBRE em duas.",
        "- A cada 6 a 8 frases, UMA pergunta retórica curta pro espectador ('e aí, o que ele faz?', "
        "'adivinha quem aparece?').",
        "- 1 ou 2 vezes NO VÍDEO INTEIRO, uma reação curtíssima do narrador como frase própria ('Caraca.', "
        "'Olha isso.', 'Não acredito.') — nunca inventando fato.",
        "- PROIBIDO conectivo de redação: 'além disso', 'no entanto', 'portanto', 'em seguida', 'dessa forma', "
        "'por sua vez', 'entretanto', 'contudo'.",
        "- NUNCA estique palavra com letras repetidas ('faaala', 'nãooo') nem escreva onomatopeia letra a letra: "
        "a voz SOLETRA isso e estraga o vídeo. Escreva normal — a ênfase e o alongamento são aplicados depois, "
        "no áudio. Reticências (...) só pra suspense de verdade.",
    ]
    proib = [i["item"] for i in (rep.get("roteiro_automatico_proibido") or {}).get("itens") or [] if i.get("item")]
    if proib:
        linhas.append("- PROIBIDO (entrega roteiro automático): " + "; ".join(proib) + ".")
    evitar = [n["item"] for n in rep.get("nao_usar") or [] if isinstance(n, dict) and n.get("item")]
    if evitar:
        linhas.append("- NÃO use: " + "; ".join(evitar) + ".")
    moldes = rep.get("moldes_piada") or []
    if os.environ.get("PARCEIRO_TIPO", "anime") in _TIPOS_COM_PIADA and moldes:
        linhas.append("- Ponha EXATAMENTE 1 tirada do narrador neste trecho (frase curta própria, comentário dele sobre "
                      "a cena, sem inventar fato), usando UM destes moldes; tem que fazer sentido traduzida (sem time, "
                      "político ou marca do Brasil):")
        # 11/11 dona (Medieval 9: "as piadas com vozes reais ficam muito boas, temos que ampliar com piadas de seios
        # e de boa RES-peito como ele fala, piadinhas falando da beleza das moças"): 1 dos 2 moldes sorteados é
        # sempre um de BELEZA ("beleza": true no repertório) — só usado se a cena tiver moça adulta. PIADA_BELEZA=0 volta.
        beleza = [m for m in moldes if m.get("beleza")]
        outros = [m for m in moldes if not m.get("beleza")]
        if beleza and outros and os.environ.get("PIADA_BELEZA", "1") != "0":
            escolha = [random.choice(beleza), random.choice(outros)]
            linhas.append("  (o molde de beleza só se a cena tiver moça ADULTA bonita; sem isso, use o outro molde)")
        else:
            escolha = random.sample(moldes, min(2, len(moldes)))
        for m in escolha:
            travas = "; ".join(m.get("travas") or [])
            linhas.append(f"  * {m.get('nome', '')} | MOLDE: {m.get('molde', '')} | exemplo real: "
                          f"\"{m.get('exemplo_real', '')}\"" + (f" | NUNCA: {travas}" if travas else ""))
    linhas += [f"- {r}" for r in ajustes_cortes().get("regras_roteiro") or []]
    # 13/11 teste T13 (pesquisador: ThomasPraun/spoken-script, hooks.md — ideia reescrita): o TIPO da 1ª frase vira
    # variante sorteada por vídeo (variantes.py "abertura"). "fato" (ou sem env) = como sempre. As outras continuam
    # carregando o fato do vídeo — muda só a forma. Desliga: "abertura": "fato" em cortes_ajustes.json.
    _ab = _ABERTURAS.get(os.environ.get("CORTES_ABERTURA", ""))
    if _ab:
        linhas.append("- FORMA DA 1ª FRASE (vale por cima de outras instruções de abertura; 5 a 12 palavras, sem "
                      "saudação, sem contar o final): " + _ab)
    # 28/10 teste T4 (frente 7, dona: "pontos de expectativa pra prender"): versão B = 1 frase de expectativa no MEIO,
    # sempre VERDADEIRA (o que ela promete acontece no próprio vídeo). Banimento antigo: nada de "parte 2" falsa.
    if os.environ.get("CORTES_GANCHO_MEIO") == "B":
        linhas.append("- No MEIO do roteiro (nunca na 1ª nem na última frase), coloque UMA frase curta de expectativa que "
                      "prenda até o final — ex.: 'e o pior ainda estava por vir', 'só que ninguém esperava o que veio "
                      "depois'. O que ela promete TEM de acontecer neste vídeo. PROIBIDO: 'parte 2', 'continua', "
                      "'no próximo vídeo', 'comenta', 'se inscreve' ou qualquer promessa que o vídeo não cumpre.")
    return "\n".join(linhas)


def ajustes_cortes():
    """27/10: regras/ajustes do MELHORADOR dos Cortes (bin\\cortes_ajustes.json) — só vale em Short de parceiro
    (PARCEIRO_CANAL definido); longo e outros = {}."""
    if not os.environ.get("PARCEIRO_CANAL"):
        return {}
    try:
        return json.loads((Path(__file__).resolve().parent / "cortes_ajustes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _narrador_v2():
    return os.environ.get("VOZ_CLONADA") if os.environ.get("VOZ_CLONADA_VERSAO") == "2" else None


_TRECHOS = Path(r"D:\hipercool-materiais\amostras_voz\trechos_icones")  # o anime_tts abre o vídeo com um deles


def _guia_narrador():
    """(voz, linguagem_v2.json do narrador da vez) ou (None, {})."""
    voz = _narrador_v2()
    if not voz:
        return None, {}
    try:
        return voz, json.loads((Path(r"D:\hipercool-materiais\models\rvc\vozes") / voz / "linguagem_v2.json")
                               .read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return voz, {}


def _falas_do_trecho(voz):
    """Falas dos trechos originais que abrem o vídeo (anime_tts._abrir_com_trecho); [] = a voz não tem trecho."""
    try:
        lista = json.loads((_TRECHOS / voz / "trechos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [t.get("frase") or "(som)" for t in lista if t.get("arquivo")]


_OFENDE_PUBLICO = re.compile(r"(?i)insignificante|\btol[oa]s?\b|idiota|burr[oa]|imbecil|est[uú]pid|in[uú]te[il]|"
                             r"fracot|verme|\blixo\b|criatura|ot[aá]ri|pat[eé]tic|\bmortal|miser[aá]ve|ignorante|"
                             r"retardad|plebe|\bral[eé]\b|desprez|infeliz|desocupad|imprest[aá]ve|incompetent|"
                             r"amadores|\bnoobs?\b|\blentos\b|gentalha|ign[oó]bil|parasita|\bman[eé]s?\b|pentelh|"
                             r"humaninho|seus humanos|meia-pataca|moscas?-mortas|sem cultura|polu[ií]?da")


_ABERTURAS = {  # teste T13 (13/11): braço -> instrução da 1ª frase. "fato" não está aqui = sem instrução extra.
    "pergunta": "uma PERGUNTA curta sobre o fato mais estranho do vídeo, que o próprio vídeo responde (ex.: 'Por que "
                "alguém enterraria o próprio carro?').",
    "contraste": "um CONTRASTE entre o que se esperava e o que aconteceu, na mesma frase (ex.: 'Era pra ser só um "
                 "treino, mas terminou com o ginásio destruído').",
    "custo": "o PREÇO que alguém da história pagou ou arriscou, antes de explicar como (ex.: 'Ele perdeu tudo que "
             "tinha em uma única noite').",
}


def _jeito_do_narrador(gancho=False):
    """Clone 2.0 (dono 19/10): o vídeo sai com a voz de um narrador parceiro — o roteiro vem escrito no jeito DELE
    (guia medido nas legendas e na fala real: D:\\hipercool-materiais\\bin\\clone2.py linguagem).
    gancho=True (fechar_loop): só o jeito de falar — 21/10 o gancho virava cópia da abertura e apagava o desfecho."""
    voz, g = _guia_narrador()
    if not g:
        return ""

    def lista(k, n=6):
        return ", ".join(f'"{x}"' for x in (g.get(k) or [])[:n])
    trecho = _falas_do_trecho(voz)
    nicho = os.environ.get("NICHO_CLONE", os.environ.get("PARCEIRO_TIPO", "anime"))
    # dono 26/10: dorama/filme = o PROTAGONISTA conta em 1ª pessoa, vale por cima da pessoa do narrador ("3ª pessoa",
    # "o próprio Naruto contando"); do narrador fica só o jeito de falar
    prota1 = primeira_pessoa()
    pessoa = ("Neste vídeo NÃO é ele quem conta: quem narra é o PROTAGONISTA da história, em 1ª pessoa ('eu', 'meu'); "
              "dele vem só o jeito de falar. NADA de bordão, abertura, piada ou mania dele: o personagem da história "
              "nunca falaria isso. Tom de DESABAFO informal, de quem conta o perrengue pra um amigo ('cê não tem noção "
              "do que eu passei', 'aquele infeliz'), julgando as pessoas da história com as próprias palavras."
              if prota1 else g.get('pessoa', ''))  # 28/10: aprendizado 5a106596 aprovado pelo dono
    if prota1:  # 26/10 (filme com a Chiquinha: 4 bordões e o salva-vidas "aluno novo na escola"): sem a abertura dele
        trecho = []
    linhas = ["\n\nESTE VÍDEO SAI COM A VOZ DE UM NARRADOR REAL: escreva NO JEITO DELE (copie o jeito, nunca o texto). "
              "Quando isto brigar com o 'COMO OS NARRADORES BR FALAM' acima, vale isto"
              + (" — MENOS a 1ª pessoa do protagonista, que sempre vale." if prota1 else "."),
              f"- Quem ele é: {g.get('resumo', '')} Tom: {g.get('tom', '')}. {pessoa}",
              f"- Frases {g.get('tamanho_frase', 'curtas')}."]
    if gancho or prota1:
        pass
    elif trecho:  # dono 21/10 (Seu Madruga): trecho real + abertura escrita = 2 bordões seguidos no começo
        linhas.append(f"- O vídeo JÁ ABRE com a voz real dele: {' / '.join(trecho)}. Então a 1ª frase vai DIRETO ao "
                      "assunto (fato concreto do vídeo), sem apresentação, sem bordão e sem a abertura dele; e não "
                      "repita essa fala em lugar nenhum.")
    elif g.get("abertura"):  # dono 21/10 "não tem contexto": a 1ª frase era só a abertura inteira, copiada
        chamado = re.split(r"[,!?.]", g["abertura"])[0].strip()
        linhas.append(f"- 1ª frase = gancho com o FATO principal do vídeo. Pode abrir com o chamado dele ('{chamado}, "
                      "...') e emendar o fato na mesma frase — nunca só apresentação sem conteúdo.")
    if g.get("tiradas") and not prota1:
        linhas.append(f"- Comentários/piadas dele: {g['tiradas']}")
    # 11/11 (dona: "o Patolino chama de 'plateia insignificante' — isso não pode, nem depreciar a plateia como o Kratos
    # faz"): 11 de 80 perfis tinham fala_com_publico ofensiva (idiota, verme, tolo, ignorante, criatura, plebeus...).
    # Filtra a lista e manda a regra pra TODO narrador: o personagem pode ser ranzinza com a HISTÓRIA, nunca com quem
    # assiste. ROTEIRO_PUBLICO_LIVRE=1 desliga.
    if os.environ.get("ROTEIRO_PUBLICO_LIVRE") != "1":
        g = dict(g)
        g["fala_com_publico"] = [x for x in g.get("fala_com_publico") or [] if not _OFENDE_PUBLICO.search(str(x))]
        linhas.append("- NUNCA deprecie, xingue ou diminua quem assiste (nada de 'plateia insignificante', 'tolo', "
                      "'idiota', 'verme', 'ignorante', 'criatura', 'mortal', 'plebeu', 'seu burro'). Pode ser ranzinza "
                      "ou debochado com os PERSONAGENS da história; com o público, sempre respeitoso e acolhedor "
                      "('você que tá vendo', 'meu povo', 'galera').")
    for chave, texto in (("conectores", "Conectores que ele usa"), ("fala_com_publico", "Fala com o público assim"),
                         ("interjeicoes", "Interjeições dele"), ("apelidos_protagonista", "Chama o protagonista de")):
        if chave == "apelidos_protagonista" and (nicho in _NICHOS_SEM_PROTAGONISTA or nicho in _NICHOS_PRIMEIRA_PESSOA):
            continue  # 21/10: "esse infeliz de uma figa" pro criador do Game Boy — vídeo informativo não tem prota
        if chave == "interjeicoes" and prota1:
            continue
        if g.get(chave):
            linhas.append(f"- {texto}: {lista(chave)}.")
    if g.get("bordoes") and not gancho and not prota1:
        # dona 23/10: NO MÁXIMO 1 bordão no vídeo inteiro — só pra identificar quem narra; o foco é a história
        linhas.append(f"- Bordões dele: {lista('bordoes')}. Use NO MÁXIMO 1 no vídeo inteiro, colado numa frase que "
                      "também conta um fato do vídeo (na mesma linha), nunca uma linha só de bordão.")
    if g.get("girias_regionais"):
        linhas.append(f"- Gírias/regionalismos DELE (1 ou 2 no vídeo, onde couber natural): {lista('girias_regionais', 8)}.")
    if g.get("contracoes"):
        linhas.append(f"- Escreva como ele FALA (a voz lê do jeito escrito): {lista('contracoes', 8)}.")
    if g.get("frases_reais"):
        linhas.append("- Jeito real dele (só o ritmo e o vocabulário, NÃO copie): "
                      + " | ".join(str(f) for f in g["frases_reais"][:5]))
    if g.get("evitar"):
        linhas.append(f"- Ele NÃO faz: {lista('evitar', 5)}.")
    if g.get("tipo") == "personagem" and not gancho and not prota1:  # dono 20/10: o público tem que reconhecer quem narra
        quem = g.get("canal", voz).upper()
        # 22/10 (dono: "parar de ser alguém falando com a voz da Chiquinha — ser a PRÓPRIA Chiquinha narrando do jeito
        # dela; ela fala 'pois é, pois é, pois é'"): com persona (persona_personagem.py) o personagem narra o vídeo
        # INTEIRO como ele: maneirismos ao longo, 2-3 bordões REAIS espalhados, comparações com o mundo dele.
        # O monitor (monitor_bordoes.py) tira o que a voz fala estranho.
        estranhos = {str(x).strip().lower() for x in g.get("bordoes_estranhos") or []}
        reais = [b for b in g.get("bordoes_iconicos") or [] if b.strip().lower() not in estranhos]
        manias = [m for m in g.get("maneirismos") or [] if m.strip().lower() not in estranhos]
        if g.get("persona_v") and (reais or manias):
            linhas.append(f"- QUEM NARRA É O PRÓPRIO PERSONAGEM ({quem}), em 1ª pessoa, do começo ao fim — NÃO é um "
                          f"narrador neutro com a voz do personagem: é o personagem contando a história do jeito "
                          f"próprio, com a personalidade e o gênero de {quem} (concorde as palavras com isso).")
            if g.get("como_conta"):
                linhas.append(f"- Como ele conta: {g['como_conta']}")
            # dona 23/10: personagem usa NO MÁXIMO 1 bordão por vídeo (só pra identificar; o foco é a história)
            if manias:
                linhas.append("- Manias de fala dele (escreva EXATAMENTE assim, palavra inteira; no máximo 1 no vídeo, "
                              "onde caberia a reação dele): " + "; ".join(f'"{m}"' for m in manias[:5]) + ".")
            if reais and not trecho:
                linhas.append("- Bordões REAIS dele (o público reconhece): use LITERALMENTE 1 só no vídeo inteiro, "
                              "colado num fato do vídeo: " + "; ".join(f'"{b}"' for b in reais[:5]) + ".")
            elif reais:
                linhas.append("- A voz real dele já abre o vídeo: NÃO escreva bordão nenhum.")
            if g.get("referencias"):
                linhas.append("- De passagem (1 vez, se couber), ele compara uma cena com o mundo dele: "
                              + ", ".join(str(x) for x in g["referencias"][:4]) + ".")
            if g.get("soaria_falso"):
                linhas.append("- Isto denunciaria que NÃO é ele (evite): "
                              + "; ".join(str(x) for x in g["soaria_falso"][:4]) + ".")
        elif trecho:
            linhas.append(f"- QUEM NARRA É O PRÓPRIO {quem}, em 1ª pessoa. Como a voz real dele já abre o vídeo, use NO "
                          "MÁXIMO 1 bordão escrito, diferente da fala do trecho, colado numa frase com fato, no meio ou "
                          "perto do fim.")
        else:
            linhas.append(f"- QUEM NARRA É O PRÓPRIO {quem}, em 1ª pessoa, contando a história. OBRIGATÓRIO: use "
                          f"LITERALMENTE 1 bordão clássico dele (o 1º da lista de preferência), colado numa frase com fato, "
                          f"na abertura ou perto do fim: {lista('bordoes', 3)}. Isto vale mais que 'nunca copie o texto'.")
    if gancho:
        linhas.append("- Nesta tarefa: NÃO use bordão, NÃO use a abertura dele, NÃO se apresente.")
    # dona 23/10 (o Plankton narrou um vídeo só xingando o pessoal, sem contar nada): o jeito do personagem é um
    # TEMPERO A MAIS por cima da história, nunca no lugar dela
    linhas.append("- O CONTEÚDO É A HISTÓRIA DO VÍDEO: toda frase conta um fato do que acontece (quem, o quê, a virada). O "
                  "jeito do personagem é só um tempero A MAIS nas palavras; NUNCA troque fatos por opinião, xingamento, "
                  "reclamação ou falar de si mesmo. Quem nunca viu o vídeo tem de entender a história só pela narração.")
    linhas.append("- Zoeira leve sim; palavrão pesado e piada de orientação sexual NUNCA (o YouTube corta o anúncio).")
    # dona 23/10: o Short roda em LOOP — despedida no fim quebra o loop
    linhas.append("- NADA de despedida ou encerramento ('boa noite', 'até a próxima', 'tchau', 'fui', 'beijo'): o vídeo "
                  "roda em loop e a última frase emenda na primeira.")
    return "\n".join(linhas)


def _split_blocks(text, block_chars=6000):
    """Divide o texto cru em blocos de ~block_chars, cortando em fim de frase."""
    text = re.sub(r"\s+", " ", text).strip()
    blocks, start = [], 0
    while start < len(text):
        end = min(start + block_chars, len(text))
        if end < len(text):
            dot = text.rfind(". ", start, end)
            if dot > start:
                end = dot + 1
        blocks.append(text[start:end].strip())
        start = end
    return blocks


def _auto_block_chars(target_lines, text_len):
    """Escolhe block_chars de modo que sobre ~30 frases/bloco.

    Para target_lines=40  (curto) → block_chars=6000 (comportamento antigo)
    Para target_lines=1000 (longo) → block_chars=2000 (mais blocos)

    Pressupõe que a IA entrega ~30 frases/bloco com max_tokens=2000 quando o
    prompt é direto. Se o bloco for maior, a IA condensa sozinha.
    """
    if target_lines <= 50 or text_len < 6500:
        return 6000  # vídeos curtos: comportamento antigo preservado
    # Para vídeos longos, queremos target_lines/30 blocos.
    # Cada bloco precisa ter text_len / (target_lines/30) chars
    n_blocks = max(2, round(target_lines / 30))
    return max(1500, text_len // n_blocks)


# 23/10 (dono: "esse vídeo deu muito ruim", mushishi): o gateway devolveu a RECUSA do Gemini como se fosse texto
# ("The prompt could not be submitted... violate Google's Generative AI Prohibited Use policy") e ela foi NARRADA em
# 4 vídeos (2 chegaram a ser agendados). Resposta de erro/recusa nunca vira roteiro: em qualquer língua, descarta.
_RX_ERRO_IA = re.compile(
    r"could not be submitted|prohibited use|violat\w* .{0,40}polic|sensitive words|"
    r"as an? (?:generative )?ai\b|generative ai (?:model|assistant|system)|"
    r"i can(?:'|no)t (?:help|assist|create|write|provide)|i'?m sorry,? (?:but|i )|i'?m unable to|"
    r"unable to (?:help|assist)|"
    r"against (?:my|the) (?:guidelines|polic)|content policy|safety (?:filter|policy|guidelines)|"
    r"request (?:was )?blocked|send feedback|troubleshooting|"
    # 13/11: "api key", "rate limit", "prompt", "exception:" sozinhos também são NARRAÇÃO nos canais de negócios/IA
    # ("o prompt certo muda tudo", "sem a api key o robô não funciona"): o roteiro inteiro era descartado como erro.
    # Agora só a forma que o PROVEDOR escreve.
    r"(?:invalid|missing|incorrect|no|wrong) api key|api key (?:not|is|inv[áa]lida|ausente|incorreta)|"
    r"rate.?limit\w* (?:exceeded|reached|error|atingido)|exceeded .{0,25}rate limit|\bquota exceeded\b|"
    r"internal server error|\b(?:http|error)\s*[45]\d{2}\b|traceback \(most recent|\w+(?:exception|error):\s|"
    # revisão 23/10: "como ia sair dali", "alíquota", "o erro 100 vezes" são narração normal — fora da lista
    r"não posso (?:ajudar|criar|escrever|gerar)|como modelo de linguagem|"
    r"viola(?:m|r)? (?:as )?(?:diretrizes|políticas) (?:de (?:uso|conte[úu]do|seguran[çc]a)|d[ao] (?:openai|google|"
    r"anthropic|plataforma|youtube))|conteúdo (?:sensível|impróprio) .{0,30}não (?:posso|consigo|pode ser|é permitido)|"
    # 30/10 (PROPOSTAS CORTES, sem-obra-54b88d nota 2,5): a IA pediu o material em vez de escrever e o pedido foi
    # NARRADO ("envie a transcrição para que criar o roteiro completo no estilo do ... garantindo perfeita para o loop")
    # 13/11: só quando é PEDIDO DE MATERIAL ("...para que eu crie", "...completa", "...aqui"); "Mande o vídeo pro grupo
    # da família" e "Cole o texto no ChatGPT" são fala normal de CTA/tutorial
    r"(?:envie|mande|forneça|cole|me passe)(?:-me)? (?:a|o) (?:transcrição|legenda|texto|vídeo|roteiro)\b"
    r"(?=.{0,80}(?:para que|pra que|para eu|pra eu|que eu possa|e eu (?:crio|escrevo|fa[çc]o|reescrevo)|abaixo|"
    r"complet[ao]|original|aqui\b))|"
    r"(?:aqui está|segue) (?:o|seu) roteiro\s*[:\n]|roteiro (?:completo|reescrito) no estilo|"
    r"(?:seu|este|esse|do|no|o|ao) prompt (?:acima|abaixo|fornecido|enviado|anterior|original|do sistema)|system prompt|"
    r"garantindo .{0,25}\bloop\b|please (?:provide|send|share)", re.I)


TRANSCRICAO_LIXO = False  # 27/10: a IA respondeu [ERRO: LIXO] — o Short não sai (não pede de novo a outro modelo)


def _e_lixo(texto):
    return bool(texto) and "ERRO: LIXO" in str(texto).upper()


def resposta_de_erro(texto):
    """True se o texto parece erro do provedor ou recusa da IA (nunca pode ser narrado)."""
    return bool(texto) and bool(_RX_ERRO_IA.search(texto))


# Marcador de lista no começo da linha: "- ", "* ", "• ", "1. ", "2) " (e reticências soltas). NÃO é número da frase:
# antes era r"^[\-\*\d\.\)\s]+" e comia o número de "300 soldados cercaram a vila" -> "soldados cercaram a vila",
# "2 anos depois" -> "anos depois", "1995 foi o ano" -> "foi o ano" (a narração saía sem o número).
_RX_MARCADOR_LISTA = re.compile(r"^\s*(?:(?:[-*•–—]+|\d{1,3}[.)]|#{1,6})\s+|\.{2,}\s*|…\s*)+")
_PARES_ASPAS = (('"', '"'), ("“", "”"), ("«", "»"), ("'", "'"))


_RX_CURTA = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{1,6}[.!?…]+")   # frase de 1-2 palavras com pontuação final


def _limpa_linha(s):
    """Uma linha da resposta do modelo -> frase limpa (sem marcador de lista, sem negrito de markdown, sem aspas em
    volta da frase inteira). Aspas de fala no MEIO da frase ficam inteiras: antes o strip tirava só uma das duas
    ('"Você não é nada", disse ela.' virava 'Você não é nada", disse ela.')."""
    s = _RX_MARCADOR_LISTA.sub("", s.strip())
    s = re.sub(r"\*+|(?<!\w)_{1,2}(?=\w)|(?<=\w)_{1,2}(?!\w)", "", s).strip()   # **negrito**, _itálico_
    for a, b in _PARES_ASPAS:
        if len(s) >= 2 and s[0] == a and s[-1] == b and a not in s[1:-1] and b not in s[1:-1]:
            s = s[1:-1].strip()
    if s.count('"') == 1 and (s[0] == '"' or s[-1] == '"'):   # aspa órfã na ponta (o par ficou em outra linha)
        s = s.replace('"', "").strip()
    return s


def _clean_lines(raw):
    """Quebra a resposta do modelo em frases-linha limpas."""
    out = []
    for ln in raw.splitlines():
        s = _limpa_linha(ln)
        if len(s) >= 8:
            out.append(s)
        elif out and _RX_CURTA.fullmatch(s):
            out[-1] = f"{out[-1]} {s}"   # "Não!", "Vazio.", "Tarde." numa linha só: gruda na anterior em vez de sumir
    return out


def rewrite(transcript, target_lines=40):
    """Reescreve a transcrição num roteiro PT-BR (lista de frases).

    target_lines: nº aproximado de frases no roteiro final (controla a duração).
    Para vídeos longos (1h+), use target_lines >= 800 (cada frase ≈ ~4s de narração).
    Retorna [str]. Lista vazia se a IA não estiver disponível ou a transcrição for inválida.
    """
    if len(re.sub(r'[^a-zA-ZáéíóúãõçÁÉÍÓÚÃÕÇ]', '', transcript)) < 50:
        logging.error("[script] transcrição parece vazia ou sem texto real (só ruído/símbolos). Abortando.")
        return []

    # Fila: se já geramos esse roteiro antes (mesma transcrição + target), reusa
    # e NÃO chama o LLM de novo. Beta/experimental herdam o que a produção gerou.
    cached = _cache_get(transcript, target_lines)
    if cached is not None:
        return cached

    if not claude_client.is_available():
        logging.error("[script] claude_client indisponível — sem reescrita")
        return []

    block_chars = _auto_block_chars(target_lines, len(transcript))
    blocks = _split_blocks(transcript, block_chars=block_chars)
    # Quantas frases pedir por bloco? A IA entrega ~30 frases em 2000 tokens
    # quando o trecho cabe na janela; se o trecho for grande ela condensa.
    per_block = max(3, round(target_lines / max(1, len(blocks))))
    logging.info(f"[script] {len(blocks)} blocos (block_chars={block_chars}), ~{per_block} frases/bloco")

    system = _system() + _jeito_do_nicho() + _jeito_do_narrador()
    roteiro = []
    for i, blk in enumerate(blocks):
        prompt = (
            f"Trecho {i+1}/{len(blocks)} da transcrição de um recap de anime.\n"
            f"Reescreva com voz própria em PT-BR mantendo FIDELIDADE ao trecho — "
            f"narrando todos os fatos, diálogos e momentos relevantes. "
            f"Produza aproximadamente {per_block} frases curtas de narração (uma por linha), "
            f"sendo o mais completo possível: NÃO condense demais, NÃO pule diálogos "
            f"importantes, NÃO resuma numa frase algo que merece mais.\n"
            "CONCORDÂNCIA DE GÊNERO: use o artigo e pronome corretos (a/o, ela/ele, da/do) para cada personagem. "
            "Se o personagem é feminino, diga 'a guerreira', 'ela', 'da Lilim'; nunca 'o Lilim'. Erre o gênero = erro grave."
            f"\n\n{blk}"
        )
        try:
            resp = claude_client.generate_text(prompt, system=system,
                                               max_tokens=2000, temperature=0.6, timeout=300, video=True)
        except Exception as e:
            logging.error(f"[script] bloco {i} falhou: {e}")
            continue
        if not resp:
            logging.warning(f"[script] bloco {i} retornou None (gateway timeout ou erro silencioso)")
            continue
        if _e_lixo(resp) and len(blocks) == 1:  # 27/10: Short (1 bloco) com transcrição lixo = sem roteiro
            global TRANSCRICAO_LIXO
            TRANSCRICAO_LIXO = True
            logging.warning("[script] a IA marcou a transcrição como LIXO — sem roteiro")
            return []
        if resposta_de_erro(resp[:300]):  # erro/recusa vem no começo; no meio de um bloco bom, a linha sai sozinha
            logging.warning(f"[script] bloco {i}: a IA devolveu ERRO/RECUSA em vez de roteiro — descartado: "
                            f"{resp[:120]!r}")
            continue
        if resp:
            # Proteção contra recusas quando o texto cru é lixo (sem voz/música apenas)
            resp_lower = resp.lower()
            if "[erro: lixo]" in resp_lower or ("transcrição" in resp_lower and ("incompleta" in resp_lower or "ruído" in resp_lower or "por favor" in resp_lower or "esqueceu" in resp_lower)):
                logging.warning(f"[script] A IA recusou o bloco {i} pois parece ruído/incompleto. Pulando...")
                continue

            # Filtro adicional de segurança: remover linhas que começam parecendo fillers
            clean_lines = _clean_lines(resp)
            final_lines = []
            for line in clean_lines:
                ll = line.lower()
                if ll.startswith("aqui está") or ll.startswith("aqui vai") or ll.startswith("espero que goste") or ll.startswith("claro"):
                    continue # Descarta fillers de conversação da IA
                if line.endswith(":") and len(line.split()) < 5:
                    continue # Descarta indicações como "Narrador:", "Cena 1:"
                final_lines.append(line)

            roteiro.extend(final_lines)

    roteiro = [l for l in roteiro if not resposta_de_erro(l)]  # linha solta de erro no meio de um bloco bom
    if not roteiro:
        return []

    # ── Protecao anti-ban (anti-strike YouTube) + viralizacao opcional ──
    roteiro = [viralizador.anti_ban(linha) for linha in roteiro]
    if os.environ.get("VIRAL_SLANG") == "1":
        roteiro = [viralizador.viralizar(linha) for linha in roteiro]

    # Sem corte global: no modo deitado (recap fiel 1h+) queremos cobertura
    # completa. Cortar em target_lines só perderia conteúdo — o target já é meta
    # orientativa passada ao LLM por bloco. Shorts usam target baixo, sem impacto.
    logging.info(f"[script] roteiro final: {len(roteiro)} frases (target_lines={target_lines})")
    # revisão 23/10: roteiro incompleto (blocos que falharam) no cache = o vídeo falhava pra sempre sem chamar a IA
    if len(roteiro) >= max(2, target_lines // 4):
        _cache_put(transcript, target_lines, roteiro)
    return roteiro


_RX_TEMPO = re.compile(r"^\s*[-•*]?\s*\[(\d+(?:[.,]\d+)?)\s*s?\]\s*(.+)$")


def rewrite_curto_com_tempo(cues, target_lines, src_dur=None):
    """Roteiro do Short com o segundo do original de cada frase (dono 21/10: "o narrador geralmente está falando de um
    quadro específico que está na tela na hora"). cues = [[início_s, texto], ...] da legenda. Devolve (frases, tempos)
    ou ([], []) — quem chama cai no rewrite() normal (sem tempos: o Short espalha as frases pelo original)."""
    # Proteção contra problemas de import circular (Python 3.11+): acessar json via módulo explícito
    import json as _json_module

    if not cues or not claude_client.is_available():
        return [], []
    blocos, atual, t0 = [], [], None  # junta a legenda em trechos de ~4 s: menos marcas, mesmo efeito
    for t, txt in cues:
        if t0 is None:
            t0 = t
        atual.append(txt)
        if t - t0 >= 4:
            blocos.append(f"[{t0:.0f}s] {' '.join(atual)}")
            atual, t0 = [], None
    if atual:
        blocos.append(f"[{t0:.0f}s] {' '.join(atual)}")
    transcricao = "\n".join(blocos)
    if len(re.sub(r"[^a-zA-ZáéíóúãõçÁÉÍÓÚÃÕÇ]", "", transcricao)) < 50:
        return [], []
    prompt = (
        f"Transcrição de um vídeo curto{f' de {src_dur:.0f} s' if src_dur else ''}, com o segundo em que cada trecho "
        "aparece entre colchetes.\nReescreva com voz própria em PT-BR, fiel aos fatos, em NO MÁXIMO "
        f"{target_lines} frases curtas de narração (nunca mais que {target_lines}), UMA POR LINHA, na ordem do vídeo.\n"
        "CONCORDÂNCIA DE GÊNERO: use o artigo e pronome corretos (a/o, ela/ele, da/do) para cada personagem. "
        "Se o personagem é feminino, diga 'a guerreira', 'ela'; nunca 'o guerreira'. Erre o gênero = erro grave.\n"
        "Cada linha COMEÇA com o segundo do vídeo original em que acontece o que a frase narra, no formato [12s] — "
        "o narrador fala do que está na tela naquela hora. Os segundos só aumentam e vão até o fim do vídeo.\n"
        "Nada além das linhas (sem título, sem comentário).\n\n" + transcricao)
    # 25/10: sem tempo o Short cai no corte "espalhado" e a fala pode vir DEPOIS da cena (dono: "pode vir antes, nunca
    # depois"). 24-25/10: 8 respostas com só 2 linhas marcadas (frases longas/marcas no meio da linha) e 2 recusas —
    # agora lê toda marca [Ns] do texto e, se ainda faltar, pede de novo 1 vez.
    frases, tempos, resp = [], [], ""
    for tentativa in range(2):
        extra = ("" if not tentativa else
                 "\nATENÇÃO: UMA frase curta por linha e TODA linha começa com [Ns]. Sem parágrafo.")
        try:
            resp = claude_client.generate_text(prompt + extra,
                                               system=_system() + _jeito_do_nicho() + _jeito_do_narrador(),
                                               max_tokens=2000, temperature=0.6, timeout=300, video=True)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[script] roteiro com tempo falhou ({type(e).__name__}: {e})")
            continue
        if _e_lixo(resp):
            # 27/10 (52ae24): o Argon disse LIXO (Whisper tiny leu japonês como inglês); a 2ª tentativa caiu na reserva,
            # que INVENTOU uma perseguição de carro no jeito do narrador. Transcrição lixo = sem roteiro.
            global TRANSCRICAO_LIXO
            TRANSCRICAO_LIXO = True
            logging.warning("[script] a IA marcou a transcrição como LIXO — sem roteiro (não pede de novo)")
            return [], []
        if resposta_de_erro(resp):
            logging.warning(f"[script] roteiro com tempo: a IA devolveu ERRO/RECUSA — descartado: "
                            f"{(resp or '')[:120]!r}")
            continue
        frases, tempos = _frases_com_tempo(resp, src_dur)
        if len(frases) > target_lines + 1 and not tentativa:
            # 30/10: "aproximadamente N" vinha com até 2x (T8 B pediu 5 e recebeu 6-10; fonte de 17 s com alvo 3 deu 4
            # frases = narração maior que o original e fim com imagem repetida). Pede de novo 1x, mais firme.
            logging.warning(f"[script] roteiro com tempo veio com {len(frases)} frases (alvo {target_lines}) — peço de novo")
            prompt += f"\nIMPORTANTE: a resposta anterior teve {len(frases)} linhas; o limite é {target_lines}."
            continue
        if len(frases) >= max(3, target_lines // 2):
            break
        amostra = re.sub(r"\s+", " ", resp or "")[:160]  # 23/10: sem isso não dava pra saber por que veio 0
        logging.warning(f"[script] roteiro com tempo veio com {len(frases)} frases marcadas"
                        f"{' — tento de novo' if not tentativa else ''} (resposta: {amostra!r})")
    if len(frases) < max(3, target_lines // 2):
        logging.warning("[script] roteiro com tempo não saiu — uso o normal (corte espalhado)")
        return [], []
    frases, tempos = _tirar_abertura_vazia(frases, tempos)
    if len(frases) > target_lines + 1:  # 2ª resposta ainda longa: as N-1 primeiras + a última (a história fecha)
        idx = list(range(max(1, target_lines - 1))) + [len(frases) - 1]
        logging.warning(f"[script] roteiro com tempo cortado de {len(frases)} pra {len(idx)} frases (alvo {target_lines})")
        frases, tempos = [frases[k] for k in idx], [tempos[k] for k in idx]
    logging.info(f"[script] roteiro com tempo: {len(frases)} frases, {tempos[0]:.0f}s..{tempos[-1]:.0f}s do original")
    return frases, tempos


def _cues_marcados(cues, passo_s=5.0):
    """[[t, texto], ...] -> [(t0, "[t0s] texto junto de ~passo_s")] (menos marcas, mesmo efeito)."""
    out, atual, t0 = [], [], None
    for t, txt in cues:
        t = float(t)
        if t0 is None:
            t0 = t
        atual.append(str(txt).strip())
        if t - t0 >= passo_s:
            out.append((t0, f"[{t0:.0f}s] {' '.join(atual)}"))
            atual, t0 = [], None
    if atual:
        out.append((t0, f"[{t0:.0f}s] {' '.join(atual)}"))
    return out


# 01/11 dona (vídeo do engenheiro, 19m25s: o narrador comenta a ironia da irmã do protagonista): "é o que um humano
# faria se estivesse lendo a história e parasse um momento pra falar algo que não estava escrito, um comentário
# pessoal — temos que adicionar mais disso, humaniza o vídeo". 1 por trecho (~2-3 min de vídeo).
_COMENTARIO_NARRADOR = (
    # 01/11 23h dona viu a PREVIA4 ("tem que colocar mais comentários como esses"): 2 por trecho (~1 a cada 1-1,5 min)
    "COMENTÁRIOS PESSOAIS DO NARRADOR (obrigatório, 2 neste trecho, um na 1ª metade e outro na 2ª): como alguém que "
    "está lendo a história em voz alta e PARA um instante pra comentar com o amigo, cada comentário é 1 frase (no "
    "máximo 2) que NÃO está na história — a opinião, a "
    "ironia ou a piada do narrador sobre o que ACABOU de acontecer. A 1ª frase do comentário COMEÇA OBRIGATORIAMENTE "
    "com UMA destas aberturas (varie, não repita a do trecho anterior): 'Cá entre nós,', 'E olha a ironia:', "
    "'Sinceramente,', 'Vamos combinar,', 'Convenhamos,', 'Pra mim,', 'Na boa,', 'Confesso que', 'Imagina só', "
    "'Repara que'. Prefira IRONIA da situação (ex.: 'E olha a ironia: a irmã que mais zombava dele é justamente a que "
    "vai precisar dele.'), reação sincera ('Cá entre nós, eu já teria desistido aqui.') ou provocação leve "
    "('Sinceramente, esse cara não aprende, né?'). Nunca invente fato, nunca adiante o que vem depois, sem palavrão. "
    "Use o mesmo [Ns] da frase anterior.\n"
    # L-09 (LONGOS_MELHORIAS, 01/11): narrador "parça" — hJaA ("our boy") e Manhwa Fresh falam do prota como de um amigo
    "TOM DE PARÇA (no trecho todo): fale do protagonista como de um amigo seu, com carinho e zoeira leve — 'o nosso "
    "garoto', 'o coitado', 'o cara' — e reaja como quem assiste junto ('e lá vai ele cair no golpe de novo', 'as red "
    "flags ali todas piscando'). Isso aparece em pelo menos 2 frases do trecho, sem palavrão e sem inventar fato.\n")
# 04/11 (pesquisa, zenstory "deslop_qc"; dona: "a narração tem que ser a melhor possível"): frases-feitas de IA deixam
# a narração com cara de robô — a lista vai no pedido (não apaga nada depois: cortar no meio quebraria o sentido)
_SEM_CLICHE = (
    "SEM CARA DE IA: NÃO use frases-feitas de texto gerado por IA — 'mal sabia ele', 'o que ninguém esperava', "
    "'prepare-se', 'e é aí que tudo muda', 'o destino tinha outros planos', 'uma reviravolta inesperada', 'de tirar o "
    "fôlego', 'sem mais delongas', 'nesse mundo implacável', 'uma jornada épica', 'algo inimaginável', 'a verdadeira "
    "batalha estava só começando'. Conte o que acontece com palavras concretas, como gente falando.\n")
# L-07 (LONGOS_MELHORIAS, 01/11): os que estouram dão uma PEQUENA VITÓRIA antes dos 8 min (bXe7 aos 5, yKfg aos 2).
# Só nos 2 primeiros blocos (~primeiros 6-8 min de narração); não inventa — só dá destaque se o trecho tiver
_VITORIA_CEDO = (
    "PEQUENA VITÓRIA CEDO: se NESTE trecho o protagonista cala, vence ou humilha alguém arrogante (mesmo que seja "
    "algo pequeno), dê destaque a esse momento com 2-3 frases de reação ('e o arrogante ficou sem resposta'). Se não "
    "tiver, NÃO invente.\n")


# LONGOS_MELHORIAS "A FAZER 10/11 (a)": o roteiro tinha 1 frase a cada 6,6 s do original SEM teto — fonte de 206 min
# (HZRT) virou 1952 frases ≈ 13 h de render a 24 s/frase > 11,5 h da sessão do Kaggle: refeito 3x, nunca terminou.
# Com teto, fonte de 3 h+ volta a caber (1500 × 24 s = 10 h). Só muda o que passa do teto; LONGO_TETO_FRASES=0 desliga.
TETO_FRASES_LONGO = int(os.environ.get("LONGO_TETO_FRASES", "1500") or 0)


def alvo_com_teto(alvo):
    """(alvo, apertado): o alvo de frases do longo já limitado ao teto, e se o teto cortou."""
    alvo = int(alvo)
    if TETO_FRASES_LONGO > 0 and alvo > TETO_FRASES_LONGO:
        return TETO_FRASES_LONGO, True
    return alvo, False


def rewrite_longo_com_tempo(cues, target_lines, src_dur=None):
    """Roteiro LONGO (deitado) com o segundo do original de cada frase. Dona 25/10 ("os longos estão muito atrás dos
    Cortes"): o Short já narrava o que está na tela (rewrite_curto_com_tempo, 21/10) e o longo espalhava as frases na
    proporção — com a narração mais curta que o original e trechos condensados, a fala descolava da imagem.
    Mesmos blocos do rewrite() longo (fiel, completo), com [Ns] em cada trecho da transcrição e em cada frase. Bloco
    sem marcas suficientes: as frases dele se espalham DENTRO do trecho do bloco (nunca invade outro trecho).
    Devolve (frases, tempos) ou ([], []) — quem chama cai no rewrite_to_file normal."""
    if not cues or not claude_client.is_available():
        return [], []
    pedido_original = target_lines
    target_lines, apertado = alvo_com_teto(target_lines)
    if apertado:
        logging.info(f"[script] roteiro longo: alvo {pedido_original} frases passa do teto — uso {target_lines} "
                     "(LONGO_TETO_FRASES) pra caber na sessão")
    marcados = _cues_marcados(cues)
    texto_total = "\n".join(m for _t, m in marcados)
    if len(re.sub(r"[^a-zA-ZáéíóúãõçÁÉÍÓÚÃÕÇ]", "", texto_total)) < 200:
        return [], []
    chave_cache = "<SEGREDO_REMOVIDO>" + texto_total
    guardado = _cache_get(chave_cache, target_lines)
    if guardado:
        frases, tempos = [], []
        for linha in guardado:
            m = _RX_TEMPO.match(linha)
            if m:
                tempos.append(float(m.group(1)))
                frases.append(m.group(2).strip())
        if frases:
            return frases, tempos
    # blocos pelo tamanho, com o trecho de tempo de cada um
    tam = _auto_block_chars(target_lines, len(texto_total))
    blocos, atual, n_chars = [], [], 0
    for t, m in marcados:
        atual.append((t, m))
        n_chars += len(m)
        if n_chars >= tam:
            blocos.append(atual)
            atual, n_chars = [], 0
    if atual:
        blocos.append(atual)
    fim_video = float(src_dur or 0) or (float(marcados[-1][0]) + 10)
    por_bloco = max(3, round(target_lines / max(1, len(blocos))))
    logging.info(f"[script] roteiro longo com tempo: {len(blocos)} blocos, ~{por_bloco} frases/bloco, "
                 f"{marcados[0][0]:.0f}s..{marcados[-1][0]:.0f}s do original")
    system = _system() + _jeito_do_nicho() + _jeito_do_narrador()
    # 02/11 dona: o 1º RECAP DE ANIME saiu com 873 frases pra alvo 1058 (vídeo 60% do original). Na variante de anime o
    # pedido vira "NO MÍNIMO" e o bloco que vier com menos de 80% é refeito 1x pedindo as cenas/falas que faltaram
    anime_var = os.environ.get("ANIME_VARIANTE") == "anime_recap"
    frases, tempos, sem_marca = [], [], 0
    for bi, bloco in enumerate(blocos):
        ini = float(bloco[0][0])
        fim = float(blocos[bi + 1][0][0]) if bi + 1 < len(blocos) else fim_video
        prompt = (
            f"Trecho {bi + 1}/{len(blocos)} da transcrição de um recap, com o segundo do vídeo original em que cada "
            "parte aparece entre colchetes.\n"
            "Reescreva com voz própria em PT-BR mantendo FIDELIDADE ao trecho — narrando todos os fatos, diálogos e "
            # 04/11 dona: "a narração tem que ser a melhor possível — sem travas que limitem a criatividade, nem mínima
            # nem máxima". O nº de frases é só referência de ritmo; a qualidade manda (sem "NO MÍNIMO", sem refazer)
            f"momentos relevantes. Como referência de ritmo, algo perto de {por_bloco} frases curtas de narração — "
            "use quantas o trecho pedir para ficar a MELHOR narração possível, UMA POR LINHA, na "
            "ordem do vídeo. NÃO condense demais, NÃO pule diálogos importantes.\n"
            # só quando o original é longo demais pra sessão (teto): aqui o nº de frases deixa de ser só referência
            + (f"ESTE VÍDEO É MUITO LONGO: fique em NO MÁXIMO {por_bloco + 2} frases neste trecho. Para caber, junte "
               "numa frase só as cenas de transição, repetições e conversa sem consequência; os momentos fortes "
               "(virada, luta, humilhação, revelação) continuam com todas as frases que precisarem.\n"
               if apertado else "") +
            "CONCORDÂNCIA DE GÊNERO: use o artigo e pronome corretos (a/o, ela/ele, da/do) para cada personagem. "
            "Se o personagem é feminino, diga 'a Lilim', 'ela', 'da guerreira'; nunca 'o Lilim'. Erre o gênero = erro grave.\n"
            "Cada linha COMEÇA com o segundo do vídeo original em que acontece o que a frase narra, no formato [123s] "
            f"— o narrador fala do que está na tela naquela hora. Os segundos só aumentam, entre {ini:.0f} e {fim:.0f}.\n"
            + _COMENTARIO_NARRADOR + _SEM_CLICHE + (_VITORIA_CEDO if bi < 2 else "") +
            # 04/11 (pesquisa, padrão alexandria-audiobook "3 últimas falas entre blocos"): cada bloco era escrito sem
            # ver o anterior — a narração recomeçava/repetia apresentações a cada ~30 frases. Agora vê como parou.
            ("O RECAP JÁ VINHA ASSIM (suas últimas frases do trecho anterior — CONTINUE daqui, no mesmo tom, sem repetir "
             "nem reapresentar personagens):\n" + "\n".join(frases[-3:]) + "\n\n" if frases else "") +
            "Nada além das linhas (sem título).\n\n" + "\n".join(m for _t, m in bloco))
        resp = None
        for _tentativa in (1, 2, 3):
            try:
                resp = claude_client.generate_text(prompt, system=system, max_tokens=5000,  # 04/11: sem teto que corte a narração
                                                   temperature=0.6, timeout=300)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[script] bloco {bi} com tempo falhou ({type(e).__name__}: {e})")
                resp = None
            if resp and not resposta_de_erro(resp[:300]):
                break  # 04/11: sem trava de tamanho (antes refazia o bloco com < 80% das frases)
            resp = None
        if not resp:
            continue
        marc, soltas = [], []
        for linha in resp.splitlines():
            m = _RX_TEMPO.match(linha)
            txt = " ".join(_clean_lines(m.group(2) if m else linha))
            if not txt and soltas:  # linha só com "Não!" / "Vazio.": fica na frase anterior (antes era jogada fora)
                curta = _limpa_linha(m.group(2) if m else linha)
                if _RX_CURTA.fullmatch(curta):
                    if marc and marc[-1][1] == soltas[-1]:
                        marc[-1] = (marc[-1][0], f"{marc[-1][1]} {curta}")
                    soltas[-1] = f"{soltas[-1]} {curta}"
            if not txt or resposta_de_erro(txt) or (txt.endswith(":") and len(txt.split()) < 5):
                continue
            low = txt.lower()
            if low.startswith(("aqui está", "aqui vai", "espero que goste", "claro")):
                continue
            if m:
                marc.append((float(m.group(1).replace(",", ".")), txt))
            soltas.append(txt)
        if len(marc) >= max(3, len(soltas) * 0.6):
            ant = ini
            for t, txt in marc:
                t = min(max(t, ant, ini), fim)  # dentro do trecho do bloco e sempre crescente
                frases.append(viralizador.anti_ban(txt))
                tempos.append(round(t, 2))
                ant = t
        elif soltas:  # a IA não marcou: espalha as frases dentro do trecho deste bloco
            sem_marca += 1
            passo = (fim - ini) / len(soltas)
            for k, txt in enumerate(soltas):
                frases.append(viralizador.anti_ban(txt))
                tempos.append(round(ini + k * passo, 2))
    if len(frases) < max(10, target_lines // 4):
        logging.warning(f"[script] roteiro longo com tempo saiu com {len(frases)} frases pra {target_lines} — "
                        "uso o normal")
        return [], []
    frases, tempos = _tirar_abertura_vazia(frases, tempos)
    logging.info(f"[script] roteiro longo com tempo: {len(frases)} frases ({sem_marca} bloco(s) sem marca, "
                 f"espalhados no trecho), {tempos[0]:.0f}s..{tempos[-1]:.0f}s")
    _cache_put(chave_cache, target_lines, [f"[{t}s] {f}" for t, f in zip(tempos, frases)])
    return frases, tempos


_RX_MARCA = re.compile(r"\[(\d+(?:[.,]\d+)?)\s*s?\]")


# ponto de abreviação não fecha frase ("O Sr. Kim chegou" virava "O Sr." + "Kim chegou." e o "O Sr." era jogado fora)
_RX_FIM_SENTENCA = re.compile(r"(?<!\bSr\.)(?<!\bDr\.)(?<!\bSra\.)(?<!\bDra\.)(?<!\bProf\.)(?<!\bMr\.)(?<!\bMrs\.)"
                              r"(?<!\bMs\.)(?<!\bSt\.)(?<!\bvs\.)(?<!\bn[ºo]\.)(?<=[.!?…])\s+")


def _sentencas(txt):
    """Texto -> frases. Pedaço curto ("Vazio.", "Não!", "Tarde.") NÃO é jogado fora (antes sumia da narração — e é
    justamente a frase de impacto): gruda na frase vizinha, sem criar um clipe de 1 palavra."""
    out = []
    for p in (x.strip() for x in _RX_FIM_SENTENCA.split(txt or "")):
        if not p:
            continue
        if len(p) < 8 and out:
            out[-1] = f"{out[-1]} {p}"            # curto depois de uma frase: fica junto dela
        elif out and len(out[-1]) < 8:
            out[-1] = f"{out[-1]} {p}"            # curto abrindo: gruda na seguinte
        else:
            out.append(p)
    if len(out) == 1 and len(out[0]) < 8 and not re.search(r"[A-Za-zÀ-ÿ]{2}", out[0]):
        return []
    return out


def _frases_com_tempo(resp, src_dur=None):
    """(frases, tempos) de uma resposta com marcas [Ns] em qualquer lugar do texto. Trecho com várias frases entre
    duas marcas vira uma frase por sentença, com o tempo repartido até a marca seguinte (no último, até ~o fim)."""
    marcas = list(_RX_MARCA.finditer(resp or ""))
    frases, tempos = [], []
    for k, m in enumerate(marcas):
        t0 = float(m.group(1).replace(",", "."))
        fim = marcas[k + 1].start() if k + 1 < len(marcas) else len(resp)
        txt = " ".join(_clean_lines(re.sub(r"^\s*[-•*]?\s*", "", resp[m.end():fim]))).strip()
        partes = _sentencas(txt)
        if k + 1 < len(marcas):
            t1 = float(marcas[k + 1].group(1).replace(",", "."))
        else:
            t1 = max(t0, min(float(src_dur) * 0.92, t0 + 4.0 * len(partes))) if src_dur else t0 + 4.0 * len(partes)
        for j, p in enumerate(partes):
            frases.append(viralizador.anti_ban(p))
            tempos.append(round(t0 + (t1 - t0) * j / len(partes), 2))
    return frases, tempos


_RX_SAUDACAO = re.compile(
    r"^\s*(?:(?:e\s+)?a[ií]|fala|ol[aá]|oi|ah|eita|ent[aã]o|bom)?[,!.\s]*"
    r"(?:minha\s+gente|meu\s+povo|galera|pessoal|gente|turma|mon|amigos?)\s*[,!.…]+\s*", re.I)


def _tirar_abertura_vazia(frases, tempos=None):
    """Rede de segurança (21/10, Ivete): a 1ª frase saía igual à abertura do narrador ("Minha gente, mainha chegou..."),
    sem nada do vídeo; com trecho real no começo, bordão também é repetição. Sai e o vídeo começa na frase com fato."""
    # 30/10 (inspeção dos Shorts prontos): 1ª fala de enchimento ("E aí, galera", "Minha gente", "Ah, mon") nos 3 s que
    # decidem a retenção, com qualquer narrador. A saudação sai; se não sobrar fato na frase, a frase inteira sai.
    # 30/10 variante T10 (bin\variantes.py, cortes_ajustes "saudacao"): A (ou sem env) = tira; B = mantém a saudação.
    if frases and os.environ.get("CORTES_SAUDACAO") != "B":
        m = _RX_SAUDACAO.match(frases[0])
        if m:
            resto = frases[0][m.end():].strip()
            if len(resto.split()) >= 4:
                logging.info(f"[script] saudação tirada da 1ª frase: «{frases[0][:m.end()].strip()}»")
                frases = [resto[0].upper() + resto[1:]] + list(frases[1:])
            elif len(frases) > 3:
                logging.info(f"[script] 1ª frase era só saudação, saiu: «{frases[0]}»")
                return frases[1:], ([tempos[0]] + tempos[2:] if tempos else tempos)
    voz, g = _guia_narrador()
    if len(frases) <= 3 or not g:
        return frases, tempos
    vazias = [g.get("abertura") or ""] + (list(g.get("bordoes") or []) if _falas_do_trecho(voz) else [])
    if not any(x and _parecida(frases[0], x) >= 0.6 for x in vazias):
        return frases, tempos
    logging.info(f"[script] 1ª frase era só abertura/bordão do narrador, saiu: «{frases[0]}»")
    return frases[1:], ([tempos[0]] + tempos[2:] if tempos else tempos)


def _normal(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in t if not unicodedata.combining(c))).split()


def _parecida(a, b):
    import difflib
    return difflib.SequenceMatcher(None, " ".join(_normal(a)), " ".join(_normal(b))).ratio()


def _gancho_ruim(nova, frases):
    """Motivo pra recusar o gancho, ou None. 21/10 (Seu Madruga, Ivete): o modelo devolvia a 1ª frase/abertura e a
    última frase — o desfecho do vídeo — sumia."""
    if not 8 <= len(nova) <= 220:
        return "tamanho"
    if resposta_de_erro(nova):
        return "a IA devolveu erro/recusa"
    if _parecida(nova, frases[0]) >= 0.5:
        return "repete a 1ª frase"
    if any(_parecida(nova, f) >= 0.6 for f in frases[1:-1]):
        return "repete outra frase"
    _voz, g = _guia_narrador()
    falas = [x for x in [g.get("abertura") or ""] + list(g.get("bordoes") or []) if x]
    if any(_parecida(nova, x) >= 0.5 for x in falas):
        return "é a abertura/bordão do narrador"
    if any(_parecida(frases[-1], x) >= 0.5 for x in falas):
        return None  # a última era só bordão: não tem fato pra manter
    antes = {p for p in _normal(frases[-1]) if len(p) >= 5}
    if len(antes) >= 3 and len(antes & set(_normal(nova))) / len(antes) < 0.34:
        return "perdeu o fato da última frase"
    return None


def fechar_loop(frases):
    """Gancho de retorno (dono 21/10): a última frase termina levando de volta à primeira, pra quem vê em loop não
    perceber que recomeçou ("x coisa acontece com o animal ... e é por isso que" -> começo). Devolve a nova última
    frase ou None (fica a original)."""
    if len(frases) < 3 or not claude_client.is_available():
        return None
    prompt = ("Roteiro de um Short que roda em LOOP (uma frase por linha):\n" + "\n".join(frases) +
              "\n\nQuando a última frase termina, o vídeo recomeça na PRIMEIRA. Reescreva SÓ a ÚLTIMA frase:\n"
              "- MANTENHA o fato/desfecho que ela conta (é o final do vídeo, não pode sumir).\n"
              "- Mude só o FIM dela: termine numa ponte (pergunta ou frase em aberto) que a PRIMEIRA frase completa "
              "naturalmente, como conversa contínua.\n"
              "- Exemplo: primeira 'Uma esfera de fogo caiu do céu naquele dia.'; última 'E o vilarejo nunca mais foi o "
              "mesmo.' -> 'E o vilarejo nunca mais foi o mesmo, tudo por causa do que aconteceu quando...'\n"
              "- PROIBIDO: copiar ou parafrasear a primeira frase; usar bordão ou a abertura do narrador; 'como eu "
              "disse'; pedir like/inscrição.\n"
              "Responda só a nova última frase, numa linha.")
    nova, motivo = "", None
    for tentativa in range(2):
        pedido = prompt if not motivo else (prompt + f"\n\nSua resposta anterior foi recusada ({motivo}): «{nova}». "
                                            "Refaça mantendo o fato da última frase.")
        try:
            resp = (claude_client.generate_text(pedido, system=_system() + _jeito_do_narrador(gancho=True),
                                                max_tokens=200, temperature=0.6, timeout=120, video=True) or "")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[script] gancho de retorno falhou: {e}")
            return None
        nova = next((l.strip().strip('"«»') for l in resp.strip().splitlines() if l.strip()), "")
        motivo = _gancho_ruim(nova, frases)
        if not motivo:
            return viralizador.anti_ban(nova)
        logging.info(f"[script] gancho recusado ({motivo}), tentativa {tentativa + 1}: «{nova}»")
    return None


CTAS_FIM = [
    "E você, o que faria no lugar dele? Comenta aí embaixo!",
    "Se curtiu essa história, deixa o like e me conta nos comentários!",
    "Gostou? Segue o canal que amanhã tem mais história assim.",
    "Comenta aí o que você achou disso!",
    "Deixa seu like se você também ficou chocado com esse final!",
    "Quer a parte dois? Escreve 'quero' nos comentários!",
]


def cta_fim(semente=""):
    """Frase de CTA do fim (like/comentário/seguir), em rodízio estável pela semente (id do vídeo)."""
    import hashlib
    return CTAS_FIM[int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(CTAS_FIM)]


def rewrite_to_file(transcript, out_txt, target_lines=40):
    """Reescreve e salva o roteiro (uma frase por linha). Retorna nº de frases."""
    linhas = [l for l in rewrite(transcript, target_lines=target_lines) if not resposta_de_erro(l)]
    # 23/10 (mushishi): sobrou 1 frase (a do erro) + o CTA e o vídeo saiu assim — roteiro curto demais = falha
    if len(linhas) < max(2, target_lines // 4):
        logging.error(f"[script] roteiro com {len(linhas)} frase(s) pra {target_lines} pedidas — falha, não narra")
        return 0
    linhas, _ = _tirar_abertura_vazia(linhas)
    from pathlib import Path
    Path(out_txt).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return len(linhas)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    src = sys.argv[1]           # arquivo com a transcrição crua
    out = sys.argv[2] if len(sys.argv) > 2 else "roteiro.txt"
    target = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    from pathlib import Path
    n = rewrite_to_file(Path(src).read_text(encoding="utf-8"), out, target_lines=target)
    print(f"{n} frases → {out}")
