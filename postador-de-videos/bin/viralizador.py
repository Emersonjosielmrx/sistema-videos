"""viralizador.py — reescreve a NARRAÇÃO falada antes do TTS (T1, porte do CENSOR CIRÚRGICO n8n).

Duas camadas:
  anti_ban(texto)  — SEMPRE on: suaviza termos que dão strike no YouTube, sem mudar o sentido.
  viralizar(texto) — flag VIRAL_SLANG=1: gírias gen-z SEGURAS e pontuais (não mexe em
                     pronome/sujeito; as agressivas do n8n foram deixadas de fora de propósito).

Fonte da verdade: nó CENSOR CIRÚRGICO de fabrica-de-animes-1. Regex case-insensitive.
Aplicado em _tts_filter.clean_for_tts → áudio e legenda batem (ambos passam aqui).
"""
import os
import re

_VIDA = {"matou": "tirou a vida", "mataram": "tiraram a vida", "matar": "tirar a vida", "matando": "tirando a vida",
         "mata": "tira a vida", "assassinou": "tirou a vida", "assassinaram": "tiraram a vida",
         "assassinar": "tirar a vida", "assassinando": "tirando a vida"}
_POSSE = {"me": "minha", "te": "sua", "nos": "nossa", "lhe": "sua"}
_DE = {"o": "do", "a": "da", "os": "dos", "as": "das", "ele": "dele", "ela": "dela", "eles": "deles", "elas": "delas"}


def _tirar_vida(m):
    """matar/assassinar conjugado -> "tirar a vida" com a mesma pessoa/tempo e a preposição certa."""
    clitico, verbo, obj = m.group(1), m.group(2), m.group(3)
    s = _VIDA[verbo.lower()]
    if clitico:
        s = s.replace("a vida", f"a {_POSSE[clitico.lower()]} vida") + (obj or "")
    elif obj:
        s += " " + _DE[obj.strip().lower()]
    else:
        s += " de"
    return s[0].upper() + s[1:] if (clitico or verbo)[0].isupper() else s


# 29/10 noite (dona: "libere a palavra sangue; suco de tomate só nas partes MUITO violentas — às vezes fala de sangue como
# descendência e 'suco de tomate' fica estranho"): sangue/sangrar só viram "suco de tomate"/"vazar suco" quando a FRASE
# tem gore pesado (jorrar, poça, banho, tripas, cabeça arrancada...). "Sangue real", "do mesmo sangue" ficam.
# 13/11 (achado A3 do agente online, reproduzido no D:): a lista tinha palavras soltas que não são gore sozinhas
# ("membros da guilda", "banho", "rio de Janeiro", "coberto de neve", "lavou", "arrancou o carro") e a frase comum
# virava "desviveu"/"suco de tomate" — o que a dona mandou parar em 29-30/10. Agora só valem coladas no que as torna
# gore. Lista antiga em _GORE_ANTIGA (VIRALIZADOR_GORE_ANTIGA=1 volta).
_GORE_ANTIGA = re.compile(r"jorr|espirr|esguich|po[çc]a|banho|rio de|litros|encharc|ensopad|cobert[oa]s? de|lav(ad|ou)|cuspi"
                          r"|vomit|v[ôo]mit|tripa|v[íi]scer|entranha|arranc|esmag|despeda[çc]|dilacer|mutil|esquartej|decapit"
                          r"|degol|perder a cabe[çc]a|cabe[çc]a rol|membros|rasgad|carnific|massacr|chacin", re.IGNORECASE)
