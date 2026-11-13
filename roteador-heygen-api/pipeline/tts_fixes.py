# -*- coding: utf-8 -*-
"""tts_fixes.py - DICIONARIO de correcoes foneticas para TTS PT-BR do HeyGen.

Vozes tipo Chill/Chase tem problemas conhecidos:
  - voce -> 'voke'
  - codigo -> 'codyygo'
  - mantem -> 'mante'
  - padrao -> 'padra-o'
  - implementar -> 'inpelmentacal'

Estrategia: substituir grafia por versao hifenizada ou grafia alternativa
que o TTS pronuncia melhor. Tambem adiciona virgulas para forcar pausas.

USO:
  from tts_fixes import apply_fixes, add_rule
  text = apply_fixes(meu_texto)

ADICIONAR NOVA REGRA:
  add_rule('palavra_errada', 'pronuncia_correta')
  add_rule('palavra_errada', 'pronuncia_correta', regex=True)  # se quiser regex
"""
import re


# Dicionario principal: palavra_errada -> pronuncia_correta
# Match: word-boundary case-insensitive (\b...\b)
# Para virgulas extras de pausa, adicione elas no valor.
DICT_FIXES = {
    # --- palavras problematicas conhecidas ---
    # grafia alternativa hifenizada para forcar silabas no TTS
    "código": "có-di-go",
    "codigo": "có-di-go",
    "códigos": "có-di-gos",
    "codigos": "có-di-gos",
    "implementação": "implemen-ta-ção",
    "implementacao": "implemen-ta-ção",
    "implementar": "implemen-tar",
    "inteligência": "in-te-li-gên-cia",
    "inteligencia": "in-te-li-gên-cia",
    "artificial": "ar-ti-fi-ci-al",
    "autenticação": "autên-ti-ca-ção",
    "autenticacao": "autên-ti-ca-ção",
    "ferramenta": "fer-ra-men-ta",
    "ferramentas": "fer-ra-men-tas",
    "refatorar": "re-fac-to-rar",
    "debugar": "de-bug-ar",
    "implement": "implemênt",
    "voz": "vóz",
    "vozes": "vó-zes",
    "manter": "man-ter",
    "mantém": "mantêm",
    "mantem": "mantêm",
    "padrão": "pad-rão",
    "padrao": "pad-rão",
    "padrões": "pad-rões",
    "padroes": "pad-rões",
    "também": "tam-bém",
    "tambem": "tam-bém",
    "tecnologia": "tec-no-lo-gia",
    "tecnologias": "tec-no-lo-gias",
    "técnico": "téc-ni-co",
    "tecnico": "téc-ni-co",
    "enquanto": "enquan-to",
    "entender": "en-ten-der",
    "poderia": "pode-ria",
    "poderiam": "pode-ri-am",
    "difícil": "di-fí-cil",
    "dificil": "di-fí-cil",
    "fáceis": "fá-ceis",
    "fácil": "fá-cil",
    "facil": "fá-cil",
    "decisão": "de-ci-são",
    "decisao": "de-ci-são",
    "decisões": "de-ci-sões",
    "decisoes": "de-ci-sões",
    "economia": "e-co-no-mia",
    "repetitivas": "re-pe-ti-ti-vas",
    "repetitiva": "re-pe-ti-ti-va",
    "futuro": "fu-tu-ro",
    "programação": "pro-gra-ma-ção",
    "programacao": "pro-gra-ma-ção",
    "programadores": "pro-gra-ma-do-res",
    "legado": "le-ga-do",
    "complexas": "com-plex-as",
    "complexa": "com-plex-a",
    "complexos": "com-plex-os",
    "complexo": "com-plex-o",
    "arquitetura": "ar-qui-te-tu-ra",
    "consistência": "con-sis-tên-cia",
    "consistencia": "con-sis-tên-cia",
    "impressionante": "im-pres-si-o-nan-te",
    "preferências": "pre-fe-rên-cias",
    "preferencias": "pre-fe-rên-cias",
    "aprende": "a-pren-de",
    "hora": "o-ra",
    "horas": "o-ras",
    "três": "três",
    "cinco": "cin-co",
    "trabalho": "tra-ba-lho",
    "trabalham": "tra-ba-lham",
    "simples": "sim-ples",
    "simples": "sim-ples",
    "design": "de-zain",
    "context": "con-text",
    "contexto": "con-tex-to",
    "automático": "au-to-má-ti-co",
    "automatizado": "au-to-ma-ti-za-do",
    "automatizados": "au-to-ma-ti-za-dos",
    "automatizadas": "au-to-ma-ti-za-das",
    "comando": "co-man-do",
    "comandos": "co-man-dos",
    "commit": "com-mit",
    "commits": "com-mits",
    "open source": "ópen sórce",
    "workflow": "work-flow",
    "workflows": "work-flows",
    # --- palavras sem acento ---
    "nao": "não",
    "voce": "você",
    "eh": "é",
    "pra": "para",
    "ta": "está",
    "tá": "está",
    "ne": "né",
    "ja": "já",
    "so": "só",
    "sozinho": "so-zinho",
    "entao": "então",
    "porque": "por-que",
    "por que": "por-que",
    "num": "em um",
    "numa": "em uma",
    "nesse": "nes-se",
    "la": "lá",
    "ali": "a-li",
    "hoje": "ho-je",
    "sempre": "sem-pre",
    "nunca": "nun-ca",
    "ainda": "ain-da",
    "talvez": "tal-vez",
    "agora": "a-go-ra",
    "depois": "de-pois",
    "antes": "an-tes",
    "obrigado": "obri-ga-do",
    "obrigada": "obri-ga-da",
    "precisa": "pre-ci-sa",
    "preciso": "pre-ci-so",
    "muito": "mui-to",
    "pouco": "pou-co",
    "grande": "gran-de",
    "pequeno": "peque-no",
    "primeiro": "pri-mei-ro",
    "segundo": "se-gun-do",
    "ultimo": "úl-ti-mo",
    "último": "úl-ti-mo",
    "mesmo": "mes-mo",
    "outro": "ou-tro",
    "outros": "ou-tros",
    "mesma": "mes-ma",
    "coisa": "coi-sa",
    "coisas": "coi-sas",
    "forma": "for-ma",
    "jeito": "jei-to",
    "parte": "par-te",
    "vez": "vez",
    "vezes": "ve-zes",
    "lugar": "lu-gar",
    "tipo": "ti-po",
    "caso": "ca-so",
    "fazendo": "fa-zendo",
    "feito": "fei-to",
    "vamos": "va-mos",
    "sao": "são",
    "são": "são",
    "todos": "to-dos",
    "tudo": "tu-do",
    "nada": "na-da",
    "algo": "al-go",
    "alguem": "alguém",
    "ninguem": "nin-guém",
    "conversa": "con-ver-sa",
    "inicio": "iní-cio",
    "início": "iní-cio",
    "vai": "vai",
    "pode": "po-de",
    "podem": "po-dem",
    "consigo": "con-si-go",
    "fazer": "fa-zer",
    "faz": "faz",
    "foco": "fo-co",
    "cuida": "cui-da",
    "usa": "u-sa",
    "usando": "u-san-do",
    "usar": "u-sar",
    "fica": "fi-ca",
    "ficar": "fi-car",
    "ficam": "fi-cam",
    "chegar": "che-gar",
    "chegou": "che-gou",
    "fazer": "fa-zer",
    "busca": "bus-ca",
    "buscas": "bus-cas",
    "buscar": "bus-car",
    "achou": "a-chou",
    "encontrar": "en-con-trar",
    "dar": "dar",
    "dá": "dá",
    "vão": "vão",
    "seguir": "se-guir",
    "definiu": "de-fi-niu",
    "criou": "cri-ou",
    "criar": "cri-ar",
    "revolucionando": "re-vo-lu-cio-nan-do",
    "revolucionar": "re-vo-lu-cio-nar",
    "revolucionou": "re-vo-lu-cio-nou",
    # --- termos para evitar (substituir por equivalente mais simples) ---
    "absurdamente": "muito",
    "incredo": "incrível",
    "incrívelmente": "muito",
    "adimplemento": "pagamento",
    "coaduna": "combina",
    "consubstanciado": "provado",
    "deletar": "apagar",
    "deletado": "apagado",
    "efetuar": "fazer",
    "implementa": "faz",
    "incrementalmente": "aos poucos",
    "logaritmo": "cálculo",
    "metodologia": "método",
    "na verdade": "na real",
    "obrigatoriamente": "precisa",
    "outrossim": "também",
    "por conseguinte": "por isso",
    "porém": "mas",
    "porem": "mas",
    "previamente": "antes",
    "primordialmente": "principalmente",
    "subsidiariamente": "também",
    "subsequente": "depois",
    "todavia": "mas",
    "utilizar": "usar",
    "utilizado": "usado",
    "utilizando": "usando",
    "utilização": "uso",
    "versatilidade": "flexibilidade",
    "viabilizar": "fazer acontecer",
    "vislumbrar": "ver",
}


