# -*- coding: utf-8 -*-
"""seo.py — AGENTE de título, descrição e tags dos vídeos (completo vertical, Shorts e longo 16:9).

Uma chamada de LLM por (capítulo, idioma, tipo), em cache (workspace/cache/seo/). Ordem: Sonnet do proxy do
Claude Code -> Gemini do proxy -> Gemini direto. Falhou tudo -> devolve None e quem chamou usa o modelo fixo.

  pacote(chave_fila, idioma, "completo")          -> {titulo, descricao, tags}
  pacote(chave_fila, idioma, "shorts", n=7)       -> {titulos: [...], descricao, tags}
  pacote_longo(obra_slug, caps, idioma, capitulos_txt) -> {titulo, descricao, tags}

O que o agente recebe: capítulo, gêneros da obra, o roteiro narrado (resumo), gancho e pergunta do editorial e o
banco de palavras buscadas (config/seo_palavras.json, do autocompletar do YouTube).
Regras (dono, 15/10): o NOME DA OBRA NUNCA aparece (título, descrição, hashtags, tags — risco de direitos autorais;
_sem_obra() apaga se o LLM escorregar). Título = provocação + o máximo de palavras buscadas que tenham a ver com a
história. O completo sai com 3 títulos em estilos diferentes (busca / provocacao / curiosidade); um é escolhido em
rodízio (amostragem de Thompson em workspace/titulos_estilos.json) e o estilo vai pro estado da postagem pra medir
qual rende mais (docs/seo_titulos.md).
"""
import hashlib
import json
import random
import re
from pathlib import Path

from hp_common import PROJECT_DIR, log

CACHE = PROJECT_DIR / "workspace" / "cache" / "seo"
PALAVRAS = PROJECT_DIR / "config" / "seo_palavras.json"
STATS_TITULOS = PROJECT_DIR / "workspace" / "titulos_estilos.json"
VERSAO = "v3"  # muda a chave do cache: o v2 saiu com as palavras do português em TODAS as línguas
NOMES_IDIOMA = {None: "português do Brasil", "pt": "português do Brasil", "hi": "hindi", "id": "indonésio",
                "it": "italiano", "ru": "russo", "th": "tailandês", "vi": "vietnamita", "en": "inglês",
                "fr": "francês", "es": "espanhol"}


def recap_capitulo(chave, idioma=None):
    """Roteiro (recap) do capítulo da fila, no idioma pedido se a tradução estiver em cache."""
    import fila
    import hp_paineis
    est = fila.ler_estado().get(chave) or {}
    cap = next(((o, n, p) for k, o, n, p in fila.capitulos() if k == chave), None)
    if not cap:
        return None, None, None
    obra, n, pasta = cap
    sk = est.get("skip", {})
    ps, _c = hp_paineis.selecionar_paineis(pasta, 120, 1, int(sk.get("fim", 0)), int(sk.get("inicio", 0)), verbose=False)
    narr = hp_paineis.arquivo_narracao(pasta, len(ps), 1, int(sk.get("fim", 0)), int(sk.get("inicio", 0)))
    if idioma:
        tr = narr.with_name(narr.stem + f"_{idioma}.json")
        narr = tr if tr.exists() else narr
    try:
        return json.loads(narr.read_text(encoding="utf-8")), obra, n
    except (OSError, ValueError):
        return None, obra, n


def _llm(prompt):
    import claude_client
    r = claude_client._extract_json(claude_client.perguntar(prompt, max_tokens=4000, temperature=0.7)
                                    or claude_client.gemini(prompt, max_tokens=4000, temperature=0.7))
    if isinstance(r, dict):
        return r
    try:
        import gemini_llm
        return claude_client._extract_json(gemini_llm.generate_text(prompt, max_tokens=4000, temperature=0.7))
    except Exception as e:  # noqa: BLE001
        log(f"  [!] seo: Gemini direto falhou ({str(e)[:80]})")
        return None


def _resumo(recap, limite=3500):
    falas = [l.get("text", "").strip() for l in (recap or {}).get("locucoes", []) if l.get("text", "").strip()]
    txt = " ".join(falas)
    return txt[:limite]