_GORE = _GORE_ANTIGA if __import__("os").environ.get("VIRALIZADOR_GORE_ANTIGA") == "1" else re.compile(
    r"jorr|espirr|esguich|"
    r"(?:po[çc]a|banho|rio|litros|mar) de sangue|"
    r"(?:encharcad|ensopad|cobert|lavad|banhad)[oa]s? (?:de|em) sangue|"
    r"(?:cusp|v[oô]mit)\w+ sangue|"
    r"\btripas?\b|v[íi]sceras?|entranhas?|"
    r"arranc\w+ (?:(?:a|o|as|os|um|uma|seu|sua|seus|suas|d?el[ea]) )?(?:cabe[çc]a|bra[çc]o|perna|cora[çc][ãa]o|olho|"
    r"l[íi]ngua|membro|pele|unha|dente|m[ãa]o|dedo)|"
    r"esmag\w+ (?:(?:a|o|as|os|seu|sua) )?(?:cabe[çc]a|cr[âa]nio|corpo|peito|m[ãa]o|osso)|"
    r"membros (?:arrancad|decepad|espalhad|cortad|dilacerad)|"
    r"rasgad[oa]s? ao meio|partid[oa]s? ao meio|"
    r"despeda[çc]|dilacer|mutil|esquartej|decapit|degol|perder a cabe[çc]a|cabe[çc]a rol|"
    r"carnific|massacr|chacin", re.IGNORECASE)


_CENSURA = {"trocou": False, "n": 0}  # 30/10: quantas trocas de gore já houve (piscada do narrador)


def _so_gore(troca):
    """troca = texto ou função(match) -> texto. Só troca quando a FRASE tem gore pesado (30/10: vale também pra
    morte/matar/assassino/tortura — dona: 'veja outras que não precisam, só pro contexto onde o YouTube não veicula bem')."""
    def f(m):
        txt, i = m.string, m.start()
        ini = max(txt.rfind(c, 0, i) for c in ".!?\n") + 1
        fins = [p for p in (txt.find(c, m.end()) for c in ".!?\n") if p >= 0]
        frase = txt[ini:min(fins) if fins else len(txt)]
        if not _GORE.search(frase):
            return m.group(0)
        _CENSURA["trocou"] = True
        if callable(troca):
            return troca(m)
        return troca[0].upper() + troca[1:] if m.group(0)[0].isupper() else troca
    return f


# 30/10 (dona: "adicionar frases como 'disso o YouTube não gosta', como outros narradores usam — aí as pessoas sabem que é
# censurado"): ANIME_PISCADA_CENSURA=1 (variante A/B do longo) = 1 a cada 3 trocas de gore o narrador pisca pro público.
_PISCADAS = ["Vocês entenderam, né? O YouTube não deixa eu falar a palavra.",
             "Eu sei, eu sei, mas o YouTube não gosta dessa palavra.",
             "Tô tendo que maneirar aqui, senão o YouTube me pega.",
             "Usa a imaginação aí, porque o YouTube não deixa eu falar do jeito certo."]


