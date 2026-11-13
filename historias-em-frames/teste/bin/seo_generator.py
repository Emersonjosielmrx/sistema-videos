# -*- coding: utf-8 -*-
"""seo_generator.py — título, descrição e tags das histórias (§1 de MELHORIAS_PARA_TODOS_OS_PROJETOS.md).

Copiado de D:\\hipercool-videos\\bin\\seo.py e adaptado aos Shorts de história (terror, drama, superação, romance,
comédia, religioso...):
- 3 títulos (estilos busca / provocacao / curiosidade) escritos A PARTIR DA HISTÓRIA (título, tema, narração), um
  escolhido por Thompson (workspace/titulos_estilos.json); o estilo vai pro postar.json (estilo_titulo).
- Palavras buscadas: config/seo_palavras.json (autocompletar do YouTube pt-BR).

Quem chama: story_pipeline._write_postar_json (o postar.json é a base que a rede do manhwa-react adapta por canal).
LLM: claude_client.generate_text (gateway OmniRoute, secrets/omniroute.json) -> gemini_llm.generate_text.
Se os dois falharem devolve None e quem chama segue com o crew/viralizador de antes.
"""
import hashlib
import json
import random
import re
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE = PROJECT_DIR / "workspace" / "cache" / "seo"
PALAVRAS = PROJECT_DIR / "config" / "seo_palavras.json"
STATS_TITULOS = PROJECT_DIR / "workspace" / "titulos_estilos.json"
VERSAO = "v3"  # v1 não recebia a história e chamava funções que não existem aqui; v3 pede texto_capa
ESTILOS = ("busca", "provocacao", "curiosidade")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _llm(prompt):
    """Gateway (claude_client) primeiro, Gemini de reserva. Devolve dict ou None."""
    import claude_client
    try:
        if claude_client.is_available():
            r = claude_client._extract_json(claude_client.generate_text(prompt, max_tokens=3000, temperature=0.7))
            if isinstance(r, dict):
                return r
    except Exception as e:  # noqa: BLE001
        log(f"  [!] seo: gateway falhou ({str(e)[:80]})")
    try:
        import gemini_llm
        r = claude_client._extract_json(gemini_llm.generate_text(prompt, max_tokens=3000, temperature=0.7))
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
    log("  [!] seo: agente não devolveu um pacote válido; usando o modelo de antes")
    return None


def _banco():
    try:
        return json.loads(PALAVRAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _palavras(b, genero):
    gen = b.get("generos", {})
    pal = gen.get(genero) or [w for ws in gen.values() for w in ws]
    return (f"Palavras buscadas (use SÓ as que combinam com a história): "
            f"{', '.join(dict.fromkeys(b.get('sempre', []) + pal))}\n"
            f"Como o público busca (padrões reais): {' | '.join(b.get('padroes_reais', []))}\n")


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


def escolher_estilo(estilos):
    """Thompson no placar ÚNICO de todos os projetos (placar_titulos, COMUM, desde 20/10)."""
    import placar_titulos
    return placar_titulos.escolher(estilos)


def registrar_resultado(estilo, venceu, video_id=""):
    """Chamado pela análise de performance (CTR/visualizações do vídeo contra a média do canal)."""
    import placar_titulos
    return placar_titulos.registrar(estilo, venceu, projeto="historias", video_id=video_id)


REGRAS = (
    "Você é especialista em SEO e CTR do YouTube para canais de Shorts de histórias narradas (terror, drama, "
    "superação, romance, comédia, fé). Escreva TUDO em português do Brasil. Regras:\n"
    "1) Título = provocação/curiosidade forte + o MÁXIMO que couber de palavras que o público busca e que tenham a "
    "ver com ESTA história. Estilo dos canais que mais crescem: frases longas tipo 'ELA OUVIU batidas NA PORTA às 3h "
    "mas MORAVA SOZINHA e o que aconteceu VAI te ARREPIAR'. Até 85 caracteres (o #shorts entra depois), 3-5 "
    "palavras-chave em MAIÚSCULAS, no máximo 1 emoji. Só prometa o que acontece na história; sem palavrão.\n"
    "2) Descrição de 2-3 linhas curtas: gancho com palavras buscadas; pergunta pro público comentar + convite pra se "
    "inscrever; termina com 5-7 hashtags de GÊNERO/BUSCA (#historia #terror #creepypasta ...) incluindo #shorts.\n"
    "3) 15 a 25 tags de busca reais: palavras buscadas do gênero, frases como o público digita ('história de terror "
    "real', 'história de superação emocionante').\n"
    "SEGURANÇA DE ANÚNCIOS: NUNCA use estas palavras no título/descrição/tags: "
    "morte, matar, morrer, sangue, arma, droga, suicídio, escravo, sexo, nu, nudez, tortura, assassino, "
    "pornografia, estupro, violação, bomba, terrorista. Use eufemismos seguros. "
    "Devolva SÓ JSON.")


def gerar_seo_historia(genero, tema="", titulo_base="", narracao="", chave=""):
    """Pacote {titulo, titulos, descricao, tags, estilo} pro Short da história, ou None se o LLM falhar.

    genero: terror / superacao / drama / romance / comedia / religioso ...
    tema, titulo_base, narracao: o que a história conta (sem isso o título promete o que não acontece).
    chave: identifica a história no cache (ex.: pasta de saída).
    """
    b = _banco()
    estilos = b.get("estilos_titulo") or {e: "" for e in ESTILOS}
    resumo = re.sub(r"\s+", " ", narracao or "")[:2500]
    contexto = (f"Gênero: {genero}\nTema: {tema}\nTítulo de trabalho: {titulo_base}\n"
                + (f"Narração da história: {resumo}\n" if resumo else "") + _palavras(b, genero))
    prompt = (REGRAS + "\nGere 3 títulos, um por estilo:\n"
              + "\n".join(f"- {e}: {d}" for e, d in estilos.items()) + "\n\n" + contexto
              + "\n'texto_capa' = frase da CAPA: 2 a 4 palavras em MAIÚSCULAS, no máx. 22 caracteres, provocação "
              "desta história (ex.: 'TEM ALGO NO RALO', 'ELA MENTIU 5 ANOS'), sem emoji."
              + '\nFormato: {"titulos": {' + ", ".join(f'"{e}": "..."' for e in estilos)
              + '}, "descricao": "...", "tags": [...], "texto_capa": "..."}')
    ch = f"{VERSAO}|{chave or titulo_base}|{hashlib.md5((tema + titulo_base).encode('utf-8')).hexdigest()[:8]}"
    r = _pedir(ch, prompt, lambda r: isinstance(r.get("titulos"), dict)
               and all(r["titulos"].get(e) for e in estilos) and r.get("tags"))
    if not r:
        return None
    tc = re.sub(r"\s+", " ", str(r.get("texto_capa") or "")).strip().upper()
    r["texto_capa"] = tc if len(tc) <= 26 else ""
    r["titulos"] = {e: c for e, t in r["titulos"].items() if (c := _corta(t, 91)) and len(c) >= 15}
    if not r["titulos"]:
        return None
    estilo = escolher_estilo(list(r["titulos"]))
    titulo = r["titulos"][estilo]
    if "#shorts" not in titulo.lower():
        titulo = f"{titulo} #shorts"
    desc = r.get("descricao", "")
    if "#shorts" not in desc.lower():
        desc = desc.rstrip() + " #shorts"
    return {**r, "titulo": titulo[:100], "descricao": desc[:5000], "estilo": estilo}
