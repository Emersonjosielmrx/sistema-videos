# -*- coding: utf-8 -*-
r"""humor_narrador.py — passada de HUMOR no roteiro do LONGO (26/11; dona: "analise e implemente da melhor maneira").

Por quê (D:\video-fila\memes_melhoria\ANALISE_HUMOR_VIRJAO_MOMO.md; fala real x nossos roteiros, por mil palavras):
os nossos longos saem como TEXTO LIDO, os narradores de referência REAGEM ao vivo. Narrador em 1ª pessoa: Virjão 8,6 /
Momo 13,7 x nosso 0,2; pergunta 11-18 x 1; interjeição 4-9 x 1; '!' e '...' = ZERO em todos os nossos longos (a IA do
roteiro não escreve); "Sinceramente, esse cara não aprende, né?" 3x no mesmo vídeo; a piada de virada ("Mentiraaa,
galera!") é pedida no prompt e nunca sai; "nosso garoto" 7,7/mil (Momo real 0,8).

polir(frases, tempos) -> (frases, tempos). Só roda em roteiro NOVO (anime_script.rewrite_longo_com_tempo chama antes de
guardar no cache; roteiro já pronto/cacheado não muda). Só anime/manhwa (nicho informativo e 1ª pessoa ficam fora).
Cada passo tem chave; HUMOR_POLIR=0 desliga tudo:
  1. HUMOR_DEDUP=0      comentário repetido no vídeo sai (o 1º fica)
  2. HUMOR_ABERTURAS=0  'Sinceramente,', 'Cá entre nós,'... no máximo N vezes cada; no excesso a abertura sai e a
                        frase fica ('Sinceramente, esse cara...' -> 'Esse cara...')
  3. HUMOR_APELIDO=0    'nosso garoto' no máximo 1 a cada HUMOR_APELIDO_CADA (40) frases; o resto vira 'o prota'
                        (ou o apelido de prota do narrador, ex. 'protinha') — nunca 'o cara', que é dos outros
  4. HUMOR_REACOES=0    a IA SUGERE reações curtas do narrador (1ª pessoa, pergunta incrédula, imitação caricata,
                        piada de virada em 2 linhas, piada recorrente com placar, golpe com onomatopeia) e temperos
                        (interjeição + '!' numa frase de impacto que já existe). O CÓDIGO confere cada uma: curta, sem
                        palavrão (a postagem reprova), sem ofender o público, sem cena triste, sem repetir, sem começar
                        igual demais, espaçada (HUMOR_ESPACO), dentro do teto de frases do longo. A reação entra DEPOIS
                        da frase, com o mesmo segundo dela (a imagem segue na mesma cena). Fatos, ordem e tempos do
                        roteiro não mudam.
Densidade (padrão, por frase de roteiro ~5-6 s): até 1 reação a cada HUMOR_CADA=14 frases (~1 a cada 2 min na prática)
e 1 tempero a cada HUMOR_TEMPERO_CADA=20. IA: 1 chamada a cada HUMOR_BLOCO=80 frases.
Perfil de cada narrador: humor_narradores.json (ao lado): interjeições, fala com o público, bordões, apelidos.
"""
import hashlib
import json
import logging
import os
import re
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PERFIS = AQUI / "humor_narradores.json"

# igual ao colab/postar_longos._PALAVRAO (palavrão na narração = longo NÃO sobe) + variações que ele não pega
_PALAVRAO = re.compile(r"\b(caralh\w*|porras?|put[ao]s?|puta\w*|merda\w*|fod[aeiô]\w*|cacete|bucet\w*|arrombad\w*|"
                       r"viad[oa]s?|desgraçad\w*|desgraç\w*|fdp|cuz[aã]o|carai|bost\w*)\b", re.I)
_OFENDE = re.compile(r"(?i)insignificante|\btol[oa]s?\b|idiota|burr[oa]|imbecil|est[uú]pid|retardad|verme|\blixo\b|"
                     r"ot[aá]ri|ignorante|plebe|incompetent")