# (regex, substituição) — anti-ban. Ordem: específico antes de genérico.
# Backup: viralizador_backup_20260705.py (versão pré-expansão)
_ANTI_BAN = [
    # --- classificação etária ---
    (r"18\s*(\+|mais)", "conteúdo maduro"),
    (r"hentai|ecchi|porn[oô]", "anime de cultura"),
    (r"proibid[oa] para menores", "exclusivo para adultos"),

    # --- violência sexual ---
    (r"estuprada", "forçada"),
    (r"estuprado", "forçado"),
    (r"estupro", "abuso"),
    (r"estuprar|estupr\w*|abus[oa] sexual", "forçar a barra"),
    (r"incesto", "tabu familiar"),
    (r"violar|viola[çc][ãa]o", "cruzar a linha"),

    # --- nudez e corpo ---
    (r"nudes|nudez|pelad[oa]|\bnua\b|\bnú\b|peladão|peladao", "sem roupa"),
    (r"fanservice", "agrado visual"),
    (r"calcinha\w*|lingerie", "roupa de baixo"),
    (r"cueca", "a peça de baixo"),
    (r"\bseios?\b", "os frontais"),

    # --- atos sexuais (específico antes de genérico) ---
    (r"sexo oral|boquete|fela[çc][ãa]o", "um talento com a boca"),
    (r"chupar|chupando|chupou", "usar a boca"),
    (r"mamar|mamando|mamou", "provar o sabor"),
    (r"engoli[r]-?los|engoli-los", "degustar tudo"),
    (r"penetra\b", "avança em"),
    (r"penetrou", "avançou"),
    (r"penetrando", "avançando"),
    (r"penetra[çc][ãa]o", "avanço profundo"),
    (r"penetr\w*", "avançar"),
    (r"sexo anal", "vuco-vuco diferente"),
    (r"\bsexo\b|coito|\btransa\b", "vuco-vuco"),
    (r"transarmos", "darmos um trato"),
    (r"transar|trepar|transou|transaram", "dar um trato"),
    (r"fod[êe]-?l[oa]", "pegar com tudo"),
    (r"\bfode\b", "pega pesado"),
    (r"fodendo", "pegando pesado"),
    (r"foder", "amar intensamente"),
    (r"(?<!se )metendo|meteu(?! nessa)|\bmeter\b(?!\s+nessa|\s+nesse|\s+nisso)", "mandando ver"),
    (r"cavalgando|cavalga\w*", "no comando"),
    (r"rebola\w*", "requebrar"),
    (r"menage|m[eé]nage|orgia", "festa privada"),

    # --- orgasmo e fluidos ---
    (r"gozou", "finalizou"),
    (r"gozando", "finalizando"),
    (r"gozar", "finalizar"),
    (r"gozei", "finalizei"),
    (r"gozaram", "finalizaram"),
    (r"\bgoza\b", "finaliza"),
    (r"ejacula[rçã]\w*", "finalizar"),
    (r"gozo\s+muito", "finalizo demais"),
    (r"\bgozo\b", "o gran finale"),
    (r"me excita\w*", "me acende"),
    (r"excita[çc][ãa]o", "fogaço"),
    (r"excitad[oa]", "aceso"),
    (r"excitante", "provocante"),
    (r"excita\w*", "acender"),
    (r"orgasmos", "clímaxes"),
    (r"orgasmo", "clímax"),

    # --- genitais ---
    (r"buceta|vagina|xereca|ppk|xana", "flor"),
    (r"\bpinto\b|\bpau\b|\brola\b|p[eê]nis|piroca", "instrumento"),
    (r"\bcu\b|\bcú\b|cuzão|cuzao|cuzinho|ânus|anus", "popô"),
    (r"clit[óo]ris", "o botão mágico"),
    (r"ere[çc][ãa]o", "animação"),

    # --- corpo ---
    (r"mamilos|tetas|\bpeitos\b", "dotes"),
    (r"\bbunda\b|\braba\b|n[áa]degas", "bumbum"),

    # --- masturbação e auto-prazer ---
    (r"se masturbou", "fez amor próprio"),
    (r"se masturbando", "fazendo amor próprio"),
    (r"se masturbar", "fazer amor próprio"),
    (r"se masturb\w*", "fazer amor próprio"),
    (r"masturba[çc][ãa]o", "amor próprio"),
    (r"masturb\w*", "amor próprio"),
    (r"bater\s+punhet\w*", "praticar amor próprio"),
    (r"punhet\w*", "amor próprio"),
    (r"se toc(ar|ava|ando|ou)\w*", "se cuidava"),

    # --- desejo e excitação ---
    (r"(muito|demais|tanto)\s+tes[ãa]o", r"\1 fogo"),
    (r"com\s+tes[ãa]o", "no fogo"),
    (r"tes[ãa]o|tesao", "fogo"),
    (r"er[oó]tic\w*", "picantes"),
    (r"tesud[oa]", "pegando fogo"),
    (r"molhad[oa]", "acesa"),
    (r"vol[úu]pia", "desejo intenso"),
    (r"lasc[ií]v\w*", "ardente"),
    (r"lux[úu]ria", "fogo interior"),

    # --- xingamentos sexuais ---
    (r"safad[oa]", "sem vergonha"),
    (r"pervertid[oa]", "mente criativa"),
    (r"gostos[oa]\b", "atraente"),
    (r"\btarad[oa]\b", "doido varrido"),
    (r"piranha|vadia|\bvagabunda\b", "dama da noite"),
    (r"putaria|puteiro|bordel|prost[ií]bulo", "casa de shows"),
    (r"prostitut\w*", "profissional do amor"),
    (r"ninfoman[ií]ac\w*", "insaciável"),
    (r"\bcorno\b|chifrudo", "premiado"),

    # --- fetiche/bdsm ---
    (r"sadomaso\w*|bdsm", "práticas intensas"),
    (r"fetiche", "preferência especial"),
    (r"submiss\w*", "obediente"),
    (r"\bdominação\b|\bdomina[çc][ãa]o\b", "controle total"),
    (r"\bdominad\w*", "no controle"),

    # --- gemidos ---
    (r"gemidos", "barulhinhos"),
    (r"gemido", "barulhinho"),
    (r"gemendo|\bgeme\b", "soltando uns sons"),
    (r"gemir", "soltar uns sons"),

    # --- sedução ---
    (r"sedu[çc][ãa]o", "encantamento"),
    (r"seduz\w*", "encanta"),

    # --- espiar ---
    (r"voyeur|espiando|espiar", "bisbilhotando"),
    (r"exibi[çc]\w*", "se mostrar"),
    (r"se despir|se despiu|se despida", "se descobrir"),
    (r"despir|despiu|despida", "tirar a roupa"),

    # --- violência ---
    (r"suic[íi]dio|se matar", "ir de base"),
    # 29/10: era tudo -> "desviver" sem conjugar ("cai no rio e desviver todos", Short d9bb92; "a desviver atlântica")
    # 30/10 (dona, depois do "sangue"): matar/morrer/morto/assassino em história de ficção o YouTube veicula; as trocas
    # ("desviveu", "sem vida", "tirar a vida") ficam SÓ quando a frase tem gore pesado (_so_gore), como o sangue
    (r"\b(?:(me|te|nos|lhe)\s+)?(matou|mataram|matar|matando|assassinou|assassinaram|assassinar|assassinando)\b"
     r"(\s+(?:o|a|os|as|ele|ela|eles|elas)\b)?", _so_gore(_tirar_vida)),
    (r"(?<!\ba )(?<!\bna )(?<!\bda )(?<!\bpela )(?<!\buma )(?<!\bnuma )(?<!\bessa )(?<!\bnessa )(?<!\besta )"
     r"(?<!\bnesta )\b()(mata)\b(\s+(?:o|a|os|as|ele|ela|eles|elas)\b)?", _so_gore(_tirar_vida)),
    (r"vida de(?=\s*(?:[.,!?;:…]|$))", "vida"),
    (r"\bfoi mort[oa]\b", _so_gore(lambda m: ("P" if m.group(0)[0] == "F" else "p") + "erdeu a vida")),
    (r"\bforam mort[oa]s\b", _so_gore(lambda m: ("P" if m.group(0)[0] == "F" else "p") + "erderam a vida")),
    (r"\bmorreu\b", _so_gore("desviveu")),
    (r"\bmorrer\b", _so_gore("desviver")),
    (r"\bmort[oa]s?\b", _so_gore("sem vida")),
    (r"\bassassinat\w*", _so_gore("crime")),
    (r"\bassassin[oa]s\b", _so_gore("criminosos")),
    (r"\bassassin\w*", _so_gore("criminoso")),
    (r"degola[rçã]\w*|decapita[rçã]\w*", "perder a cabeça"),
    (r"\bsangue\b", _so_gore("suco de tomate")),
    (r"\bsangrar\b", _so_gore("vazar suco")),
    (r"tortura[r]?\w*", _so_gore("interrogação intensa")),
    (r"enforc\w*", "gravata definitiva"),
    (r"esfaquead[oa]s?\b", "perfurados"),
    (r"esfaque\w*|apunhal\w*", "furar com metal"),
    (r"esquartej\w*", "desmontagem forçada"),

    # --- drogas e crimes ---
    (r"escrav[oa]|escravidão|escravid[aã]o", "servo"),
    (r"drogas|coca[ií]na|hero[ií]na|maconha|crack\b", "aditivos proibidos"),
    (r"[eê]xtase\b", "êxtase"),
    (r"overdose", "apagão químico"),
    (r"ped[oó]fil[oa]|pedofilia", "criminoso"),
    (r"traficante", "comerciante ilegal"),

    # --- palavrões genéricos ---
    (r"\bcacetes?\b", "caramba"),  # 23/10: "cacetete" virava "carambate"
    (r"caralhos", "carambas"),
    (r"caralho", "caramba"),
    (r"\bporra\b", "poxa"),
    (r"filh[oa]\s+da\s+puta", "filhote do capeta"),
    (r"\bputa\b", "dama"),
    (r"\bmerda\b", "droga"),
    (r"vai se f[ou]der", "vai ver se eu tô na esquina"),
    (r"desgra[çc]ad[oa]|desgra[çc]a\b", "infeliz"),
    (r"fodid[oa]|fudid[oa]", "ferrado"),
    (r"\bputo\b", "irritado"),
    (r"\bidiota\b", "jumento"),
    (r"\bimbecil\b", "lesado"),
    (r"retardad[oa]", "lerdo"),
    (r"\bcretino\b", "sem noção"),
    (r"\bbabaca\b", "mané"),
    (r"ot[áa]ri[oa]|otario", "trouxa"),
    (r"arrombad[oa]", "escancarado"),
    (r"\bcadela\b", "cachorrinha"),
    (r"\bgalinha\b(?=.*xinga|.*voc[êe])", "danada"),
    (r"viado|viada|\bbicha\b", "diferentão"),
    (r"\bbosta\b", "porcaria"),

    # --- termos de risco contextual (canal anal, etc) ---
    (r"canal anal", "caminho proibido"),
    (r"\banal\b", "proibido"),
    (r"\boral\b(?=.*sexo|\s+nele|\s+nela)", "especial"),
    (r"amante", "affair"),
    (r"\bsexy\b|\bsexi\b", "atraente"),
    (r"stripper|striptease", "dançarina"),
    (r"\bvirgem\b", "inexperiente"),
    (r"esperma", "sementinha"),
    (r"ass[eé]dio", "importunação"),
    (r"mijar|mijando|mijou", "fazer xixi"),
    (r"cagar|cagando|cagou", "fazer o número dois"),
    (r"transou|transaram|\btransa\b", "ficaram juntos"),
    (r"\bputinha\b", "danadinha"),
    (r"foda-se|foda se", "dane-se"),
    (r"\bfoda\b", "loucura"),
    (r"gostos[ãa]o|gostoson[ao]", "bonitão"),
    (r"\bs[êe]men\b", "essência"),  # 23/10: sem o limite "semente" virava "essênciate"
    (r"\bgala\b", "substância"),
    (r"\b[úu]tero\b", "interior"),
    (r"pega[çc][ãa]o", "uns amassos"),
    (r"sentando\s+(n[eo]l[ea]|sozinha|n[oa]\s)", r"indo com tudo \1"),
]

