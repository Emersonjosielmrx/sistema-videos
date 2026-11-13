# -*- coding: utf-8 -*-
"""publicar.py — fecha o ciclo: gera caption (titulo/descricao/hashtags) e
escreve o postar.json ao lado do mp4, no padrao que o postador le.

Padrao do doc: D:\\hipercool-materiais\\_postados\\PADRAO_DOC_POSTAGEM.md
  categoria=vo3, tipo=short, campos obrigatorios: arquivo/categoria/tipo/
  titulo/descricao/tags. Preencher evita o custo do Gemini na cola.

A caption e gerada pelo LLM (gateway pro -> chaves), com tom da PERSONA do
canal (inteligencia.py). Fallback keyless se o LLM falhar.

Uso:
    from publicar import gerar_postar_json
    gerar_postar_json(mp4_path, canal_nome, tema, fala, cta=None, thumb=None)
"""
import json
import os
import re
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))


def _slug(txt):
    return re.sub(r"[^a-z0-9]+", "-", (txt or "").lower()).strip("-")[:40]


def _persona(tema):
    try:
        import inteligencia
        return inteligencia.get_persona(tema)
    except Exception:
        return {"publico": "jovens brasileiros", "tom": "energico"}


def _caption_llm(canal, tema, fala, cta=""):
    """Gera titulo/descricao/tags via LLM. Retorna dict ou None se falhar."""
    try:
        from llm_client import LLMClient
    except Exception:
        return None
    p = _persona(tema)
    prompt = f"""Você é especialista em SEO de YouTube Shorts em português brasileiro.
Gere metadados para postar este Short.

Canal: {canal}
Tema: {tema}
Fala do vídeo: {fala}
Público-alvo: {p.get('publico')}
Tom: {p.get('tom')}

Responda APENAS um JSON válido (sem markdown), com:
- "titulo": até 90 caracteres, com as palavras que esse público realmente digita na busca.
  Escreva como uma frase de gente, diferente a cada vídeo. NÃO use aspas dentro.
- "descricao": 2-3 frases que contam o que a pessoa vai ver, no tom do canal, e uma pergunta no fim.
  Máx 400 caracteres.
- "tags": lista de 12 tags de busca em pt-BR (strings curtas), relevantes ao tema.

REGRAS (o canal já foi suspenso por parecer spam, então são obrigatórias):
- Nada de telefone, WhatsApp, "chama no zap", endereço de site, "clique no link" ou "link na bio".
- No máximo 1 emoji no título e 1 na descrição. Pode não ter nenhum.
- Nada de "#shorts #ia #viral #brasil" nem hashtag genérica repetida: no máximo 3 hashtags,
  e só se forem do assunto do vídeo.
- Nada de promessa ("garantido", "fique rico", "ganhe dinheiro fácil").
- Não repita a mesma fórmula de título que você usaria para qualquer vídeo.

Exemplo do formato:
{{"titulo": "...", "descricao": "...", "tags": ["...", "..."]}}"""
    try:
        resp = LLMClient().send(prompt, max_tokens=600)
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if not m:
            return None
        data = json.loads(m.group(0))
        titulo = _sem_contato((data.get("titulo") or "").strip())[:100]
        descricao = _sem_contato((data.get("descricao") or "").strip())[:4900]
        tags = [_sem_contato(str(t).strip()) for t in (data.get("tags") or []) if str(t).strip()][:15]
        tags = [t for t in tags if t]
        if titulo and descricao and tags:
            return {"titulo": titulo, "descricao": descricao, "tags": tags}
    except Exception:
        pass
    return None


# telefone, url, @handle e convites a sair do YouTube: o revisor da rede tambem
# barra, mas o veo nao pode nem gerar. (item AB-06 do PLANO_MELHORIAS_VEO.md)
_RX_CONTATO = re.compile(
    r"(?:\+?\d[\d\s().-]{7,}\d)"                       # telefone
    r"|(?:(?:https?://|www\.)\S+)"                     # url
    r"|(?:\b\w+\.(?:com|com\.br|net|br|io|app)\b\S*)"  # dominio solto
    r"|(?:@[A-Za-z0-9_.]{3,})"                         # @handle
    # chamadas para sair do YouTube. A palavra "WhatsApp" sozinha NAO entra:
    # e o nome de um produto da dona ("Ligacoes WhatsApp com IA"), e descrever o
    # produto e legitimo; o que a politica pune e mandar a pessoa para la.
    r"|(?:\b(?:chama|chame|fala|fale|me chama|manda|mande)\s+(?:no|na|pelo|pela)\s+"
    r"(?:whats?app|zap|dire?c?t|insta\w*|telegram)\b)"
    r"|(?:\bno\s+zap\b|\bclique?\s+no\s+link\b|\blink\s+na\s+bio\b|\blink\s+na\s+descri\w+\b)",
    re.I)