_PUBLICO = re.compile(r"(?i)\b(voc[eê]s?|c[eê]s|galera|povo|rapaziada|molecada|quem (t[aá]|est[aá]) vendo)\b")
_TRISTE = re.compile(r"(?i)\b(morr\w*|mort[oa]s?|morte|falec\w*|funeral|enterr\w*|luto|velório|assassin\w*|suicid\w*|"
                     r"estupr\w*|abus\w*|câncer|sacrific\w*|massacr\w*|devorad\w*|decapitad\w*|chorando|lágrimas|"
                     r"desviv\w*|órf[ãa]o?)\b")
ABERTURAS = ("Cá entre nós,", "E olha a ironia:", "Sinceramente,", "Vamos combinar,", "Convenhamos,", "Pra mim,",
             "Na boa,", "Confesso que", "Imagina só", "Repara que")
_ABERT_TIRAVEL = ("Cá entre nós,", "E olha a ironia:", "Sinceramente,", "Vamos combinar,", "Convenhamos,", "Pra mim,",
                  "Na boa,")
TIPOS = ("reacao", "pergunta", "imitacao", "virada", "gag", "golpe")
_INTERJ_OK = ("Nossa,", "Eita,", "Rapaz,", "Caramba,", "Olha só,", "Pô,", "Ih,", "Vixe,", "Ixi,", "Meu Deus,", "Caraca,")
_RX_JA_INTERJ = re.compile(r"(?i)^(nossa|eita|rapaz|caramba|olha|pô|po|ih|vixe|ixi|meu deus|caraca|ai|mano|cara)\b")
_RX_VIRADA = re.compile(r"(?i)^(mentira+|brincadeira|t[oô] (zoando|brincando)|zoeira)\b")
# piada recorrente com escalada (a Momo: "a sanidade do coitado caiu pra 10"). 1 só por vídeo; o CÓDIGO escreve a
# frase (o molde) e põe o número — a IA só escolhe ONDE.
GAGS = {
    "sanidade": ("cena de susto, absurdo ou humilhação que deixa o protagonista (ou quem sofre na cena) abalado",
                 "E a sanidade do coitado caiu pra {N}%.", [80, 50, 25, 10, 0]),
    "subestimou": ("alguém subestimou o protagonista e se deu mal por isso",
                   "Mais um que subestimou o prota. Placar: {N} a zero!", [1, 2, 3, 4, 5]),
    "vexame": ("o rival/vilão/arrogante passou vergonha ou se deu mal de novo",
               "Placar de vexames do bonitão: {N} a zero, meu povo!", [1, 2, 3, 4, 5]),
}
_SEM_HUMOR = {"fatos", "curiosidades", "historia_mitologia", "animais", "esportes", "financas", "dorama",
              "filme_sem_voz"}


def _lig(chave, padrao="1"):
    return os.environ.get(chave, padrao) != "0"


def _num(chave, padrao):
    try:
        return float(os.environ.get(chave) or padrao)
    except ValueError:
        return float(padrao)


def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def _parecida(a, b, lim=0.6):
    wa, wb = set(w for w in _norm(a) if len(w) > 2), set(w for w in _norm(b) if len(w) > 2)
    if len(wa) < 3 or len(wb) < 3:
        return " ".join(_norm(a)) == " ".join(_norm(b))
    return len(wa & wb) / len(wa | wb) >= lim


def _sem_abertura(f):
    for a in ABERTURAS:
        if f.startswith(a):
            return f[len(a):].strip()
    return None


def _e_comentario(f):
    return _sem_abertura(f) is not None


# ── 1. comentário repetido ────────────────────────────────────────────────────────────────────────────────────────
def tirar_comentario_repetido(frases, tempos):
    vistos, out_f, out_t, tirados = [], [], [], 0
    for f, t in zip(frases, tempos):
        corpo = _sem_abertura(f)
        if corpo is not None:
            if any(_parecida(corpo, v, 0.7) for v in vistos):
                tirados += 1
                continue
            vistos.append(corpo)
        out_f.append(f)
        out_t.append(t)
    return out_f, out_t, tirados