# (regex, substituição) — gírias virais SEGURAS (não mexem em pronome/sujeito).
_VIRAL = [
    (r"\bestudar\b|\bestudo\b", "upar"),
    (r"\bprova\b|\bteste\b", "o boss final"),
    (r"\bchefe\b|\bpatrão\b|\bpatrao\b", "o admin"),
    (r"\bdinheiro\b|\bsalário\b|\bsalario\b", "o gold"),
    (r"\btrabalho\b|\bemprego\b", "o grind"),
    (r"\bincrível\b|\bincrivel\b", "insano"),
    (r"\bvergonha\b", "cringe"),
    (r"\braiva\b|\bfúria\b|\bfuria\b", "tiltou"),
    (r"\bvenceu\b|\bganhou\b", "solou"),
    (r"\bperdeu\b", "foi de base"),
]

# ───────── PALAVRA INTEIRA + CONTEXTO (13/11) ─────────
# As regras acima casavam PEDAÇO de palavra, em toda narração (áudio e legenda): "prometeu" -> "promandando ver",
# "cometeu" -> "comandando ver", "enviado" -> "endiferentão", "diamante" -> "diaffair", "biscoito" -> "bisvuco-vuco",
# "atropelado" -> "atrosem roupa", "homenagem" -> "hofesta privadam", "manuscrito" -> "mpopôcrito", "a heroína da
# história" -> "a aditivos proibidos". Agora: (1) cada regra só casa palavra inteira (plural com "s" continua valendo);
# (2) palavra que normalmente é inocente só troca com contexto (tabela _GUARDAS); (3) _ANTES acerta gênero/conjugação.
_LETRA = r"[0-9A-Za-zÀ-ÖØ-öø-ÿ_]"
_FRONT_INI = rf"(?<!{_LETRA})"
_FRONT_FIM = rf"(?=s?(?!{_LETRA}))"