def _cache(chave):
    return CACHE / f"{hashlib.md5(chave.encode('utf-8')).hexdigest()}.json"


def _pedir(chave_cache, prompt, valida):
    f = _cache(chave_cache)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            pass
    for _ in range(2):
        r = _llm(prompt)
        if isinstance(r, dict) and valida(r):
            r["tags"] = _limpar_tags(r.get("tags", []))
            CACHE.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
            return r
    log("  [!] seo: agente não devolveu um pacote válido; usando o modelo fixo")
    return None


def _limpar_tags(tags):
    """Sem '#', sem repetidas, cada uma <= 30 caracteres e o total <= 400 (margem segura pro YouTube)."""
    out, total = [], 0
    for t in tags:
        t = re.sub(r"\s+", " ", str(t).replace("#", "")).strip()[:30]
        if t and t.lower() not in {o.lower() for o in out} and total + len(t) + 1 <= 400:
            out.append(t)
            total += len(t) + 1
    return out


_DIC_SEGURO_SEO = None
def _dic_seguro():
    global _DIC_SEGURO_SEO
    if _DIC_SEGURO_SEO is not None:
        return _DIC_SEGURO_SEO
    p = PROJECT_DIR / "config" / "dicionario_seguro.json"
    try:
        _DIC_SEGURO_SEO = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _DIC_SEGURO_SEO = {}
    return _DIC_SEGURO_SEO

def _sanitizar_seo(pacote_dict, idioma=None):
    """Troca palavras proibidas no título, descrição e tags pelo eufemismo."""
    dic = _dic_seguro()
    proibidas = dic.get("proibidas", {})
    if idioma and idioma in dic.get("idiomas", {}):
        # SÓ a lista da própria língua. Misturando com a do português, palavra estrangeira virava
        # expressão em português dentro do título: em italiano "La bomba e il crack della famiglia"
        # saía "La carga explosiva e il substância pesada della famiglia"; em indonésio "mata", que
        # lá quer dizer OLHO, virava "elimina" porque também é 3ª pessoa de matar em português.
        proibidas = dic["idiomas"][idioma]
    if not proibidas:
        return pacote_dict
    padroes = sorted(proibidas.keys(), key=len, reverse=True)
    regex = re.compile(r"\b(" + "|".join(re.escape(p) for p in padroes) + r")\b", re.IGNORECASE)
    def _sub(m):
        alts = proibidas.get(m.group(0).lower(), [])
        return alts[0] if alts else m.group(0)
    for campo in ("titulo", "descricao"):
        if campo in pacote_dict and isinstance(pacote_dict[campo], str):
            pacote_dict[campo] = regex.sub(_sub, pacote_dict[campo])
    if isinstance(pacote_dict.get("titulos"), dict):  # completo: {estilo: título}
        pacote_dict["titulos"] = {e: regex.sub(_sub, t) for e, t in pacote_dict["titulos"].items()}
    elif "titulos" in pacote_dict:
        pacote_dict["titulos"] = [regex.sub(_sub, t) for t in pacote_dict["titulos"]]
    if "tags" in pacote_dict:
        pacote_dict["tags"] = [regex.sub(_sub, t) for t in pacote_dict["tags"]]
    return pacote_dict


