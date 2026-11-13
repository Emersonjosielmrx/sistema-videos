# -*- coding: utf-8 -*-
"""seo.py — AGENTE de título, descrição e tags dos vídeos (completo vertical, Shorts e longo 16:9).

Uma chamada de LLM por (capítulo, idioma, tipo), em cache (workspace/cache/seo/). Ordem: Sonnet do proxy do
Claude Code -> Gemini do proxy -> Gemini direto. Falhou tudo -> devolve None e quem chamou usa o modelo fixo.

  pacote(chave_fila, idioma, "completo")          -> {titulo, descricao, tags}
  pacote(chave_fila, idioma, "shorts", n=7)       -> {titulos: [...], descricao, tags}
  pacote_longo(obra_slug, caps, idioma, capitulos_txt) -> {titulo, descricao, tags}

O que o agente recebe: nome da obra, capítulo, o roteiro narrado (resumo), gancho e pergunta do editorial.
Regras (no prompt): título com curiosidade e no máx. ~70 caracteres, nome da obra nas tags e na descrição,
20–30 tags de busca reais (obra, gênero, "manhwa recap", "resumo manhwa"...), sem prometer o que não acontece.
"""
import hashlib
import json
import re
from pathlib import Path

from hp_common import PROJECT_DIR, log

CACHE = PROJECT_DIR / "workspace" / "cache" / "seo"
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
    """Sem '#', sem repetidas, cada uma <= 30 caracteres e o total <= 480 (limite do YouTube é 500)."""
    out, total = [], 0
    for t in tags:
        t = re.sub(r"\s+", " ", str(t).replace("#", "")).strip()[:30]
        if t and t.lower() not in {o.lower() for o in out} and total + len(t) + 1 <= 480:
            out.append(t)
            total += len(t) + 1
    return out


REGRAS = (
    "Você é especialista em SEO e retenção do YouTube para canais de recap de manhwa (resumo narrado). "
    "Escreva TUDO em {lingua}. Regras: título com curiosidade/emoção, no máximo 70 caracteres, 1-2 palavras "
    "em MAIÚSCULAS, sem prometer o que não acontece e sem palavrão; descrição de 3 parágrafos curtos (gancho; o "
    "que acontece no capítulo sem contar o final; pergunta pro público comentar + convite pra se inscrever), com "
    "o nome da obra e o número do capítulo, terminando com 4-6 hashtags; 20 a 30 tags de busca reais (nome da "
    "obra e variações, gênero, 'manhwa recap', 'resumo de manhwa', 'manhwa dublado', nomes dos personagens, "
    "termos que o público digita). Nada de conteúdo sexual explícito no texto. Devolva SÓ JSON.")


def pacote(chave, idioma=None, tipo="completo", n=0):
    recap, obra, cap = recap_capitulo(chave, idioma)
    if not recap:
        return None
    ed = recap.get("_editorial") or {}
    base = (f"Obra: {obra['titulo']}\nCapítulo: {cap}\nGancho: {ed.get('gancho', '')}\n"
            f"Pergunta do fim: {ed.get('pergunta', '')}\nRoteiro narrado (resumo):\n{_resumo(recap)}\n\n")
    lingua = NOMES_IDIOMA.get(idioma, idioma)
    if tipo == "shorts":
        prompt = (REGRAS.format(lingua=lingua) + f"\nSão {n} Shorts (partes em sequência do capítulo). Gere "
                  f"'titulos' (lista com EXATAMENTE {n} títulos, um por parte, cada um com no máx. 60 caracteres, "
                  "terminando com o número da parte tipo '(Parte 1)' e no máximo 1-2 emojis), 'descricao' (curta, "
                  "2 linhas + hashtags incluindo #shorts) e 'tags'.\n\n" + base
                  + 'Formato: {"titulos": [...], "descricao": "...", "tags": [...]}')
        return _pedir(f"{chave}|{idioma}|shorts|{n}", prompt,
                      lambda r: len(r.get("titulos", [])) == n and r.get("tags"))
    prompt = (REGRAS.format(lingua=lingua) + "\nVídeo: o capítulo completo narrado.\n\n" + base
              + 'Formato: {"titulo": "...", "descricao": "...", "tags": [...]}')
    return _pedir(f"{chave}|{idioma}|completo", prompt, lambda r: r.get("titulo") and r.get("tags"))


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
              f"{caps[-1]} de '{obra['titulo']}'. O título deve dizer que é a história completa/maratona dos "
              "capítulos. Na descrição, inclua no fim a lista de capítulos com minutos exatamente como abaixo.\n\n"
              + "\n".join(resumos) + f"\n\nLista de capítulos (copie igual):\n{capitulos_txt}\n\n"
              + 'Formato: {"titulo": "...", "descricao": "...", "tags": [...]}')
    return _pedir(f"longo|{'|'.join(chaves)}|{idioma}", prompt, lambda r: r.get("titulo") and r.get("tags"))