def _alternativas(rx):
    """Divide o padrão nas alternativas de 1º nível (o "|" fora de parênteses e de [])."""
    partes, atual, prof, classe, i = [], "", 0, False, 0
    while i < len(rx):
        c = rx[i]
        if c == "\\":
            atual += rx[i:i + 2]
            i += 2
            continue
        if classe:
            classe = c != "]"
        elif c == "[":
            classe = True
        elif c == "(":
            prof += 1
        elif c == ")":
            prof -= 1
        elif c == "|" and prof == 0:
            partes.append(atual)
            atual = ""
            i += 1
            continue
        atual += c
        i += 1
    return partes + [atual]


def _palavra_inteira(rx):
    out = []
    for alt in _alternativas(rx):
        if alt.startswith("(?<"):       # já tem "não vem depois de X": soma a fronteira de palavra
            ini = _FRONT_INI
        elif alt.startswith(("\\b", "\\d", "(?:(")) or not re.match(r"[A-Za-zÀ-ÿ\[(]", alt):
            ini = ""
        else:
            ini = _FRONT_INI
        fim = "" if re.search(r"(\\w\*|\\b|\\w\+|\)\?|\\s\+|\+\))$", alt) or alt.endswith(")") else _FRONT_FIM
        out.append(ini + alt + fim)
    return "|".join(out)