REGRAS = (
    "Você é especialista em SEO e CTR do YouTube para canais de recap de manhwa (resumo narrado). "
    "Escreva TUDO em {lingua}. Regras:\n"
    "1) NUNCA escreva o nome da obra (nem traduzido, nem em hashtag/tag): risco de direitos autorais. Nomes dos "
    "personagens podem ir na descrição.\n"
    "2) Título = provocação/curiosidade forte + o MÁXIMO que couber de palavras que o público busca e que tenham a "
    "ver com a história (use as palavras buscadas abaixo, só as que combinam com o roteiro). Estilo dos canais que "
    "mais crescem: frases longas tipo 'ELE FOI HUMILHADO por ser POBRE mas HERDOU uma GAROTA e agora TODAS querem "
    "ele'. Até 95 caracteres, 3-5 palavras-chave em MAIÚSCULAS, no máximo 1 emoji. Sem prometer o que não "
    "acontece, sem palavrão.\n"
    "3) Descrição de 3 parágrafos curtos: 1ª linha = gancho com palavras buscadas; o que acontece no capítulo sem "
    "contar o final (com as palavras buscadas naturalmente: manhwa recap, resumo manhwa, gênero); pergunta pro "
    "público comentar + convite pra se inscrever; termina com 5-7 hashtags de GÊNERO/BUSCA (#manhwa #manhwarecap "
    "#resumomanhwa #romance ...), nunca hashtag com o nome da obra.\n"
    "4) 20 a 30 tags de busca reais: palavras buscadas do gênero, frases como o público digita ('manhwa romance "
    "completo', 'ele foi humilhado manhwa'), nomes dos personagens. Sem o nome da obra.\n"
    "SEGURANÇA DE ANÚNCIOS: NUNCA use estas palavras no título/descrição/tags: "
    "morte, matar, morrer, sangue, arma, droga, suicídio, escravo, sexo, nu, nudez, tortura, assassino, "
    "pornografia, estupro, violação, bomba, terrorista. Use eufemismos seguros. "
    "Devolva SÓ JSON.")


def _obra_cfg(slug):
    import fila
    return next((o for o in fila.cfg().get("obras", []) if o.get("slug") == slug), {})


