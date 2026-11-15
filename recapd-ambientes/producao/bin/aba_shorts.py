"""Lista a aba Shorts de um canal pela API interna do site (InnerTube), sem yt-dlp e sem conta.

Ideia do misterzaidxpy/tubescrape (MIT), reescrita só com requests e COM paginação (o tubescrape só lê a 1ª página).
Medido 15/11: 0,8-2,1 s por canal contra 4,7-10,5 s do yt-dlp, mesmos ids, já com as views. Leitura pública,
sem cookie de conta (não toca nenhuma conta, então não entra na regra do IP fixo por conta).

Uso: listar("https://www.youtube.com/@canal/shorts", maximo=150, proxy=None) -> [(id, titulo, views)]
Falha (mudança no site, bloqueio) = exceção; quem chama volta para o yt-dlp.
"""
import json
import re
from pathlib import Path

import requests

BROWSE = "https://www.youtube.com/youtubei/v1/browse"
PARAMS_SHORTS = "EgZzaG9ydHPyBgUKA5oBAA%3D%3D"
CLIENTE = {"hl": "en", "gl": "US", "clientName": "WEB", "clientVersion": "2.20260227.01.00", "platform": "DESKTOP"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
IDS = Path(__file__).resolve().parent.parent / "workspace" / "cache" / "discover_canal" / "_ids_canais.json"
_RX_UC = re.compile(r'"(?:channelId|externalId|browseId)":"(UC[\w-]{22})"')
_RX_CANON = re.compile(r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"')


def _views(txt):
    """'2.6K views' -> 2600; '1.2M views' -> 1200000; '523 views' -> 523; '' -> 0."""
    m = re.search(r"([\d.,]+)\s*([KMB]?)", (txt or "").replace(",", ""), re.I)
    if not m:
        return 0
    try:
        n = float(m.group(1))
    except ValueError:
        return 0
    return int(n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2).upper()])


def _sessao(proxy):
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    s.cookies.set("CONSENT", "YES+", domain=".youtube.com")
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


def canal_id(url, s, timeout=20):
    m = re.search(r"/channel/(UC[\w-]{22})", url)
    if m:
        return m.group(1)
    base = re.sub(r"/(shorts|videos|featured|streams)/?$", "", url.rstrip("/"))
    try:
        memo = json.loads(IDS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        memo = {}
    if base in memo:
        return memo[base]
    html = s.get(base, timeout=timeout).text
    m = _RX_CANON.search(html) or _RX_UC.search(html)
    if not m:
        raise RuntimeError(f"id do canal não achado em {base}")
    memo[base] = m.group(1)
    try:
        IDS.parent.mkdir(parents=True, exist_ok=True)
        IDS.write_text(json.dumps(memo, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return m.group(1)


def _varrer(no, itens, cont, grade=False):
    """Acha os shortsLockupViewModel e o token da próxima página em qualquer nível do JSON."""
    if isinstance(no, dict):
        lk = no.get("shortsLockupViewModel")
        if isinstance(lk, dict):
            ep = ((lk.get("onTap") or {}).get("innertubeCommand") or {}).get("reelWatchEndpoint") or {}
            vid = ep.get("videoId")
            ov = lk.get("overlayMetadata") or {}
            if vid:
                itens.append((vid, ((ov.get("primaryText") or {}).get("content") or "").strip(),
                              _views((ov.get("secondaryText") or {}).get("content"))))
            return
        ci = no.get("continuationItemRenderer")
        if isinstance(ci, dict):
            tok = ((ci.get("continuationEndpoint") or {}).get("continuationCommand") or {}).get("token")
            if tok and grade:  # só o da grade de Shorts (o painel de comentários também tem um)
                cont.append(tok)
            return
        for k, v in no.items():
            _varrer(v, itens, cont, grade or k in ("richGridRenderer", "appendContinuationItemsAction"))
    elif isinstance(no, list):
        for v in no:
            _varrer(v, itens, cont, grade)


def listar(url, maximo=150, proxy=None, timeout=20):
    s = _sessao(proxy)
    uc = canal_id(url, s, timeout)
    corpo = {"context": {"client": CLIENTE}, "browseId": uc, "params": PARAMS_SHORTS}
    vistos, saida = set(), []
    for _pag in range(40):
        r = s.post(BROWSE, params={"prettyPrint": "false"}, json=corpo, timeout=timeout)
        r.raise_for_status()
        itens, cont = [], []
        _varrer(r.json(), itens, cont)
        for it in itens:
            if it[0] not in vistos:
                vistos.add(it[0])
                saida.append(it)
        if (maximo and len(saida) >= maximo) or not cont or not itens:
            break
        corpo = {"context": {"client": CLIENTE}, "continuation": cont[-1]}
    if not saida:
        raise RuntimeError(f"aba Shorts vazia/irreconhecível em {url}")
    return saida[:maximo] if maximo else saida


if __name__ == "__main__":
    import sys
    import time
    for u in sys.argv[1:]:
        t = time.time()
        L = listar(u, 150)
        print(f"{u}: {len(L)} em {time.time() - t:.1f} s; 1º {L[0]}; com views {sum(1 for x in L if x[2])}")