# ── 2. aberturas de comentário ────────────────────────────────────────────────────────────────────────────────────
def limitar_aberturas(frases):
    teto = max(2, len(frases) // 250)
    usos, tiradas, out = {}, 0, []
    for f in frases:
        ab = next((a for a in _ABERT_TIRAVEL if f.startswith(a)), None)
        if ab:
            usos[ab] = usos.get(ab, 0) + 1
            if usos[ab] > teto:
                resto = f[len(ab):].strip()
                if len(resto.split()) >= 3:
                    f = resto[:1].upper() + resto[1:]
                    tiradas += 1
        out.append(f)
    return out, tiradas


# ── 3. "nosso garoto" demais ──────────────────────────────────────────────────────────────────────────────────────
_RX_NG = re.compile(r"\b(o|do|no|pro|pelo|ao|com o|que o)\s+nosso garoto\b|^Nosso garoto\b", re.I)


def variar_nosso_garoto(frases, apelidos=()):
    cada = int(_num("HUMOR_APELIDO_CADA", 40))
    alt = ["prota"] + [a.split()[-1] for a in apelidos
                       if "prot" in a.lower() and a.split()[-1].lower() not in ("prota", "protagonista")]
    ultimo, trocas, k, out = -10 ** 6, 0, 0, []
    for i, f in enumerate(frases):
        if _RX_NG.search(f):
            if i - ultimo >= cada:
                ultimo = i
            else:
                def troca(m):
                    nonlocal k
                    novo = alt[k % len(alt)]
                    k += 1
                    return f"{m.group(1)} {novo}" if m.group(1) else f"O {novo}"
                f2 = _RX_NG.sub(troca, f)
                if f2 != f:
                    trocas += 1
                    f = f2
        out.append(f)
    return out, trocas


# ── 4. reações do narrador ────────────────────────────────────────────────────────────────────────────────────────
def _perfil():
    try:
        todos = json.loads(PERFIS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        todos = {}
    voz = (os.environ.get("VOZ_CLONADA") or os.environ.get("NARRADOR") or "").strip().lower()
    base = {k: v for k, v in (todos.get("_generico") or {}).items() if k != "exemplos"}
    for k, v in (todos.get(voz) or {}).items():
        if v and k != "exemplos":  # exemplos = transcrição automática com erro: a IA copiava ("Eu chocar a Macho")
            base[k] = v
    return voz or "generico", base


def metricas(frases):
    txt = " ".join(frases)
    n = max(1, len(txt.split()))

    def c(rx):
        return round(1000 * len(re.findall(rx, txt, re.I)) / n, 1)
    return {"1a_pessoa": c(r"\b(eu|mim|comigo)\b"), "pergunta": c(r"\?"), "exclamacao": c(r"!"),
            "interjeicao": c(r"\b(nossa|eita|caramba|caraca|rapaz|meu deus|ai ai|vixe|ixi|pô|olha só)\b"),
            "reticencia": c(r"\.\.\.|…")}


_SISTEMA = (
    "Você é o NARRADOR de um canal brasileiro de recap de anime/manhwa, assistindo a história JUNTO com o público e "
    "REAGINDO ao vivo, como os narradores brasileiros que mais dão views. Você NÃO reescreve o roteiro: só aponta onde "
    "o narrador PARA meio segundo e solta uma reação curta. Responda SÓ com JSON válido, sem texto antes ou depois.")

_MODELOS = """TIPOS DE REAÇÃO (cada uma = 1 linha falada de 3 a 14 palavras, com pontuação viva: ! ? ...):
- reacao: o narrador reage em 1ª PESSOA ao que ACABOU de acontecer. Ex.: "Nossa, eu jamais teria coragem de fazer isso!" / "Eu já teria saído correndo, galera." / "Isso aqui não é possível não!"
- pergunta: pergunta incrédula de quem não acredita, repetindo o absurdo. Ex.: "Pera aí... ele pagou mil moedas num pão?" / "Cadê o cérebro desse cara?" / "Como assim ela nem percebeu?"
- imitacao: o narrador imita o personagem de jeito exagerado, com fala arrastada ou alongada. Ex.: 'E o vilão todo cheio de pose: "Eu... sou... invencíveeel!"' / 'E ela toda dengosa: "Ai, que medinho..."'
- virada: piada CONTADA em 2 linhas. Linha 1 = ameaça/afirmação exagerada terminando em "hein?!" ou "..."; linha 2 = só a virada, começando com "Mentiraaa", "Brincadeira" ou "Tô zoando". Ex.: ["Se esse moleque apanhar de novo, eu paro de narrar essa obra, hein?!", "Mentiraaa, galera! Bora ver isso aí!"]
- gag: a PIADA RECORRENTE do vídeo (indicada abaixo). Só diga ONDE (depois_de); o texto é fixo, escreva "linhas": ["gag"].
- golpe: em luta, golpe narrado como locutor, com onomatopeia. Ex.: "E toma-lhe tijolada! Pá!" / "Voadora no peito, meu povo!"
TEMPERO (separado): numa frase de IMPACTO que já existe (susto, absurdo, golpe, virada), o narrador abre com uma
interjeição e fecha com exclamação, sem mudar mais NADA. Indique: {"tipo": "tempero", "frase": <n>, "inicio": "Eita,",
"fim": "!"}. inicio = uma de: Nossa, | Eita, | Rapaz, | Caramba, | Olha só, | Pô, | Ih, | Vixe, | Caraca, | Meu Deus,
fim = "!" ou "?!" ou "...".
"""


def _prompt(bloco, ini, perfil, gag, ja, max_ops, max_temp, viradas_ok, gastas):
    linhas = "\n".join(f"{ini + i}| {f}" for i, f in enumerate(bloco))
    _g, (g_quando, g_molde, _seq) = gag
    return (
        _MODELOS +
        f"\nJEITO DESTE NARRADOR — interjeições: {', '.join(perfil.get('interjeicoes', []))}; fala com o público: "
        f"{', '.join(perfil.get('fala_com_publico', []))}. Use cada expressão dele no máximo 1 vez neste trecho.\n"
        f"\nPIADA RECORRENTE deste vídeo (tipo gag): quando houver {g_quando}. Frase fixa: \"{g_molde}\". No máximo 1 "
        "vez neste trecho e só se a cena pedir.\n"
        "\nREGRAS QUE NÃO SE QUEBRAM:\n"
        f"- Até {max_ops} reações e até {max_temp} temperos neste trecho, só nos MELHORES momentos (menos se o trecho "
        "for calmo). Misture os tipos: no máximo metade em 1ª pessoa ('eu').\n"
        "- Momentos que pedem: absurdo, burrice, mentira descarada, susto, humilhação, poder exagerado, vergonha, "
        "decisão idiota, luta. NUNCA em morte, luto, choro de verdade, abuso ou cena triste.\n"
        "- NUNCA invente fato nem adiante o que vem depois. Reaja ao que a frase 'depois_de' acabou de contar.\n"
        "- SEM palavrão nenhum (o vídeo é reprovado). Nunca xingue nem diminua quem assiste.\n"
        + ("" if viradas_ok else "- NÃO use o tipo virada neste trecho.\n") +
        "- Não repita nada parecido com estas reações que o vídeo já tem: " + (" | ".join(ja[-12:]) or "(nenhuma)")
        + "\n- NÃO comece reação com estas palavras (já usadas demais): "
        + (", ".join(f'"{a}"' for a in gastas) or "(nenhuma)") + "\n"
        "\nResponda SÓ: {\"ops\": [{\"tipo\": \"pergunta\", \"depois_de\": <número da frase>, \"linhas\": [\"...\"]}, "
        "{\"tipo\": \"tempero\", \"frase\": <número>, \"inicio\": \"Eita,\", \"fim\": \"!\"}]}\n"
        "\nTRECHO (número| frase):\n" + linhas)


def _json(resp):
    m = re.search(r"\{.*\}", resp or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


def _linha_ok(s, todas):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) >= 2 and s[0] == s[-1] == '"':
        s = s[1:-1].strip()
    if not s:
        return None, "vazia"
    if not 2 <= len(s.split()) <= 18:
        return None, "tamanho"
    if _PALAVRAO.search(s):
        return None, "palavrão"
    if _OFENDE.search(s) and _PUBLICO.search(s):
        return None, "ofende público"
    if _TRISTE.search(s):
        return None, "triste"
    if any(_parecida(s, t) for t in todas):
        return None, "repetida"
    if s[-1] not in ".!?…\"":
        s += "!"
    return s[:1].upper() + s[1:], None


_RX_FIGURADO = re.compile(r"(?i)\b(morr\w*|mat\w*) (de|a) (medo|rir|vergonha|saudade|fome|sono|curiosidade|"
                          r"t[eé]dio|inveja|raiva|calor|frio|ci[uú]mes?)\b")


def _cena_triste(frases, i):
    viz = _RX_FIGURADO.sub(" ", " ".join(frases[max(0, i - 1): i + 2]))
    if _TRISTE.search(viz):
        return True
    try:
        import memes_visuais
        return memes_visuais.triste(viz)
    except Exception:  # noqa: BLE001
        return False


_NAO_NOME = {"o", "a", "os", "as", "ele", "ela", "eles", "elas", "mas", "e", "só", "aí", "então", "quando", "no", "na",
             "um", "uma", "isso", "esse", "essa", "de", "do", "da", "logo", "agora", "depois", "antes", "nisso"}


def _temperar(f, ini_t, fim_t):
    corpo = f.rstrip(".!?… ")
    p1 = corpo.split()[0] if corpo.split() else ""
    if not (p1[:1].isupper() and p1.lower().strip(",") not in _NAO_NOME):
        corpo = corpo[:1].lower() + corpo[1:]
    return f"{ini_t} {corpo}{fim_t}"


def reacoes(frases, tempos, gerar=None):
    """(frases, tempos, relatorio). gerar(prompt, system) -> texto (padrão: claude_client.generate_text)."""
    if gerar is None:
        import claude_client
        if not claude_client.is_available():
            return frases, tempos, {"pulou": "IA indisponível"}

        def gerar(p, s):
            return claude_client.generate_text(p, system=s, max_tokens=2500, temperature=0.7, timeout=180)
    voz, perfil = _perfil()
    n = len(frases)
    teto = int(_num("LONGO_TETO_FRASES", 1500))
    folga = (teto - n) if teto > 0 else 10 ** 6
    if folga <= 0:
        return frases, tempos, {"pulou": "roteiro já no teto de frases"}
    bloco_n = int(_num("HUMOR_BLOCO", 80))
    # 26/11 (teste em 2 roteiros reais): com 20/25 saiu 1 reação a cada ~37 frases (~3,5 min). Com o teto de começo
    # repetido, 14/20 fica ~1 a cada 2 min sem cansar (os de referência reagem bem mais: 1 a cada 3-5 frases).
    cada, cada_temp = _num("HUMOR_CADA", 14), _num("HUMOR_TEMPERO_CADA", 20)
    espaco = int(_num("HUMOR_ESPACO", 8))
    h = int(hashlib.md5((frases[0] if frases else "").encode("utf-8")).hexdigest(), 16)
    gag_nome = list(GAGS)[h % len(GAGS)]
    gag = (gag_nome, GAGS[gag_nome])
    gag_seq, gag_usos, gag_ultimo = GAGS[gag_nome][2], 0, -10 ** 6
    max_viradas, viradas = max(1, n // 300), 0
    # teto de começo igual: 1ª palavra e 2 primeiras (o teste mostrou "Pera aí..."/"Rapaz, até eu" em quase todas)
    teto_p1, teto_p2 = max(3, n // 100), max(2, n // 200)
    p1s, p2s = {}, {}
    todas, ja = list(frases), [f for f in frases if _e_comentario(f)]
    inserir, temperar, recusas, tipos = {}, {}, {}, {}

    def recusa(m):
        recusas[m] = recusas.get(m, 0) + 1

    def comeco(s):
        w = _norm(s)
        return (w[0] if w else ""), " ".join(w[:2])

    for ini in range(0, n, bloco_n):
        bloco = frases[ini: ini + bloco_n]
        if len(bloco) < 10:
            break
        max_ops = max(1, round(len(bloco) / cada))
        max_temp = round(len(bloco) / cada_temp) if cada_temp > 0 else 0
        gastas = sorted({a for a, c in p1s.items() if c >= teto_p1} | {a for a, c in p2s.items() if c >= teto_p2})
        try:
            resp = gerar(_prompt(bloco, ini, perfil, gag, ja, max_ops, max_temp, viradas < max_viradas, gastas),
                         _SISTEMA)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[humor] bloco {ini}: IA falhou ({type(e).__name__})")
            recusa("IA falhou")
            continue
        j = _json(resp)
        if not j or not isinstance(j.get("ops"), list):  # 26/11: 1 de cada ~4 blocos vinha sem JSON — tenta 1x mais
            try:
                j = _json(gerar(_prompt(bloco, ini, perfil, gag, ja, max_ops, max_temp, viradas < max_viradas, gastas)
                                + "\nIMPORTANTE: responda APENAS o JSON, começando com { e terminando com }.", _SISTEMA))
            except Exception:  # noqa: BLE001
                j = None
        if not j or not isinstance(j.get("ops"), list):
            recusa("resposta sem JSON")
            continue
        aceitos, temps, em_eu = 0, 0, 0
        for op in j["ops"]:
            if not isinstance(op, dict):
                continue
            tipo = str(op.get("tipo", "")).strip().lower()
            if tipo == "tempero":
                try:
                    k = int(op.get("frase"))
                except (TypeError, ValueError):
                    recusa("tempero sem posição")
                    continue
                ini_t, fim_t = str(op.get("inicio", "")).strip(), str(op.get("fim", "")).strip()
                if temps >= max_temp or not (ini <= k < ini + len(bloco)) or k in temperar:
                    continue
                p1 = _norm(ini_t)[0] if _norm(ini_t) else ""
                if ini_t not in _INTERJ_OK or fim_t not in ("!", "?!", "...") or _RX_JA_INTERJ.match(frases[k]) \
                        or frases[k].rstrip().endswith(("!", "?")) or _cena_triste(frases, k) \
                        or _e_comentario(frases[k]) or len(frases[k].split()) > 22 or p1s.get(p1, 0) >= teto_p1:
                    recusa("tempero inválido")
                    continue
                temperar[k] = (ini_t, fim_t)
                p1s[p1] = p1s.get(p1, 0) + 1
                temps += 1
                continue
            if aceitos >= max_ops or sum(len(v) for v in inserir.values()) >= folga - 1:
                continue
            try:
                k = int(op.get("depois_de"))
            except (TypeError, ValueError):
                recusa("sem posição")
                continue
            ls = op.get("linhas") or ([op["linha"]] if op.get("linha") else [])
            if tipo not in TIPOS or not (ini <= k < ini + len(bloco)) or not isinstance(ls, list) or not ls:
                recusa("formato")
                continue
            if k in inserir or any(abs(k - j_) < espaco for j_ in inserir):
                recusa("perto de outra")
                continue
            if _cena_triste(frases, k):
                recusa("cena triste")
                continue
            if any(_e_comentario(f) for f in frases[max(0, k - 1): k + 2]):
                recusa("colada em comentário")
                continue
            if tipo == "virada":
                if viradas >= max_viradas or len(ls) != 2 or not _RX_VIRADA.match(str(ls[1]).strip()):
                    recusa("virada inválida")
                    continue
            elif tipo == "gag":
                if gag_usos >= len(gag_seq) or k - gag_ultimo < 60:
                    recusa("gag fora de hora")
                    continue
                ls = [GAGS[gag_nome][1].replace("{N}", str(gag_seq[gag_usos]))]
            else:
                ls = ls[:1]
            boas, motivo = [], None
            for s in ls:
                s2, motivo = _linha_ok(s, todas + boas)
                if not s2:
                    break
                p1, p2 = comeco(s2)
                if tipo != "gag" and (p1s.get(p1, 0) >= teto_p1 or p2s.get(p2, 0) >= teto_p2):
                    motivo = "começo repetido"
                    break
                boas.append(s2)
            if motivo:
                recusa(motivo)
                continue
            eu = any(re.search(r"(?i)\b(eu|mim|comigo)\b", s) for s in boas)
            if eu and em_eu >= max(1, max_ops // 2):
                recusa("1ª pessoa demais no trecho")
                continue
            em_eu += 1 if eu else 0
            inserir[k] = boas
            for s2 in boas:
                p1, p2 = comeco(s2)
                p1s[p1] = p1s.get(p1, 0) + 1
                p2s[p2] = p2s.get(p2, 0) + 1
            todas += boas
            ja += boas
            aceitos += 1
            tipos[tipo] = tipos.get(tipo, 0) + 1
            if tipo == "virada":
                viradas += 1
            if tipo == "gag":
                gag_usos += 1
                gag_ultimo = k
    try:
        from viralizador import anti_ban
    except Exception:  # noqa: BLE001
        def anti_ban(x):
            return x
    out_f, out_t = [], []
    for i, (f, t) in enumerate(zip(frases, tempos)):
        if i in temperar:
            f = anti_ban(_temperar(f, *temperar[i]))
        out_f.append(f)
        out_t.append(t)
        for s in inserir.get(i, []):
            out_f.append(anti_ban(s))
            out_t.append(t)  # mesmo segundo da frase: a imagem continua a mesma cena
    return out_f, out_t, {"voz": voz, "gag": gag_nome, "linhas_novas": sum(len(v) for v in inserir.values()),
                          "momentos": len(inserir), "temperadas": len(temperar), "tipos": tipos, "recusas": recusas}


def _nicho_com_humor():
    tipo = os.environ.get("PARCEIRO_TIPO", "anime")
    nicho = os.environ.get("NICHO_CLONE", tipo)
    return tipo not in _SEM_HUMOR and nicho not in _SEM_HUMOR


def polir(frases, tempos, gerar=None):
    """Passos 1-4 (ver o topo). Erro num passo = aquele passo não acontece; o roteiro nunca se perde."""
    if not _lig("HUMOR_POLIR") or not frases or len(frases) != len(tempos) or not _nicho_com_humor():
        return frases, tempos
    antes, rel = metricas(frases), {}
    try:
        if _lig("HUMOR_DEDUP"):
            frases, tempos, rel["comentarios_repetidos_tirados"] = tirar_comentario_repetido(frases, tempos)
        if _lig("HUMOR_ABERTURAS"):
            frases, rel["aberturas_tiradas"] = limitar_aberturas(frases)
        if _lig("HUMOR_APELIDO"):
            frases, rel["nosso_garoto_trocados"] = variar_nosso_garoto(frases, _perfil()[1].get("apelidos", []))
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[humor] limpeza falhou ({type(e).__name__}: {e})")
    if _lig("HUMOR_REACOES"):
        try:
            f2, t2, rel["reacoes"] = reacoes(frases, tempos, gerar)
            if len(f2) == len(t2) and len(f2) >= len(frases):
                frases, tempos = f2, t2
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[humor] reações falharam ({type(e).__name__}: {e}) — roteiro segue sem elas")
    logging.info(f"[humor] {rel} | por mil palavras antes {antes} depois {metricas(frases)}")
    return frases, tempos
