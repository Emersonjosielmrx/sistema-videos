# -*- coding: utf-8 -*-
"""legenda_empresa.py — legenda de Instagram/TikTok das contas de EMPRESA e de PRODUTO (25/10/2026).

Pedido do dono (25/10): "máximo de comentários, visualizações e pessoas procurando os produtos". Dado real que motivou
(@msenergycap, 21–24/10): 0 comentário em 10 posts, 0 clique no link em 7 dias; a legenda abria com uma frase morna,
nunca perguntava nada e nunca citava as cidades onde estão os seguidores. Agora, por conta (config\\empresas_instagram.json):

  1a linha  gancho com a PALAVRA BUSCADA + o LUGAR (é o que aparece antes do "mais" e o que a busca do Instagram lê)
  corpo     o texto útil que o roteiro/carrossel já gera
  pergunta  fácil de responder nos comentários (comentário = alcance)
  chamada   "Comente PALAVRA que a gente te chama no Direct" — o vigia (ms-energy\\bin\\vigia_clientes_insta.py) responde
            quem comentar a palavra com o Direct (resposta privada da API, sem bot de comentário)
  contato   WhatsApp/link no perfil, local e serviços
  hashtags  5 (3 fixas da conta + 2 da pauta ou rodízio), não 8–9 genéricas

Uso: from legenda_empresa import montar, relegendar, tem_palavra
"""
import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

CONFIG = Path(r"D:\postador-de-videos\config\empresas_instagram.json")
VERSAO = 2  # meta["legenda_versao"]: 2 = legenda nova (a antiga é refeita na hora de postar por relegendar())


def _norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def carregar(conta):
    """Config da conta (resolve 'igual_a'); {} se a conta não está cadastrada."""
    try:
        contas = json.loads(CONFIG.read_text("utf-8")).get("contas", {})
    except (OSError, ValueError):
        return {}
    c = contas.get(conta.lstrip("@").lower()) or {}
    if c.get("igual_a"):
        c = {**contas.get(c["igual_a"], {}), **{k: v for k, v in c.items() if k != "igual_a"}}
    return c


def hashtags(conta, pauta=None):
    """5 hashtags: as fixas da conta + as da pauta, ou 2 extras em rodízio (muda com o dia: legenda igual = spam)."""
    c = carregar(conta)
    tags = list(c.get("hashtags_fixas", []))
    da_pauta = (c.get("hashtags_pauta") or {}).get(pauta or "", [])
    extras = list(c.get("hashtags_extra", []))
    if extras:
        semente = int(hashlib.md5(f"{pauta}{date.today()}".encode()).hexdigest(), 16)
        extras = extras[semente % len(extras):] + extras[:semente % len(extras)]
    for t in da_pauta + extras:
        if len(tags) >= 5:
            break
        if t not in tags:
            tags.append(t)
    return tags[:5]


def _corpo_limpo(corpo, primeira):
    linhas = [l.rstrip() for l in (corpo or "").strip().split("\n")]
    linhas = [l for l in linhas if l and not l.lstrip().startswith("#")]
    # o corpo do LLM às vezes repete o gancho na 1a linha: não dizer duas vezes
    if linhas and primeira and len(set(_norm(linhas[0]).split()) & set(_norm(primeira).split())) >= \
            0.7 * max(1, len(set(_norm(linhas[0]).split()))):
        linhas = linhas[1:]
    return "\n".join(linhas)


def montar(conta, corpo, pauta=None, primeira_linha=None, pergunta=None):
    """(legenda_insta, legenda_tiktok, hashtags). Conta sem cadastro: devolve o corpo + hashtags da pauta, sem inventar."""
    c = carregar(conta)
    tags = hashtags(conta, pauta)
    if not c:
        txt = (corpo or "").strip()
        return txt, txt, tags
    primeira = (primeira_linha or (c.get("primeira_linha") or {}).get(pauta or "") or "").strip()
    perg = (pergunta or (c.get("pergunta") or {}).get(pauta or "") or c.get("pergunta_padrao") or "").strip()
    meio = _corpo_limpo(corpo, primeira)
    blocos = [b for b in (primeira, meio) if b]
    # "comente PALAVRA que a gente te chama no Direct" SO em conta com vigia ligado: sem ele a promessa ficaria sem
    # ninguem cumprir (ex.: msenergysolar.pa, que posta pelo navegador)
    chamada = c.get("chamada_comentario", "") if c.get("vigia") else ""
    engaj = "\n".join(x for x in (perg, chamada) if x)
    if engaj:
        blocos.append(engaj)
    rodape = "\n".join(x for x in (c.get("linha_contato"), c.get("local_linha"), c.get("linha_servicos")) if x)
    if rodape:
        blocos.append(rodape)
    blocos.append(" ".join(tags))
    insta = "\n\n".join(blocos)[:2200]
    # TikTok: 1 linha (o editor de lá não guarda quebra) e sem "comente PALAVRA" (lá não há Direct automático)
    primeira_corpo = meio.split("\n")[0] if meio else ""
    tiktok = " ".join(x for x in (primeira, primeira_corpo, perg, c.get("contato_tiktok") or c.get("linha_contato"),
                                  " ".join(tags)) if x)
    return insta, tiktok[:2000], tags


def relegendar(meta, conta):
    """Refaz a legenda de um vídeo/carrossel já GERADO no formato antigo (texto + rodapé fixo), na hora de postar.
    Mexe em meta (legenda_insta, legenda_tiktok, hashtags, legenda_versao). True se refez."""
    c = carregar(conta)
    if meta.get("legenda_versao") == VERSAO or not c:
        return False
    antiga = meta.get("legenda_insta") or ""
    if (c.get("chamada_comentario") and c["chamada_comentario"] in antiga) or \
            (c.get("pergunta_padrao") and c["pergunta_padrao"] in antiga):  # ja e a nova (sem a marca de versao)
        meta["legenda_versao"] = VERSAO
        return False
    corpo = re.split(r"\n\n(?:📲|🛒|🔗)", antiga)[0] if antiga else ""
    if not corpo.strip():
        return False
    meta["legenda_insta"], meta["legenda_tiktok"], meta["hashtags"] = montar(conta, corpo, meta.get("pauta"))
    meta["legenda_versao"] = VERSAO
    return True


def tem_palavra(conta, texto):
    """O comentário traz a palavra da chamada ("SOL", "AÇAÍ"...)? Sem acento e sem caixa; palavra inteira."""
    p = _norm(carregar(conta).get("palavra_comentario", "")).strip()
    return bool(p) and re.search(rf"\b{re.escape(p)}\b", _norm(texto)) is not None


if __name__ == "__main__":
    import sys
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    conta = sys.argv[1] if len(sys.argv) > 1 else "msenergycap"
    pauta = sys.argv[2] if len(sys.argv) > 2 else "chuva"
    ins, tk, tg = montar(conta, "Mesmo em dia nublado as placas geram energia.\nO projeto considera o ano todo.", pauta)
    print(ins, "\n\n--- TikTok ---\n", tk, "\n\n", len(ins), "caracteres")
