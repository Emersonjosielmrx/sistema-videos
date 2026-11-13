# -*- coding: utf-8 -*-
"""seo_generator.py — título, descrição e tags do recap de anime (§1 de MELHORIAS_PARA_TODOS_OS_PROJETOS.md).

Copiado de D:\\hipercool-videos\\bin\\seo.py e adaptado ao anime:
- 3 títulos (estilos busca / provocacao / curiosidade), um escolhido por Thompson (workspace/titulos_estilos.json);
  o estilo usado vai pro postar.json (estilo_titulo) pra comparar o CTR depois.
- NUNCA o nome da obra: o LLM é avisado e _sem_obra apaga o que escorregar (título, descrição, tag inteira).
- Palavras buscadas: config/seo_palavras.json (autocompletar do YouTube pt-BR).

Quem chama: anime_publish.py (postar.json lido pelo postador central) e postar_animes.py (legado).
LLM: claude_client.generate_text (gateway OmniRoute, secrets/omniroute.json) -> gemini_llm.generate_text.
Se os dois falharem devolve None e quem chama usa o modelo fixo.
"""
import hashlib
import json
import logging
import os
import random
import re
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE = PROJECT_DIR / "workspace" / "cache" / "seo"
PALAVRAS = PROJECT_DIR / "config" / "seo_palavras.json"
STATS_TITULOS = PROJECT_DIR / "workspace" / "titulos_estilos.json"
VERSAO = "v4"  # v1 chamava funções do claude_client do hipercool que não existem aqui; v3 nomes_da_obra; v4 capa
ESTILOS = ("busca", "provocacao", "curiosidade")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _llm(prompt):
    """Gateway (claude_client) primeiro, Gemini de reserva. Devolve dict ou None."""
    import claude_client
    try:
        if claude_client.is_available():
            r = claude_client._extract_json(claude_client.generate_text(prompt, max_tokens=4000, temperature=0.7,
                                                                        video=True))
            if isinstance(r, dict):
                return r
    except Exception as e:  # noqa: BLE001
        log(f"  [!] seo: gateway falhou ({str(e)[:80]})")
    try:
        import gemini_llm
        r = claude_client._extract_json(gemini_llm.generate_text(prompt, max_tokens=4000, temperature=0.7))
        return r if isinstance(r, dict) else None
    except Exception as e:  # noqa: BLE001
        log(f"  [!] seo: Gemini falhou ({str(e)[:80]})")
        return None


def _limpar_tags(tags):
    """Sem '#', sem repetidas, cada uma <= 30 caracteres e o total <= 400 (margem segura pro YouTube)."""
    out, total = [], 0
    for t in tags:
        t = re.sub(r"\s+", " ", str(t).replace("#", "")).strip()
        if len(t) > 30:  # cortar deixava meia palavra ("ele foi humilhado mas se torno"): tag longa sai inteira
            continue
        if t and t.lower() not in {o.lower() for o in out} and total + len(t) + 1 <= 400:
            out.append(t)
            total += len(t) + 1
    return out


def _cache(chave):
    return CACHE / f"{hashlib.md5(chave.encode('utf-8')).hexdigest()}.json"


def _pedir(chave_cache, prompt, valida):
    f = _cache(chave_cache)
    if f.exists():
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
            if valida(r):  # o cache também passa na validação (16/10: um SEO "hindi" em português tinha ficado salvo)
                return r
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


