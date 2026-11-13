"""collabs.py — PAREAMENTO de collabs entre os nossos canais/contas (dona 29/10: "todos os vídeos a partir de hoje têm
que ser collabs em todos os projetos, a não ser que não seja benéfico; a ideia é fazer com que os inscritos de um canal
se inscrevam nos outros").

Para cada vídeo que vai sair, `parceiro(plataforma, conta)` devolve a conta NOSSA que entra como coautora (Instagram:
"Convidar colaborador"; YouTube: colaboração do Studio), em rodízio, para cada conta aparecer para o público das outras.

Regras do pareamento (29/10, dona: "transfusão de público: o máximo de pessoas se inscrevendo de um no outro; um canal
publica com todos, depois o outro também, cada um na sua rotação, tirando os estrangeiros"):
  1. A RODA é TODAS as contas da MESMA LÍNGUA (Instagram: as 25 em pt; YouTube: os 22 canais pt). Cada conta passa por
     todas as outras antes de repetir alguma.
  2. ORDEM da rotação: primeiro as do mesmo nicho (público mais parecido), depois as demais; cada conta começa num
     vizinho diferente da roda, para não irem todas para o mesmo parceiro no mesmo dia.
  3. Sem collab ("não benéfico"): língua com 1 canal só (os inovare_* em en/fr/hi/id/it/ru/th/vi — gente de outra língua
     não segue vídeo em português) e cliente real com público próprio (MS Energy, `SEM_COLLAB`).
Estado do rodízio: estado\\collabs.json. O ENVIO do convite/aceite fica no postador de cada rede (a fazer: captura do
pedido de coautor no Instagram e da colaboração no YouTube Studio).

    python collabs.py mapa        # imprime os grupos e o próximo parceiro de cada conta
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "collabs.json"
CANAIS = Path(r"D:\postador-de-videos\config\canais.json")

# Instagram: grupos de público (contas da casa em marcas_instagram.json / reuso_plataformas.json)
GRUPOS_IG = {
    "produtos_b2b": ["inovarecom.ia", "futebolcom.ia2", "sintetizerisada", "disparoemmassa.ia", "followupia.ia",
                     "vpsblindada.ia", "fabricademarketing.ia", "crmchatwoot.ia", "mentoriasia.ia", "landingpageia.ia",
                     "gestaodegrupos.ia", "agentesdeia.ia", "superchatia.ia", "inovareagenda", "inovareclone",
                     "inovarecrm", "inovaresites", "vitrineia_inovare"],
    "ia_negocio_financas": ["_lucrocomia_", "iapro.mentoria", "jornalcomia"],
    "curiosidades_entretenimento": ["canalhistoriacomia", "fakenews.ia4", "recenas.ia", "videocassetadascom.ia"],
}
# YouTube: grupos por nicho (canais.json); a língua entra como filtro
GRUPOS_YT = {
    "anime_manhwa": {"anime", "manhwa", "dorama", "jogos"},
    "curiosidades": {"fatos", "curiosidades", "misterios", "historia_mitologia", "animais", "tecnologia"},
    "filmes_esportes": {"filme_sem_voz", "esportes"},
    "financas": {"financas"},
}
# não é benéfico (dona: "a não ser que não seja benéfico para aquele vídeo"): cliente real com público próprio
SEM_COLLAB = {"msenergysolar.pa", "msenergycap"}


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def _grupo_yt(c):
    nicho = str(c.get("nicho") or "").lower()
    for g, chaves in GRUPOS_YT.items():
        if nicho in chaves:
            return g
    if any(p in nicho for p in ("anime", "manhwa", "manhua", "donghua", "isekai")):
        return "anime_manhwa"  # nichos longos dos canais inovare_* (temas de anime em outras línguas)
    if c.get("dono") == "hipercool":
        return "anime_manhwa"  # canal de manhwa sem nicho escrito
    return None


def nichos(plataforma):
    """{conta: grupo de nicho} — só para a ORDEM da roda (afinidade primeiro), não limita com quem faz collab."""
    if plataforma == "instagram":
        return {c: g for g, cs in GRUPOS_IG.items() for c in cs}
    return {slug: _grupo_yt(c or {}) or "outros" for slug, c in (_ler(CANAIS, {}).get("canais") or {}).items()}


def grupos(plataforma):
    """{língua: [contas]} — 29/10 (dona: "a ideia é ter o máximo de pessoas se inscrevendo de um no outro... um canal
    publica com todos, aí o outro também, cada um na sua rotação, tirando os estrangeiros"): a roda é TODOS os canais
    da mesma língua, não só o nicho. Língua com 1 canal só (os inovare_* estrangeiros) fica sem collab."""
    if plataforma == "instagram":  # todas as contas de Instagram da casa são em português
        return {"pt": [c for cs in GRUPOS_IG.values() for c in cs if c not in SEM_COLLAB]}
    out = {}
    for slug, c in (_ler(CANAIS, {}).get("canais") or {}).items():
        if (c or {}).get("navegador") and slug not in SEM_COLLAB:
            out.setdefault(c.get("idioma") or "pt", []).append(slug)
    return out


TG_ESTADO = Path(r"D:\postador-de-videos\config\telegram_estado.json")


VIEWS_PUB = BASE / "estado" / "views_canais_publicas.json"


def _num(txt):
    t = txt.strip().lower().replace(" ", " ")
    mult = 1_000_000 if t.endswith(" mi") else 1000 if t.endswith(" mil") else 1
    t = t.replace(" mi", "").replace(" mil", "")
    t = t.replace(".", "").replace(",", ".") if mult == 1 else t.replace(",", ".")
    try:
        return int(float(t) * mult)
    except ValueError:
        return 0


def _views_publicas(channel_id):
    """Soma das views dos vídeos e Shorts que a página pública do canal mostra (canal sem token da API: o total do
    canal não vem no HTML). Serve pra ORDENAR a roda, não é o número exato."""
    import re
    import urllib.request
    total = 0
    for aba in ("videos", "shorts"):
        req = urllib.request.Request(f"https://www.youtube.com/channel/{channel_id}/{aba}", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
            "Accept-Language": "pt-BR"})
        try:
            s = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        vistos = {}
        for m in re.finditer(r'"videoId":"([\w-]{11})".{0,4000}?"(?:accessibilityLabel|accessibilityText)":"(?:[^"]*?, )?'
                             r'([\d.,]+(?: mil| mi)?) visualiza', s, re.S):
            vistos.setdefault(m.group(1), _num(m.group(2)))
        total += sum(vistos.values())
    return total


def views_canais():
    """{slug: views do canal}. 02/11: com token da API = total do canal (base do dia do monitor do Telegram); sem token
    = soma pública dos vídeos (estado\\views_canais_publicas.json, relida a cada 12 h, 2 s entre canais)."""
    v = {s: int((x or {}).get("views") or 0)
         for s, x in ((_ler(TG_ESTADO, {}).get("base_dia") or {}).get("canais") or {}).items()}
    pub = _ler(VIEWS_PUB, {})
    agora = datetime.now()
    mudou = False
    for slug, c in (_ler(CANAIS, {}).get("canais") or {}).items():
        if v.get(slug) or not (c or {}).get("navegador") or not c.get("channel_id"):
            continue
        p = pub.get(slug) or {}
        if not p.get("em") or agora - datetime.fromisoformat(p["em"]) > timedelta(hours=12):
            import time
            time.sleep(2)
            pub[slug] = p = {"views": _views_publicas(c["channel_id"]), "em": agora.isoformat(timespec="minutes")}
            mudou = True
        v[slug] = p["views"]
    if mudou:
        VIEWS_PUB.parent.mkdir(parents=True, exist_ok=True)
        VIEWS_PUB.write_text(json.dumps(pub, ensure_ascii=False, indent=1), "utf-8")
    return v


def _ordem(plataforma, conta, roda):
    """Ordem da rotação desta conta.
    YouTube (02/11 dona: "a ordem da rotação deve ser por ordem de visualizações dos canais, sempre: canais com mais
    views primeiro, assim todos começam se beneficiando deles"): todos os outros da língua, do que tem MAIS views totais
    pro que tem menos (empate/sem leitura: mesmo nicho primeiro). Instagram (sem views lidas): mesmo nicho primeiro,
    começando no vizinho da roda (cada conta começa num parceiro diferente)."""
    n = nichos(plataforma)
    i = roda.index(conta)
    vizinhos = [roda[(i + k) % len(roda)] for k in range(1, len(roda))]
    if plataforma == "youtube":
        v = views_canais()
        return sorted(vizinhos, key=lambda c: (-v.get(c, 0), n.get(c) != n.get(conta), vizinhos.index(c)))
    return [c for c in vizinhos if n.get(c) == n.get(conta)] + [c for c in vizinhos if n.get(c) != n.get(conta)]


def parceiro(plataforma, conta, registrar=True):
    """Conta nossa para entrar como coautora no próximo vídeo de `conta`, ou None (sem collab benéfica). Rodízio: o da
    ordem que ainda não foi usado; quando todos foram, o usado há mais tempo (a roda recomeça)."""
    if conta in SEM_COLLAB:
        return None
    roda = next((cs for cs in grupos(plataforma).values() if conta in cs), None)
    if not roda or len(roda) < 2:
        return None
    ordem = _ordem(plataforma, conta, roda)
    est = _ler(EST, {})
    usado = est.setdefault(plataforma, {}).setdefault(conta, {})
    escolhido = min(ordem, key=lambda c: (usado.get(c, ""), ordem.index(c)))
    if registrar:
        usado[escolhido] = datetime.now().isoformat(timespec="seconds")
        EST.parent.mkdir(parents=True, exist_ok=True)
        EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
    return escolhido


def mapa():
    for plat in ("instagram", "youtube"):
        print(f"== {plat}")
        sozinhos = []
        for g, cs in grupos(plat).items():
            if len(cs) < 2:
                sozinhos += cs
                continue
            print(f"  língua {g}: {len(cs)} contas, cada uma passa por todas as outras {len(cs) - 1} na rotação")
            for c in cs[:3]:
                print(f"    {c}: {' -> '.join(_ordem(plat, c, cs)[:6])} -> ...")
        if sozinhos:
            print(f"  sem collab (único canal na língua dele): {', '.join(sozinhos)}")
        print(f"  sem collab (cliente com público próprio): {', '.join(sorted(SEM_COLLAB))}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if (sys.argv[1:] or ["mapa"])[0] == "mapa":
        mapa()
