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
    (r"assassin\w*|\bmat(ar|ou|aram|ando|a)\b|\bmorrer\b|\bmorreu\b|\bmort[oa]s?\b", "desviver"),
    (r"degola[rçã]\w*|decapita[rçã]\w*", "perder a cabeça"),
    (r"sangue", "suco de tomate"),
    (r"sangra[r]", "vazar suco"),
    (r"tortura[r]?\w*", "interrogação intensa"),
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
    (r"cacete", "caramba"),
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
    (r"s[êe]men", "essência"),
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

_ANTI_BAN_C = [(re.compile(r, re.IGNORECASE), s) for r, s in _ANTI_BAN]
_VIRAL_C = [(re.compile(r, re.IGNORECASE), s) for r, s in _VIRAL]


def anti_ban(texto):
    """Suaviza termos de strike. SEMPRE aplicado. Não muda o sentido da história."""
    if not texto:
        return texto
    for rgx, sub in _ANTI_BAN_C:
        texto = rgx.sub(sub, texto)
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