def _sem_contato(texto: str) -> str:
    """Apaga telefone, link, @handle e chamada para sair do YouTube.

    Mantem o nome do produto (ex.: "Ligacoes WhatsApp com IA"): o que sai e o
    contato e o convite a sair da plataforma, nao a palavra.
    """
    if not texto:
        return texto
    limpo = _RX_CONTATO.sub("", texto)
    return re.sub(r"\s{2,}", " ", limpo).strip(" -–—·|,;")


def _caption_fallback(canal, tema, fala, cta=""):
    """Caption keyless quando o LLM falha. Sem template de hashtag e sem contato."""
    base = _sem_contato((fala or tema or canal).split("|")[0].strip())
    titulo = base[:90] if base else canal
    tema_slug = tema or canal
    # a descricao e a propria fala do video + o tema; sem CTA de contato e sem
    # a cauda "#shorts #ia #viral #brasil", que era igual em todo video.
    desc = base if base else f"{canal} — {tema_slug}"
    tags = [t for t in [_slug(canal).replace("-", " "), _slug(tema_slug).replace("-", " "),
                        "inteligencia artificial", "curiosidades", "tecnologia"] if t]
    return {"titulo": titulo, "descricao": desc.strip(), "tags": tags}


def gerar_caption(canal, tema, fala, cta=""):
    """Caption com LLM; cai no fallback keyless se falhar."""
    return _caption_llm(canal, tema, fala, cta) or _caption_fallback(canal, tema, fala, cta)


def gerar_postar_json(mp4_path, canal_nome, tema, fala, cta="", thumb=None,
                      canais=None, extra=None):
    """Escreve <nome-do-video>.postar.json AO LADO do mp4. Devolve o caminho.

    Ate 15/10 o nome era fixo ("postar.json"), um por pasta: cada video novo
    apagava os metadados do anterior, e quem postava caia no texto generico.
    Agora e um arquivo por video. (item AB-06 do PLANO_MELHORIAS_VEO.md)

    Nao levanta excecao — em pior caso escreve um doc minimo com _REVISAR.
    """
    mp4 = Path(mp4_path)
    doc = {
        "arquivo": mp4.name,
        "categoria": "vo3",
        "tipo": "short",
        "pronto": True,
        # a pessoa que fala e gerada por IA: o YouTube exige a declaracao de
        # "conteudo alterado ou sintetico" (support.google.com/youtube/answer/14328491).
        # Quem posta tem que mandar --sintetico / containsSyntheticMedia.
        "sintetico": True,
    }
    try:
        cap = _caption_llm(canal_nome, tema, fala, cta)
        if cap:
            doc.update(cap)
            doc["_fonte_caption"] = "llm"
        else:
            doc.update(_caption_fallback(canal_nome, tema, fala, cta))
            doc["_fonte_caption"] = "fallback"
    except Exception as e:
        doc.update(_caption_fallback(canal_nome, tema, fala, cta))
        doc["_REVISAR"] = f"caption fallback: {str(e)[:80]}"
    # metadados uteis pro postador/aprendizado
    doc["canal_veo"] = canal_nome
    doc["tema_veo"] = tema
    doc["fala"] = fala
    # Canal: quem decide e o diretor da rede (mr/rede.py), que conhece o nicho de
    # cada canal vivo. Lista vazia = "decida voce". So respeita 'canais' se vier
    # explicito de quem chamou.
    if not canais:
        try:
            from roteamento import canal_para_persona
            canais = canal_para_persona(canal_nome, stem=mp4.stem)
        except Exception:
            canais = []
    if canais:
        doc["canais"] = canais
    if thumb:
        doc["thumbnail"] = str(thumb)
    if extra:
        doc.update(extra)
    out = mp4.with_name(f"{mp4.stem}.postar.json")
    try:
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[publicar] falha ao escrever postar.json: {e}", flush=True)
        return None
    return str(out)


if __name__ == "__main__":
    # teste rapido
    import tempfile
    demo = Path(tempfile.gettempdir()) / "demo_veo.mp4"
    demo.write_bytes(b"x")
    p = gerar_postar_json(str(demo), "Dicas Financeiras", "Educacao Financeira",
                          "O banco esconde esse erro que destroi seu salario",
                          cta="Chama no WhatsApp que ta na tela")
    print("postar.json em:", p)
    print(Path(p).read_text(encoding="utf-8"))