def _palavras(obra, idioma=None):
    """Bloco do prompt com as palavras buscadas dos gêneros da obra + padrões reais de busca."""
    try:
        b = json.loads(PALAVRAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    # Cada língua tem o seu banco. O do português entrava no prompt de todas e saía a tag
    # "manhwa recap pt br" em Short de hindi e título em hindi com a palavra "Completo"
    # (visto em 16/10). O merge troca sempre/padroes_reais/generos inteiros; língua sem
    # banco próprio continua caindo no português, como antes.
    if idioma and idioma != "pt":
        b = {**b, **(b.get("idiomas", {}).get(idioma) or {})}
    gen = (_obra_cfg(obra.get("slug")) or obra).get("generos") or list(b.get("generos", {}))
    pal = [w for g in gen for w in b.get("generos", {}).get(g, [])]
    return (f"Gêneros da obra: {', '.join(gen)}\nPalavras buscadas (use as que combinam com a história): "
            f"{', '.join(dict.fromkeys(pal + b.get('sempre', [])))}\nComo o público busca (padrões reais): "
            f"{' | '.join(b.get('padroes_reais', []))}\n")


def _nomes_proibidos(obra):
    o = _obra_cfg(obra.get("slug")) or {}
    nomes = set(o.get("nomes_proibidos", [])) | {obra.get("titulo", ""), obra.get("slug", "")}
    return sorted((n for n in nomes if n and len(n) >= 4), key=len, reverse=True)


def _sem_obra(r, obra):
    """Apaga o nome da obra (e variações, inclusive #NomeJunto) do pacote; tag com o nome sai inteira."""
    if not r:
        return r
    nomes = _nomes_proibidos(obra)
    if not nomes:
        return r
    alts = [re.sub(r"(\\[ -])+", r"[\\s_-]*", re.escape(n)) for n in nomes]
    rx = re.compile(r"#?(?:" + "|".join(alts) + r")\w*", re.I)

    def limpa(t):
        t = rx.sub("", t)
        t = re.sub(r"\(\s*\)|\[\s*\]", "", t)
        t = re.sub(r"[ \t]{2,}", " ", t)
        t = re.sub(r" +([,.!?:;)])", r"\1", t)
        t = re.sub(r"\( +", "(", t)
        t = re.sub(r"\b(de|do|da|em|no|na)\s*([,.!?])", r"\2", t)  # "capítulo 1 de <obra>," -> "capítulo 1,"
        return re.sub(r"^[ \t:—–|-]+|[ \t:—–|-]+$", "", t, flags=re.M).strip()
    for k in ("titulo", "descricao"):
        if isinstance(r.get(k), str):
            r[k] = limpa(r[k])
    if isinstance(r.get("titulos"), list):
        r["titulos"] = [limpa(t) for t in r["titulos"]]
    elif isinstance(r.get("titulos"), dict):
        r["titulos"] = {e: limpa(t) for e, t in r["titulos"].items()}
    if isinstance(r.get("tags"), list):
        r["tags"] = [t for t in r["tags"] if not rx.search(t)]
    return r


def _stats_titulos():
    try:
        return json.loads(STATS_TITULOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def escolher_estilo(estilos):
    """Thompson no placar ÚNICO de todos os projetos (placar_titulos, COMUM, desde 20/10)."""
    import placar_titulos
    return placar_titulos.escolher(estilos)


def registrar_resultado(estilo, venceu, video_id="", idioma=""):
    """Chamado pela análise (CTR/visualizações do vídeo contra a média do canal) — ver docs/seo_titulos.md."""
    import placar_titulos
    return placar_titulos.registrar(estilo, venceu, projeto="hipercool", idioma=idioma, video_id=video_id)


def pacote(chave, idioma=None, tipo="completo", n=0):
    recap, obra, cap = recap_capitulo(chave, idioma)
    if not recap:
        return None
    ed = recap.get("_editorial") or {}
    base = (f"Capítulo: {cap}\nGancho: {ed.get('gancho', '')}\nPergunta do fim: {ed.get('pergunta', '')}\n"
            f"{_palavras(obra, idioma)}Roteiro narrado (resumo):\n{_resumo(recap)}\n\n")
    lingua = NOMES_IDIOMA.get(idioma, idioma)
    if tipo == "shorts":
        prompt = (REGRAS.format(lingua=lingua) + f"\nSão {n} Shorts (partes em sequência do capítulo). Gere "
                  f"'titulos' (lista com EXATAMENTE {n} títulos, um por parte, cada um com no máx. 90 caracteres: "
                  "provocação do trecho + 2-3 palavras buscadas, terminando com o número da parte tipo '(Parte 1)' e "
                  "no máximo 1 emoji; varie o estilo entre as partes), 'descricao' (curta, 2 linhas com palavras "
                  "buscadas + hashtags de gênero incluindo #shorts) e 'tags'.\n\n" + base
                  + 'Formato: {"titulos": [...], "descricao": "...", "tags": [...]}')
        r = _pedir(f"{VERSAO}|{chave}|{idioma}|shorts|{n}", prompt,
                   lambda r: len(r.get("titulos", [])) == n and r.get("tags"))
        if r and idioma:  # o exemplo '(Parte 1)' do prompt é copiado ao pé da letra: hindi/indonésio/vietnamita
            import idiomas  # saíam com "(Parte 3)" em português (16/10). Vale também pro que já está em cache.
            palavra = (idiomas.TEXTOS.get(idioma) or {}).get("parte", "").split("{x}")[0].strip().capitalize()
            if palavra and palavra.lower() != "parte":
                r["titulos"] = [re.sub(r"\(\s*Parte\s+(\d+)\s*\)", rf"({palavra} \1)", t) for t in r["titulos"]]
        return _sem_obra(_sanitizar_seo(r, idioma), obra) if r else None
    try:
        estilos = json.loads(PALAVRAS.read_text(encoding="utf-8")).get("estilos_titulo")
    except (OSError, ValueError):
        estilos = None
    estilos = estilos or {"busca": "", "provocacao": "", "curiosidade": ""}
    prompt = (REGRAS.format(lingua=lingua) + f"\nVídeo: o capítulo completo narrado. Gere {len(estilos)} títulos, "
              "um por estilo:\n"
              + "\n".join(f"- {e}: {d}" for e, d in estilos.items()) + "\n\n" + base
              + 'Formato: {"titulos": {' + ", ".join(f'"{e}": "..."' for e in estilos)
              + '}, "descricao": "...", "tags": [...]}')
    r = _pedir(f"{VERSAO}|{chave}|{idioma}|completo", prompt,
               lambda r: isinstance(r.get("titulos"), dict) and all(r["titulos"].get(e) for e in estilos)
               and r.get("tags"))
    if not r:
        return None
    r = _sem_obra(_sanitizar_seo(r, idioma), obra)
    estilo = escolher_estilo([e for e in estilos if r["titulos"].get(e)])
    return {**r, "titulo": r["titulos"][estilo], "estilo": estilo}


def nome_playlist(slug, tipo, idioma=None):
    """Nome de PLAYLIST da obra no padrão dos títulos (premissa/provocação + palavras buscadas), SEM o nome da obra
    (dono, 15/10). tipo: "recap" (um vídeo por capítulo) ou "maratona" (compilados longos). None se o LLM falhar.
    Quem usa grava o nome em config/fila.json (a playlist é achada pelo nome: ele não pode mudar depois)."""
    import fila
    obra = _obra_cfg(slug) or {"slug": slug}
    chave1 = next((k for k, o, _n, _p in fila.capitulos() if o["slug"] == slug), None)
    recap = recap_capitulo(chave1, idioma)[0] if chave1 else None
    lingua = NOMES_IDIOMA.get(idioma, idioma)
    oque = {"recap": "os capítulos narrados desta história, um vídeo por capítulo, em ordem",
            "maratona": "as MARATONAS desta história (vídeos longos com vários capítulos juntos)"}[tipo]
    prompt = (REGRAS.format(lingua=lingua) + f"\nGere o NOME de uma PLAYLIST do YouTube que junta {oque}. Até 80 "
              "caracteres, no mesmo estilo dos títulos: premissa/provocação forte + 2-4 palavras buscadas (manhwa, "
              "recap/resumo, gênero" + (", maratona/completo" if tipo == "maratona" else "") + "). Sem número de "
              "capítulo, no máximo 1 emoji, NUNCA o nome da obra.\n\n" + _palavras(obra, idioma)
              + (f"Roteiro do 1º capítulo (resumo):\n{_resumo(recap, 1500)}\n\n" if recap else "")
              + (f"IMPORTANTE: o nome TEM que estar em {lingua} (as palavras buscadas acima são do português: "
                 f"traduza a ideia), com espaço normal entre as palavras.\n" if idioma and idioma != "pt" else "")
              + 'Formato: {"nome": "..."}')
    r = _pedir(f"{VERSAO}|playlist2|{slug}|{tipo}|{idioma}", prompt, lambda r: bool(str(r.get("nome", "")).strip()))
    if not r:
        return None
    nome = _sem_obra({"titulo": str(r["nome"]).strip()}, obra)["titulo"]
    return nome[:150] or None


def pacote_longo(chaves, idioma=None, capitulos_txt=""):
    """Compilação 16:9 de vários capítulos. chaves = chaves da fila dos capítulos, em ordem."""
    resumos, obra, caps = [], None, []
    for ch in chaves:
        recap, obra, cap = recap_capitulo(ch, idioma)
        if recap:
            caps.append(cap)
            resumos.append(f"[Capítulo {cap}] {_resumo(recap, 900)}")
    if not resumos:
        return None
    lingua = NOMES_IDIOMA.get(idioma, idioma)
    prompt = (REGRAS.format(lingua=lingua) + f"\nVídeo LONGO (maratona) juntando os capítulos {caps[0]} a "
              f"{caps[-1]}. O título deve dizer que é a história COMPLETA/maratona (use as palavras de "
              "maratona/completo do bloco abaixo, NA LÍNGUA DO VÍDEO) + a provocação. Na "
              "descrição, inclua no fim a lista de capítulos "
              "com minutos exatamente como abaixo.\n\n" + _palavras(obra, idioma)
              + "\n".join(resumos) + f"\n\nLista de capítulos (copie igual):\n{capitulos_txt}\n\n"
              + 'Formato: {"titulo": "...", "descricao": "...", "tags": [...]}')
    r = _pedir(f"{VERSAO}|longo|{'|'.join(chaves)}|{idioma}", prompt, lambda r: r.get("titulo") and r.get("tags"))
    return _sem_obra(_sanitizar_seo(r, idioma), obra) if r else None