# sinais de cena picante na MESMA frase (inclui o que as regras de cima já trocaram)
_PICANTE = re.compile(
    r"na cama|pra cama|para a cama|motel|\bnu[as]?\b|sem roupa|pelad|beij|gemi|gemendo|barulhinho|tes[ãa]o|prazer|"
    r"\bsexo|vuco|transa|dar um trato|\bpeit|dotes|frontais|\bseios?\b|\bcoxas?\b|bumbum|\bbunda|calcinha|lingerie|"
    r"roupa de baixo|cueca|sedu[zç]|excit|\baces[oa]\b|safad|sem vergonha|tirou a roupa|tirar a roupa|strip|er[óo]tic|"
    r"picante|\bdesejo|ardente|\bflor\b|pop[ôo]|finaliz|\bcorpo d[ae]l[ae]|l[áa]bios|amasso|namorad|esposa|marido|"
    r"noite juntos|dormiu com|dormir com", re.I)
# (palavra casada, tipo, contexto). tipo: "so" = só troca se o contexto aparece na frase; "sem" = não troca se aparece;
# "depois" = não troca se o que vem logo depois casa; "antes" = não troca se o que vem logo antes casa
_GUARDAS = [(re.compile(a, re.I), tipo, re.compile(c, re.I)) for a, tipo, c in [
    (r"^(?:metendo|meteu|meter|pinto|pau|rola|molhad[oa]|virgem|gala|cavalg\w*|dominad\w*|domina[çc][ãa]o|"
     r"exibi[çc]\w*|se toc\w*|violar|viola[çc][ãa]o)$", "so", _PICANTE.pattern),
    (r"^hero[ií]na$", "so", r"drog|aditivo|vici|injet|trafic|comerciante ilegal|overdose|apag[ãa]o qu[íi]mico|cheir|"
                           r"seringa|usu[áa]ri|dose\b"),
    (r"^gostos[oa]$", "sem", r"comida|prato|sabor|bolo|carne|sopa|cheiro|bebida|refei[çc]|janta|almo[çc]|lanche|"
                             r"doce|tempero|receita|ch[áa]\b|caf[ée]|fruta|p[ãa]o|cozinh"),
    (r"^(?:chup\w+|mam(?:ar|ando|ou))$", "sem", r"sangue|suco de tomate|vampir|dedo|pirulito|\bbala\b|lim[ãa]o|"
                                                r"laranja|picol[ée]|sorvete|leite|mamadeira|beb[êe]|filhote|energia|"
                                                r"\bmana\b|\balma|poder"),
    (r"^(?:gemidos?|gemendo|geme|gemir)$", "sem", r"\bdor\b|ferid|machuc|agoni|sofr|doente|febre|sangr|golpe|soco|"
                                                  r"chute|apanh|medo|fantasma"),
    (r"^piranha$", "sem", r"\brio\b|peixe|[áa]gua|\blago|aqu[áa]rio|cardume|pesc"),
    (r"^seio$", "depois", r"^\s+d[aeo]s?\b"),                       # "no seio da família"
    (r"^goz\w+$", "depois", r"^\s+d[aeo]s?\b"),                     # "gozava de boa saúde"
    (r"^retardad[oa]$", "antes", r"(?:efeito|a[çc][ãa]o|bomba|explos[ãa]o|disparo)\s+$"),
    (r"^amante$", "depois", r"^s?\s+d[aeo]s?\s+(?:arte|m[úu]sica|livro|natureza|leitura|vinho|cinema|poesia|"
                            r"batalha|luta|paz|liberdade|conhecimento|justi[çc]a)"),
]]