# Regras de regex (caso especial): usadas ANTES do dicionario
# Adicionar virgula antes de certas conjuncoes para forcar pausa no TTS
REGEX_FIXES = [
    # virgula antes de conjuncoes problematicas
    (r"\s+porque\b", ", porque"),
    (r"\s+mas\b", ", mas"),
    # remover marcadores '[Bloco N]' - TTS le em voz alta
    (r"\[Bloco\s+\d+\]\s*", ""),
    # remover URLs (TTS soletra char por char)
    (r"https?://\S+", "link"),
    # normalizar pontuacao repetida
    (r"\.{2,}", "."),
    (r"!{2,}", "!"),
    (r"\?{2,}", "?"),
    # aspas no inicio/fim do texto
    (r'^\s*"\s*', ""),
    (r'\s*"\s*$', ""),
    # que vai ser processado depois
    ]


def add_rule(wrong, right, regex=False):
    """Adiciona regra nova no dicionario em tempo de execucao."""
    if regex:
        REGEX_FIXES.append((wrong, right))
    else:
        DICT_FIXES[wrong] = right


def _word_boundary_sort_key(item):
    """Ordena pelas palavras mais longas primeiro pra evitar match parcial
    (ex: 'código' antes de 'códigos')."""
    return -len(item[0])