def _banco():
    try:
        return json.loads(PALAVRAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _palavras(b):
    """Bloco do prompt com as palavras buscadas + padrões reais de busca."""
    pal = [w for ws in b.get("generos", {}).values() for w in ws]
    return (f"Palavras buscadas (use SÓ as que combinam com a história): "
            f"{', '.join(dict.fromkeys(b.get('sempre', []) + pal))}\n"
            f"Como o público busca (padrões reais): {' | '.join(b.get('padroes_reais', []))}\n")


def _nomes_proibidos(nomes):
    out = set()
    for n in nomes or []:
        n = re.sub(r"\s+", " ", str(n or "")).strip(" \"'")
        if len(n) >= 4:
            out.add(n)
            out.add(n.replace(" ", ""))  # #NomeJunto
    return sorted(out, key=len, reverse=True)


def _rx_obra(nomes):
    nomes = _nomes_proibidos(nomes)
    if not nomes:
        return None
    alts = [re.sub(r"(\\[ -])+", r"[\\s_-]*", re.escape(n)) for n in nomes]
    return re.compile(r"#?(?:" + "|".join(alts) + r")\w*", re.I)


def _sem_obra(r, nomes):
    """Apaga o nome da obra (e variações, inclusive #NomeJunto) da descrição; tag e título com o nome saem
    inteiros (título com o nome apagado vira meia frase: 'POR QUE TODOS ODEIAM O ?')."""
    rx = _rx_obra(nomes)
    if not r or not rx:
        return r

    def limpa(t):
        t = rx.sub("", t)
        t = re.sub(r"\(\s*\)|\[\s*\]", "", t)
        t = re.sub(r"[ \t]{2,}", " ", t)
        t = re.sub(r" +([,.!?:;)])", r"\1", t)
        t = re.sub(r"\( +", "(", t)
        t = re.sub(r"\b(de|do|da|em|no|na)\s*([,.!?])", r"\2", t)
        return re.sub(r"^[ \t:—–|-]+|[ \t:—–|-]+$", "", t, flags=re.M).strip()
    if isinstance(r.get("descricao"), str):
        r["descricao"] = limpa(r["descricao"])
    if isinstance(r.get("titulos"), dict):
        r["titulos"] = {e: t for e, t in r["titulos"].items() if not rx.search(t)}
    if isinstance(r.get("tags"), list):
        r["tags"] = [t for t in r["tags"] if not rx.search(t)]
    return r


def _caps_no_limite(t, maximo=5):
    """Regra do título: 3-5 palavras-chave em MAIÚSCULAS. 21/10: 32 de 60 títulos do parceiro passavam de metade das
    letras em maiúsculas (o modelo exagera). Mantém as `maximo` primeiras palavras em caixa alta e o resto em minúscula;
    a 1ª letra do título fica maiúscula. Sigla curta (até 3 letras) não conta."""
    vistas = 0

    def troca(m):
        nonlocal vistas
        w = m.group(0)
        if len(w) <= 3:
            return w
        vistas += 1
        return w if vistas <= maximo else w.lower()
    out = re.sub(r"\b[A-ZÀ-ÖØ-Þ]{2,}\b", troca, t)
    return out[:1].upper() + out[1:] if out else out


def _corta(t, limite):
    """Até `limite` caracteres cortando num ponto natural (pontuação ou antes de 'e/mas/que/quando');
    None se não houver corte que deixe o título inteiro (meia frase no título é pior que perder o estilo)."""
    t = re.sub(r"\s+", " ", t or "").strip()
    if len(t) <= limite:
        return t
    pos = [m.start() + (m.group(0) in "!?…")
           for m in re.finditer(r"[!?…,:;—–]| (?=(?:e|mas|que|quando|porque|até)\b)", t[:limite + 1])]
    pos = [p for p in pos if limite * 0.45 <= p <= limite]
    if not pos:
        return None
    return re.sub(r"(\s+(e|o|a|os|as|de|do|da|que|um|uma|em|no|na|com|por|pra|para|mas))+$", "",
                  t[:max(pos)].rstrip(" ,:;—–-"), flags=re.I)


def quentes(placar="palavras", minimo=3, n=10):
    """Itens que MAIS renderam no placar comum (vitórias/testes com mínimo de amostra), juntando os grupos
    parceiro+recapd. 22/10, funil do dono: o que funcionou volta pro prompt e pras tags dos próximos vídeos."""
    soma = {}
    try:
        import placar_titulos
        for grupo in ("parceiro", "recapd"):
            for item, (t, v) in placar_titulos.taxas(placar, grupo).items():
                tt, vv = soma.get(item, (0, 0))
                soma[item] = (tt + t, vv + v)
    except Exception:  # noqa: BLE001
        return []
    bons = sorted(((v / t, t, item) for item, (t, v) in soma.items() if t >= minimo and v / t > 0.5),
                  reverse=True)
    return [item for _r, _t, item in bons[:n]]


VERSOES = PROJECT_DIR / "config" / "seo_versoes.json"


def _versao_seo():
    """02/11 (dona: versionar título/tags pra comparar): ANIME_SEO_VERSAO=<nome> (o postar_longos passa a 'ativa_longo'
    de config/seo_versoes.json) troca estilos/tríade pelos daquela versão. Sem env = como sempre (nome None)."""
    nome = os.environ.get("ANIME_SEO_VERSAO")
    if not nome:
        return None, {}
    try:
        ver = json.loads(VERSOES.read_text(encoding="utf-8"))["versoes"][nome]
    except (OSError, ValueError, KeyError):
        log(f"[seo] versão {nome} não achada em {VERSOES.name} — segue o padrão")
        return None, {}
    return nome, ver


def escolher_estilo(estilos):
    """Thompson no placar ÚNICO de todos os projetos (placar_titulos, COMUM, desde 20/10)."""
    import placar_titulos
    return placar_titulos.escolher(estilos)


def registrar_resultado(estilo, venceu, video_id=""):
    """Chamado pela análise de performance (CTR/visualizações do vídeo contra a média do canal)."""
    import placar_titulos
    return placar_titulos.registrar(estilo, venceu, projeto="recapd", video_id=video_id)


REGRAS = (
    "Você é especialista em SEO e CTR do YouTube para canais de recap de anime (resumo narrado da história). "
    "Escreva TUDO em português do Brasil. Regras:\n"
    "1) NUNCA escreva o nome da obra (nem traduzido, nem abreviado, nem em hashtag/tag): risco de direitos autorais. "
    "Nomes dos personagens podem ir na descrição.\n"
    "2) Título = provocação/curiosidade forte + o MÁXIMO que couber de palavras que o público busca e que tenham a "
    "ver com a história. Estilo dos canais que mais crescem: frases longas tipo 'ELE FOI HUMILHADO por ser FRACO mas "
    "DESPERTOU o SISTEMA mais FORTE e agora TODOS o TEMEM'. Até {limite} caracteres, 3-5 palavras-chave em "
    "MAIÚSCULAS, no máximo 1 emoji. Sem prometer o que não acontece, sem palavrão.\n"
    "3) Descrição de 3 parágrafos curtos: 1ª linha = gancho com palavras buscadas; o que acontece sem contar o final "
    "(com as palavras buscadas naturalmente: anime recap, resumo anime, o gênero); pergunta pro público comentar + "
    "convite pra se inscrever; termina com 5-7 hashtags de GÊNERO/BUSCA (#anime #animerecap #resumoanime #isekai "
    "...){hashtag_extra}, nunca hashtag com o nome da obra.\n"
    "4) 20 a 30 tags de busca reais: palavras buscadas do gênero, frases como o público digita ('anime isekai "
    "completo', 'ele foi humilhado anime'). Sem o nome da obra.\n"
    "SEGURANÇA DE ANÚNCIOS: NUNCA use estas palavras no título/descrição/tags: "
    "morte, matar, morrer, sangue, arma, droga, suicídio, escravo, sexo, nu, nudez, tortura, assassino, "
    "pornografia, estupro, violação, bomba, terrorista. Use eufemismos seguros. "
    "Devolva SÓ JSON.")


# Versões em outra língua (anime_idiomas, 16/10): o prompt é todo em português e o modelo voltava pro português
# (título "ELE FOI HUMILHADO..." num canal hindi). Pede o alfabeto nativo e confere a resposta.
_ESCRITA = {"hindi": ("devanágari", r"[ऀ-ॿ]"), "tailandês": ("tailandês", r"[฀-๿]"),
            "russo": ("cirílico", r"[Ѐ-ӿ]"),
            "vietnamita": ("latino com os acentos do vietnamita",
                           r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]")}
_PT_COMUM = re.compile(r"\b(ele|ela|que|não|foi|uma|com|para|mas|quando|tudo|todos|garota|escola|depois)\b", re.I)


def _na_lingua(texto, idioma_nome):
    if not idioma_nome:
        return True
    esc = _ESCRITA.get(idioma_nome)
    if esc:
        return bool(re.search(esc[1], texto or "", re.I))
    return len(_PT_COMUM.findall(texto or "")) <= 1  # indonésio/italiano/inglês: não pode ter saído em português


_MIDIA_MANHWA = (  # Shorts do parceiro @kaijinre são resumo de MANHWA, não anime (16/10)
    ("recap de anime", "recap de manhwa (webtoon coreano)"),
    ("anime recap, resumo anime", "manhwa recap, resumo manhwa, webtoon"),
    ("#anime #animerecap #resumoanime #isekai", "#manhwa #manhwarecap #webtoon #resumomanhwa"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'manhwa romance escolar', 'ele foi humilhado manhwa'"),
)


_MIDIA_DORAMA = (  # Shorts de parceiro de DORAMA (k-drama/c-drama com atores reais; dono 17/10)
    ("recap de anime", "resumo de dorama (novela asiática com atores reais)"),
    ("anime recap, resumo anime", "dorama, kdrama, resumo dorama, novela coreana, cdrama"),
    ("#anime #animerecap #resumoanime #isekai", "#dorama #kdrama #resumodorama #doramas"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'dorama de vingança', 'ela foi humilhada dorama'"),
)
_MIDIA_FATOS = (
    ("recap de anime", "fatos incríveis e curiosidades"),
    ("anime recap, resumo anime", "fatos curiosos, você sabia, curiosidades, fatos incríveis"),
    ("#anime #animerecap #resumoanime #isekai", "#fatos #curiosidades #voce sabia #inacreditavel"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'fatos incríveis', 'você sabia que', 'curiosidades do mundo'"),
)
_MIDIA_ESPORTES = (
    ("recap de anime", "momentos épicos do esporte"),
    ("anime recap, resumo anime", "futebol, esporte, gol, melhores momentos, esportes"),
    ("#anime #animerecap #resumoanime #isekai", "#futebol #esporte #gol #esportes #melhores momentos"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'gol impossível', 'melhor jogada', 'momento épico futebol'"),
)
_MIDIA_FILME_SEM_VOZ = (
    ("recap de anime", "cena épica de filme"),
    ("anime recap, resumo anime", "filme, cena de filme, edição de filme, cinema"),
    ("#anime #animerecap #resumoanime #isekai", "#filme #cinema #cena #edit #filmes"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'cena épica filme', 'melhor cena do cinema'"),
)
_MIDIA_CURIOSIDADES = (
    ("recap de anime", "curiosidade surpreendente"),
    ("anime recap, resumo anime", "curiosidades, você sabia, fatos curiosos, coisas que você não sabia"),
    ("#anime #animerecap #resumoanime #isekai", "#curiosidades #vocesabia #fatos #inacreditavel"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'coisas que você não sabia', 'curiosidade incrível'"),
)
_MIDIA_NATUREZA = (
    ("recap de anime", "momento incrível da natureza"),
    ("anime recap, resumo anime", "natureza, animais, vida selvagem, planeta terra"),
    ("#anime #animerecap #resumoanime #isekai", "#natureza #animais #vidaselvagem #planetaterra"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'animal incrível', 'natureza surpreendente'"),
)
_MIDIA_QUIZ = (
    ("recap de anime", "teste seus conhecimentos"),
    ("anime recap, resumo anime", "quiz, teste, desafio, pergunta, você sabe"),
    ("#anime #animerecap #resumoanime #isekai", "#quiz #teste #desafio #vocesabe"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'quiz difícil', 'teste de conhecimento', 'você acerta'"),
)
_MIDIA_INFO_ERRADA = (
    ("recap de anime", "será que isso é verdade?"),
    ("anime recap, resumo anime", "fatos, verdade ou mentira, você sabia, informação, teste"),
    ("#anime #animerecap #resumoanime #isekai", "#fatos #verdadeOuMentira #vocesabia #teste"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'isso é mentira', 'você acreditava nisso', 'fato errado'"),
)
_MIDIA_IA_FUTURO = (
    ("recap de anime", "o futuro com inteligência artificial"),
    ("anime recap, resumo anime", "inteligência artificial, ia, futuro, tecnologia, inovação"),
    ("#anime #animerecap #resumoanime #isekai", "#ia #inteligenciaartificial #futuro #tecnologia"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'ia vai mudar tudo', 'futuro da tecnologia'"),
)
_MIDIA_MOTIVACAO = (
    ("recap de anime", "motivação para sua vida"),
    ("anime recap, resumo anime", "motivação, inspiração, superação, mindset, sucesso"),
    ("#anime #animerecap #resumoanime #isekai", "#motivação #inspiração #superação #mindset #sucesso"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'nunca desista', 'motivação diária', 'inspiração'"),
)
_MIDIA_FINANCAS = (
    ("recap de anime", "dica financeira que muda sua vida"),
    ("anime recap, resumo anime", "finanças, investimento, dinheiro, economia, renda extra"),
    ("#anime #animerecap #resumoanime #isekai", "#finanças #investimento #dinheiro #rendaextra"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'como ganhar dinheiro', 'investimento', 'finanças pessoais'"),
)
_MIDIA_HISTORIA_MITOLOGIA = (
    ("recap de anime", "história e mitologia fascinantes"),
    ("anime recap, resumo anime", "história, mitologia, civilização antiga, lendas, mistérios"),
    ("#anime #animerecap #resumoanime #isekai", "#história #mitologia #lendas #civilização #mistérios"),
    ("'anime isekai completo', 'ele foi humilhado anime'", "'civilização perdida', 'mitologia grega', 'história antiga'"),
)
_MIDIAS = {
    "manhwa": _MIDIA_MANHWA, "dorama": _MIDIA_DORAMA, "fatos": _MIDIA_FATOS,
    "esportes": _MIDIA_ESPORTES, "filme_sem_voz": _MIDIA_FILME_SEM_VOZ,
    "curiosidades": _MIDIA_CURIOSIDADES, "natureza": _MIDIA_NATUREZA, "quiz": _MIDIA_QUIZ,
    "info_errada": _MIDIA_INFO_ERRADA, "ia_futuro": _MIDIA_IA_FUTURO,
    "motivacao": _MIDIA_MOTIVACAO, "financas": _MIDIA_FINANCAS,
    "historia_mitologia": _MIDIA_HISTORIA_MITOLOGIA,
}


def gerar_seo_anime(titulo_original, descricao_original="", tags_originais=(), video_id="",
                    nome_obra="", formato="deitado", roteiro="", midia="anime", idioma_nome=None):
    """Pacote {titulo, titulos, descricao, tags, estilo} pro vídeo, ou None se o LLM falhar.

    titulo_original: título do vídeo-fonte no YouTube (só contexto).
    nome_obra: nome do anime (anime_auto._extrair_nome_anime) — proibido em tudo que sai daqui.
    formato: "deitado" (16:9) ou "short" (9:16, ~1 min).
    roteiro: narração em pt-BR (opcional; melhora o título — sem ela o LLM usa o título/descrição originais).
    """
    b = _banco()
    estilos = b.get("estilos_titulo") or {e: "" for e in ESTILOS}
    nome_v, ver = _versao_seo()
    if ver.get("estilos_titulo"):
        estilos = dict(ver["estilos_titulo"])
    if ver.get("estilos"):
        estilos = {e: d for e, d in estilos.items() if e in ver["estilos"]} or estilos
    if os.environ.get("CORTES_NINGUEM_ESPERAVA") == "A" and "provocacao" in estilos:
        # 30/10 variante T11 (bin\variantes.py): A = texto de antes de 30/10, sem proibir "NINGUÉM ESPERAVA";
        # B (ou sem env) = seo_palavras.json atual, que proíbe. Muda só o Short de parceiro (a env vem do fazer_short)
        estilos = dict(estilos, provocacao="provocação curiosa/chocante (ex.: ELE PERDEU TUDO, O PODER PROIBIDO, "
                                           "NINGUÉM ESPERAVA) + 2-3 palavras buscadas da história")
    short = formato == "short"
    limite = 85 if short else 95
    regras = REGRAS.format(limite=limite, hashtag_extra=" + #shorts" if short else "")
    for de, para in _MIDIAS.get(midia, ()):  # manhwa/dorama trocam os termos de anime (parceiros, 16-17/10)
        regras = regras.replace(de, para)
    if short and not idioma_nome:  # 27/10: regras do MELHORADOR dos Cortes (bin\cortes_ajustes.json, só Short de parceiro)
        try:
            import anime_script
            extra = anime_script.ajustes_cortes().get("regras_titulo") or []
        except Exception:  # noqa: BLE001
            extra = []
        if extra:
            regras = regras.replace("Devolva SÓ JSON.", "\n".join(f"- {r}" for r in extra) + "\nDevolva SÓ JSON.")
    triade = ver.get("triade")
    if triade is None:
        triade = os.environ.get("ANIME_TITULO_TRIADE", "1") != "0"
    if not short and not idioma_nome and triade:
        # 30/10: variante B do A/B "titulo_triade" (postar_longos passa ANIME_TITULO_TRIADE pelo render.json "ab")
        # L-F1 (LONGOS_MELHORIAS.md) 30/10 (Fable; engenharia reversa de 14 recaps, PADROES_COMUNS item 1): os 3 de 450k-2,1M views usam a tríade
        # humilhação/status baixo -> virada/vantagem -> vingança, riqueza ou as que desprezavam agora querem; os de 3-13k
        # eram descritivos ("renasceu como árvore", "escolhido para batalha"). Vale pros 3 estilos do longo.
        regras = regras.replace("Devolva SÓ JSON.", "- Recap completo: sempre que a história tiver, cada título segue a tríade "
                                "[como ele era humilhado/desprezado] + [a virada/vantagem que ganhou] + [a vingança, a riqueza "
                                "ou quem o desprezava agora implorando], com palavras concretas da história "
                                "(ex.: 'HUMILHADO por ser POBRE, ele despertou o SISTEMA e agora a nobreza IMPLORA por ele'). "
                                "Evite título só descritivo do poder ou do mundo.\nDevolva SÓ JSON.")
    if not short and not idioma_nome and os.environ.get("ANIME_VARIANTE") == "anime_recap":
        # 02/11 dona (variante RECAP DE ANIME, docs\VARIANTE_ANIME_RECAP.md; estudo de 180 vídeos de Mattz/NoteLey/
        # DuduziVEL): os que vendem (até 1,5 mi) = premissa do protagonista com 3-6 PALAVRAS-CHAVE EM MAIÚSCULAS no meio,
        # sem o nome do anime; o sufixo "(1-12) - ANIME RECAP" entra depois (abaixo). Tags/descrição COM o nome do anime.
        regras = regras.replace("Devolva SÓ JSON.", "- RECAP DE ANIME (temporada inteira): cada título é a premissa do "
                                "protagonista numa frase, com 3 a 6 palavras-chave EM MAIÚSCULAS no meio e o resto em "
                                "minúsculas (ex.: 'Caçador FRAQUINHO recebe um sistema para ser o ÚNICO que pode subir de "
                                "NÍVEL', 'Bebê ABANDONADO foi criado por DEMÔNIOS, mas secretamente era o ESCOLHIDO DE "
                                "DEUS'). Sem o nome do anime no título. Na DESCRIÇÃO: 1 frase de sinopse com os nomes dos "
                                "personagens. Nas TAGS: o nome do anime em várias formas (é busca ativa).\nDevolva SÓ JSON.")
    if idioma_nome:  # versão para canal estrangeiro (anime_idiomas, 16/10)
        regras = regras.replace("Escreva TUDO em português do Brasil.",
                                f"Escreva TUDO em {idioma_nome} (título, descrição, tags, hashtags e texto_capa), "
                                f"para o público de {idioma_nome}; as 'palavras buscadas' abaixo são do público "
                                "brasileiro: use o espírito delas, traduzido/adaptado.")
    obra_txt = f"Nome da obra (PROIBIDO escrever, nem traduzido): {nome_obra}\n" if nome_obra else ""
    resumo = re.sub(r"\s+", " ", roteiro or "")[:3000]
    # 22/10 (funil): palavras/tags que MAIS renderam nos vídeos já medidos entram no prompt — o LLM encaixa
    # o que o público comprovadamente clica (só em pt; o placar é do público brasileiro)
    pal_q = quentes("palavras") if not idioma_nome else []
    contexto = (f"{obra_txt}Título do vídeo-fonte (inglês, só contexto): {titulo_original}\n"
                f"Descrição do vídeo-fonte: {(descricao_original or '')[:400]}\n"
                f"Tags do vídeo-fonte: {', '.join(list(tags_originais or [])[:10])}\n"
                + (f"Narração do nosso vídeo (resumo): {resumo}\n" if resumo else "")
                + _palavras(b)
                + (f"\nPalavras que MAIS renderam nos nossos vídeos medidos (views em 48 h) — encaixe com "
                   f"naturalidade as que tiverem a ver com ESTE vídeo, no título e nas tags: {', '.join(pal_q)}\n"
                   if pal_q else ""))
    tipo = ("Vídeo: Short vertical de ~1 minuto com o começo da história." if short
            else "Vídeo: recap completo narrado (16:9).")
    prompt = (regras + f"\n{tipo} Gere 3 títulos, um por estilo:\n"
              + "\n".join(f"- {e}: {d}" for e, d in estilos.items()) + "\n\n" + contexto
              + "\n'nomes_da_obra' = TODOS os nomes pelos quais a obra é conhecida (inglês, português, original "
              "romanizado e as formas curtas que o público usa, ex. 'Shield Hero', 'Herói do Escudo') — é a lista "
              "do que NÃO pode aparecer; nenhum deles pode estar nos títulos/descrição/tags."
              + "\n'texto_capa' = frase da CAPA: 2 a 4 palavras em MAIÚSCULAS, no máx. 22 caracteres, provocação da "
              "história (ex.: 'O MAIS FRACO?', 'TRAÍDO POR TODOS'), sem emoji e sem o nome da obra."
              "\n'protagonista_visual' = aparência do protagonista EM INGLÊS pra desenhar a capa (gênero, adulto, "
              "cabelo, olhos, roupa, cores, arma), SEM nomes e SEM símbolos/logos/emblemas."
              f"\n'generos' = 1 a 4 destes: {', '.join(b.get('generos', {}))}."
              + '\nFormato: {"nomes_da_obra": [...], "titulos": {' + ", ".join(f'"{e}": "..."' for e in estilos)
              + '}, "descricao": "...", "tags": [...], "texto_capa": "...", "protagonista_visual": "...", '
              '"generos": [...]}')
    if idioma_nome:  # no FIM do prompt: é o que mais pesa (antes o modelo devolvia português)
        esc = _ESCRITA.get(idioma_nome, (None,))[0]
        prompt += (f"\n\nIMPORTANTE: título(s), descrição, tags, hashtags e texto_capa em {idioma_nome}"
                   + (f", escritos no alfabeto {esc}" if esc else "")
                   + ". NÃO escreva em português (o público deste canal não fala português).")
    chave = f"{VERSAO}{'|' + nome_v if nome_v else ''}|{video_id}|{formato}{'|' + midia if midia != 'anime' else ''}{'|' + idioma_nome if idioma_nome else ''}|{hashlib.md5((titulo_original or '').encode('utf-8')).hexdigest()[:8]}"
    r = _pedir(chave, prompt, lambda r: isinstance(r.get("titulos"), dict)
               and all(r["titulos"].get(e) for e in estilos) and r.get("tags")
               and _na_lingua(" ".join(str(v) for v in r["titulos"].values()), idioma_nome))
    if not r:
        return None
    if idioma_nome:  # o modelo copiava as tags de EXEMPLO do prompt (em português) pro canal estrangeiro
        r["tags"] = [t for t in r.get("tags", []) if not _PT_COMUM.search(str(t))
                     and not re.search(r"\b(escolar|humilhado|resumo|menino|menina)\b", str(t), re.I)] or r.get("tags", [])
    nomes = [nome_obra] + [n for n in (r.get("nomes_da_obra") or []) if isinstance(n, str)]
    r = _sem_obra(r, nomes)
    rx = _rx_obra(nomes)
    tc = re.sub(r"\s+", " ", str(r.get("texto_capa") or "")).strip().upper()
    r["texto_capa"] = "" if (rx and rx.search(tc)) or len(tc) > 26 else tc
    pv = str(r.get("protagonista_visual") or "")
    r["protagonista_visual"] = "" if rx and rx.search(pv) else pv[:400]
    # 21/10: "#shorts" sai do título (fica na descrição — é lá que o YouTube usa; no título só gastava 8 caracteres)
    limpo = {e: _caps_no_limite(re.sub(r"\s*#shorts\b", "", str(t), flags=re.I).strip())
             for e, t in r["titulos"].items()}
    r["titulos"] = {e: c for e, t in limpo.items() if (c := _corta(t, limite)) and len(c) >= 15}
    if not r["titulos"]:
        return None
    # 26/10: a IA colava a palavra buscada no meio da frase ("ELE DESCOBRIU ovos BICHOS MAIS ESTRANHOS") — título com
    # palavra minúscula solta entre duas MAIÚSCULAS sai da disputa (se sobrar outro)
    _lig = {"para", "como", "mais", "pela", "pelo", "quando", "onde", "sobre", "entre", "depois", "antes", "porque",
            "isso", "essa", "esse", "isto", "sem", "com", "até", "após", "nunca", "sempre", "muito", "tudo", "todos"}
    colado = re.compile(r"\b[A-ZÀ-Ý]{2,}\s+([a-zà-ÿ]{4,})\s+[A-ZÀ-Ý]{2,}\b")
    bons = {e: t for e, t in r["titulos"].items()
            if not any(m.group(1) not in _lig for m in colado.finditer(t))}
    if bons and len(bons) < len(r["titulos"]):
        logging.info(f"[seo] título com palavra colada descartado: "
                     f"{[t for e, t in r['titulos'].items() if e not in bons]}")
        r["titulos"] = bons
    estilo = escolher_estilo(list(r["titulos"]))
    titulo = r["titulos"][estilo]
    # L-12 (LONGOS_MELHORIAS, 01/11): sufixo de maratona ("- Completo", como o 1TXD) só quando o longo É a história
    # inteira — quem sabe é quem chama (ANIME_LONGO_COMPLETO=1); "(1-2)" do vídeo-fonte é mantido se ele já veio assim
    if not short and not idioma_nome:
        m_parte = re.search(r"\((\d+)\s*-\s*(\d+)\)", titulo_original or "")
        suf = (f" ({m_parte.group(1)}-{m_parte.group(2)})" if m_parte
               else " - Completo" if os.environ.get("ANIME_LONGO_COMPLETO") == "1" else "")
        if os.environ.get("ANIME_VARIANTE") == "anime_recap":  # 02/11: "(1-12) - ANIME RECAP" como os de anime
            suf = (suf or " (COMPLETO)") + " - ANIME RECAP"
        if suf and suf.strip(" -").lower() not in titulo.lower():
            base_t = _corta(titulo, 100 - len(suf))
            if base_t:  # sem ponto natural de corte = fica sem o sufixo (meia frase no título é pior)
                titulo = base_t + suf
    desc = r.get("descricao", "")
    if short and "#shorts" not in desc.lower():
        desc = desc.rstrip() + " #shorts"
    # 22/10 (funil): completa as tags com as que mais renderam (sem duplicar, sem passar de 28 e sem obra)
    if not idioma_nome:
        tags_q = quentes("tags", n=8)
        atuais = {str(t).casefold().strip() for t in r.get("tags", [])}
        extra = [t for t in tags_q if t not in atuais and not (rx and rx.search(t))
                 and tag_do_nicho(t, list(r.get("tags", [])) + [titulo, midia])]
        if extra:
            r["tags"] = list(r.get("tags", [])) + extra[:max(0, 28 - len(atuais))]
    return {**r, "titulo": titulo[:100], "descricao": desc[:5000], "estilo": estilo, "seo_versao": nome_v}


# 23/10: a tag "quente" do funil vinha de QUALQUER nicho — Short de futebol saiu com 'manhwa hindi', 'resumo de filme',
# 'ela foi humilhada dorama' (tag sem relação = metadado enganoso pro YouTube) e as 28 passaram dos 500 caracteres do
# Studio (upload travado). Tag com palavra de nicho só entra se o vídeo já é daquele nicho; tag genérica entra sempre.
_NICHO_PAL = re.compile(r"\b(manhwa|manhua|webtoon|mang[aá]|anime|dorama|k-?drama|novela|filme|cinema|s[eé]rie|hindi|"
                        r"futebol|gol|esporte\w*|game\w*|jogo\w*|gta|minecraft|bicho\w*|animal\w*|finan\w*|"
                        r"invest\w*|isekai|webnovel)\b", re.I)


def tag_do_nicho(tag, contexto):
    proprio = " ".join(str(c) for c in contexto).casefold()
    return all(re.search(r"\b" + re.escape(m.casefold()) + r"\b", proprio) for m in _NICHO_PAL.findall(str(tag)))