_ORIGINAL = {"txt": ""}  # o texto como chegou no anti_ban (antes de qualquer troca)


def _frase_de(m):
    txt, i = m.string, m.start()
    ini = max(txt.rfind(c, 0, i) for c in ".!?\n") + 1
    fins = [p for p in (txt.find(c, m.end()) for c in ".!?\n") if p >= 0]
    return txt[ini:min(fins) if fins else len(txt)]


def _pode_trocar(m):
    casado = m.group(0)
    for rx, tipo, ctx in _GUARDAS:
        if not rx.match(casado):
            continue
        if tipo == "so":
            # também o texto ORIGINAL: uma regra anterior pode já ter trocado o sinal ("tesão" -> "fogo")
            return bool(ctx.search(_frase_de(m).replace(casado, " ", 1)) or
                        ctx.search(_ORIGINAL["txt"].replace(casado, " ")))
        if tipo == "sem":
            return not ctx.search(_frase_de(m))
        if tipo == "depois":
            return not ctx.search(m.string[m.end():m.end() + 40])
        if tipo == "antes":
            return not ctx.search(m.string[max(0, m.start() - 20):m.start()])
    return True


def _com_guarda(troca):
    def f(m):
        if not _pode_trocar(m):
            return m.group(0)
        return troca(m) if callable(troca) else m.expand(troca)
    return f