def apply_fixes(text):
    """Aplica correcoes do dicionario + regex ao texto."""
    out = text
    # primeiro regex
    for pat, new in REGEX_FIXES:
        out = re.sub(pat, new, out)
    # depois dicionario, palavras mais longas primeiro
    items = sorted(DICT_FIXES.items(), key=_word_boundary_sort_key)
    for wrong, right in items:
        # pula regra onde chave == valor (no-op)
        if wrong.lower() == right.lower():
            continue
        # \b protege contra match parcial; ignore case pra pegar acentos.
        # (?<![-]) e (?![-]) evitam match dentro de palavra hifenizada (ex: 'ta' em 'fer-ra-men-ta')
        pat = r"(?<![-])\b" + re.escape(wrong) + r"\b(?![-])"
        def _repl(m, right=right):
            matched = m.group(0)
            # preserva caixa: se começa com maiuscula, capitaliza o replacement
            if matched[0].isupper():
                return right[0].upper() + right[1:]
            return right
        out = re.sub(pat, _repl, out, flags=re.IGNORECASE)
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, encoding="utf-8") as f:
            t = f.read()
        new = apply_fixes(t)
        out = path.rsplit(".", 1)[0] + "_fix.txt"
        with open(out, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"{len(t)} -> {len(new)} chars (salvo em {out})")
    else:
        sample = "Você não vai acreditar como o código fica fácil. Implementar autenticação OAuth no GitHub usando n8n é o futuro. O Claude Code entende o contexto e mantém o padrão. A voz fala 'voce' errado. Por conseguinte, é obrigatório utilizar metodologia incrementalmente, o que viabilizar versatilidade."
        print("ANTES:", sample)
        print()
        print("DEPOIS:", apply_fixes(sample))