# acertos de gênero/conjugação que vêm ANTES da regra genérica (a genérica deixava "a servo", "ficou aceso" pra
# mulher, "ele gravata definitiva o traidor", "ele encanta a plateia" no passado, "a a peça de baixo")
_ANTES = [
    (r"escrava", "serva"), (r"escravid[ãa]o", "servidão"),
    (r"excitada", "acesa"),
    # 13/11 (chat do D:, conferindo o lote do agente online): com palavra inteira, "estuprou"/"estupraram" caíam no
    # genérico estupr\w* e a frase saía sem conjugação ("matou e forçar a barra a vila"). Verbo conjugado antes.
    (r"estupraram", "atacaram"), (r"estuprou", "atacou"), (r"estuprando", "atacando"), (r"estuprava(m?)", r"atacava\1"),
    # 13/11 (agente online, sugestão do chat do D:): infinitivo também — "tentou estuprar a princesa" saía "tentou
    # forçar a barra a princesa"
    (r"estuprar", "atacar"),
    # verbo conjugado de tortura (só com gore, como a regra genérica): "foi torturada" saía "foi interrogação intensa"
    (r"torturad([oa])", _so_gore(lambda m: "maltratad" + m.group(1))), (r"torturaram", _so_gore("maltrataram")),
    (r"torturou", _so_gore("maltratou")), (r"torturando", _so_gore("maltratando")), (r"torturar", _so_gore("maltratar")),
    # "suicídio" como substantivo com artigo: "O ir de base do pai", "cometeu ir de base" não fazem frase
    (r"comet(eu|er|eram|ia) suic[íi]dio", lambda m: {"eu": "tirou", "er": "tirar", "eram": "tiraram",
                                                      "ia": "tirava"}[m.group(1).lower()] + " a própria vida"),
    (r"\b(o|do|no|ao|um|pelo|esse|seu|meu)\s+suic[íi]dio", r"\1 fim trágico"),
    (r"seduziram", "encantaram"), (r"seduziu", "encantou"), (r"seduzindo", "encantando"), (r"seduzir", "encantar"),
    (r"seduzid([oa])", r"encantad\1"),
    (r"enforcaram\s+(o|a)(s?)\b", r"deram a gravata definitiva n\1\2"), (r"enforcou\s+(o|a)(s?)\b", r"deu a gravata definitiva n\1\2"),
    (r"enforcar\s+(o|a)(s?)\b", r"dar a gravata definitiva n\1\2"),
    (r"enforcaram", "deram a gravata definitiva em"), (r"enforcou", "deu a gravata definitiva em"),
    (r"enforcar", "dar a gravata definitiva em"), (r"enforcad[oa]", "na gravata definitiva"),
    (r"(?:degolar|decapitar)\s+(o|a)(s?)\b", r"tirar a cabeça d\1\2"),
    (r"espiar", "bisbilhotar"),
    (r"os seios", "os frontais"),
    (r"cueca", "peça de baixo"),
]

_ANTI_BAN_C = [(re.compile(_palavra_inteira(r), re.IGNORECASE), _com_guarda(s)) for r, s in _ANTES + _ANTI_BAN]
_VIRAL_C = [(re.compile(r, re.IGNORECASE), s) for r, s in _VIRAL]


def anti_ban(texto):
    """Suaviza termos de strike. SEMPRE aplicado. Não muda o sentido da história."""
    if not texto:
        return texto
    _ORIGINAL["txt"] = texto
    _CENSURA["trocou"] = False
    for rgx, sub in _ANTI_BAN_C:
        texto = rgx.sub(sub, texto)
    if _CENSURA["trocou"] and os.environ.get("ANIME_PISCADA_CENSURA") == "1" \
            and not any(p in texto for p in _PISCADAS):
        # escolha FIXA pela frase (md5): o mesmo texto passa aqui mais de uma vez (clima, TTS) e tem de sair igual
        import hashlib
        h = int(hashlib.md5(texto.encode("utf-8")).hexdigest(), 16)
        if h % 3 == 0:  # ~1 em cada 3 frases com troca
            texto = texto.rstrip() + " " + _PISCADAS[h // 3 % len(_PISCADAS)]
    return texto


def viralizar(texto):
    """Gírias gen-z seguras. Só com VIRAL_SLANG=1 (decisão do caller)."""
    if not texto:
        return texto
    for rgx, sub in _VIRAL_C:
        texto = rgx.sub(sub, texto)
    return texto


if __name__ == "__main__":
    casos = [
        "ele matou o vilão e saiu muito sangue",
        "cena de nudez proibida para menores",
        "ele vai estudar pra prova e ganhar dinheiro",
        "que porra é essa, caralho",
    ]
    for c in casos:
        ab = anti_ban(c)
        vr = viralizar(ab)
        print(f"IN : {c}")
        print(f"AB : {ab}")
        print(f"VIR: {vr}\n")
