"""proxy_router.py — ROTEADOR DE PROXY COMPARTILHADO (2026-07-04).

Único ponto de verdade do pool de proxy pros 3 engines de voz:
  - gemini_tts.py       (Gemini TTS)
  - elevenlabs_tts.py   (ElevenLabs)
  - edge_tts_engine.py  (edge-tts)

REGRA DE OURO (pedido da usuária): NUNCA fazer chamada SEM proxy.
  - Se um proxy falha (erro de CONEXÃO), o roteador vai pro PRÓXIMO (round-robin).
  - Se o pool está VAZIO, as funções LEVANTAM RuntimeError — o caller NÃO deve
    cair pra conexão direta. Sem proxy = a chamada falha, ponto.

Fonte do pool: secrets/proxies.txt (1 proxy por linha, formato
http://<USUARIO>:<SEGREDO_REMOVIDO>@host:port; linhas com # são comentário). Recarrega sozinho se
o arquivo mudar (mtime).

API:
  has_proxy()        -> bool
  current()          -> str   (proxy atual; RAISE se pool vazio)
  rotate()           -> str   (avança e retorna o próximo; RAISE se vazio)
  proxies_dict(p=None) -> {"http":p,"https":p}  (pro `requests`)
  build_opener(p=None) -> urllib.request.OpenerDirector  (pro urllib)
  run(fn, max_tries=None) -> resultado de fn(proxy_url), tentando cada proxy
"""
import json
import threading
import time
import urllib.request
from pathlib import Path

PROXIES_FILE = Path(__file__).resolve().parent.parent / "secrets" / "proxies.txt"
HEALTH_FILE = Path(__file__).resolve().parent.parent / "secrets" / "proxy_health.json"

# health considerado valido por este tempo (12h). Depois, o pool volta a tratar
# todos como "desconhecidos" (=elegiveis) — porque proxies esgotados VOLTAM.
HEALTH_TTL_S = 12 * 3600

_lock = threading.RLock()
_pool = None            # lista bruta (todos, na ordem do arquivo)
_pool_mtime = 0.0
_idx = 0
_dead = {}              # {proxy_url: epoch_ts_do_teste} — mortos recentes
_dead_loaded = False


def _load():
    """(Re)carrega o pool do proxies.txt se o arquivo mudou. Thread-safe."""
    global _pool, _pool_mtime
    with _lock:
        if not PROXIES_FILE.exists():
            _pool = []
            return _pool
        mt = PROXIES_FILE.stat().st_mtime
        if _pool is None or mt != _pool_mtime:
            lines = PROXIES_FILE.read_text(encoding="utf-8").strip().splitlines()
            _pool = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
            _pool_mtime = mt
        return _pool


def _load_dead():
    """Carrega o mapa de proxies mortos do health-check (se recente)."""
    global _dead, _dead_loaded
    with _lock:
        if _dead_loaded:
            return _dead
        _dead_loaded = True
        _dead = {}
        try:
            if HEALTH_FILE.exists():
                data = json.loads(HEALTH_FILE.read_text(encoding="utf-8"))
                now = time.time()
                for url, info in data.get("dead", {}).items():
                    ts = info.get("ts", 0) if isinstance(info, dict) else info
                    if now - ts < HEALTH_TTL_S:   # so respeita mortos RECENTES
                        _dead[url] = ts
        except Exception:
            _dead = {}
        return _dead


def _live_pool():
    """Pool preferencial: proxies NAO marcados como mortos recentes.
    Se todos estiverem mortos, devolve o pool completo (os mortos VOLTAM —
    melhor tentar do que falhar seco)."""
    pool = _load()
    dead = _load_dead()
    live = [p for p in pool if p not in dead]
    return live if live else pool


def has_proxy():
    return bool(_load())


def _tag(proxy):
    """Usuário do proxy (sem senha) pra log — nunca vaza credencial."""
    try:
        return proxy.split("//", 1)[-1].split(":", 1)[0]
    except Exception:
        return "?"


def current():
    """Proxy atual (do pool de VIVOS). RAISE se o pool está vazio."""
    pool = _live_pool()
    if not pool:
        raise RuntimeError(
            "proxy_router: pool VAZIO — regra proíbe chamada sem proxy. "
            "Preencha secrets/proxies.txt."
        )
    with _lock:
        return pool[_idx % len(pool)]


def rotate():
    """Avança pro próximo proxy VIVO (chamar quando o atual falha)."""
    global _idx
    pool = _live_pool()
    if not pool:
        raise RuntimeError("proxy_router: pool VAZIO — chamada sem proxy proibida.")
    with _lock:
        _idx = (_idx + 1) % len(pool)
        return pool[_idx]


def health_check(timeout=12, test_url="https://ipv4.webshare.io/"):
    """Testa TODOS os proxies do arquivo e persiste vivos/mortos em
    secrets/proxy_health.json. Retorna (n_vivos, n_mortos, detalhes).

    Rode via cron 1x/dia (ou pelo daemon). Os mortos ficam marcados por
    HEALTH_TTL_S (12h) e depois voltam a ser elegiveis — porque proxy
    esgotado (402 de banda) VOLTA no reset mensal."""
    global _dead, _dead_loaded
    pool = _load()
    vivos, mortos, detalhes = [], {}, {}
    now = time.time()
    for p in pool:
        try:
            op = build_opener(p)
            ip = op.open(test_url, timeout=timeout).read().decode().strip()
            if ip and ip.count(".") == 3:
                vivos.append(p)
                detalhes[_tag(p)] = f"OK {ip}"
            else:
                mortos[p] = {"ts": now, "erro": "resposta invalida"}
                detalhes[_tag(p)] = "resposta invalida"
        except Exception as e:
            mortos[p] = {"ts": now, "erro": str(e)[:80]}
            detalhes[_tag(p)] = f"FALHA {str(e)[:50]}"
    try:
        HEALTH_FILE.write_text(json.dumps(
            {"checked_at": now, "n_live": len(vivos), "n_dead": len(mortos),
             "dead": mortos}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    with _lock:
        _dead = {u: v["ts"] for u, v in mortos.items()}
        _dead_loaded = True
    return len(vivos), len(mortos), detalhes


def proxies_dict(proxy=None):
    """Dict pro `requests` (proxies=...). proxy=None usa o atual."""
    p = proxy or current()
    return {"http": p, "https": p}


def build_opener(proxy=None):
    """OpenerDirector do urllib já com o proxy setado. proxy=None usa o atual."""
    p = proxy or current()
    handler = urllib.request.ProxyHandler({"http": p, "https": p})
    return urllib.request.build_opener(handler)


def run(fn, max_tries=None):
    """Executa fn(proxy_url) tentando cada proxy até um dar certo.

    fn deve LEVANTAR exceção em falha de conexão (pra rotacionar) e retornar o
    resultado em sucesso. NUNCA chama sem proxy. Se todos falharem, relança a
    última exceção. max_tries default = tamanho do pool (1 volta completa).
    """
    pool = _load()
    if not pool:
        raise RuntimeError("proxy_router: pool VAZIO — chamada sem proxy proibida.")
    n = max_tries or len(pool)
    last = None
    for _ in range(n):
        p = current()
        try:
            return fn(p)
        except Exception as e:
            last = e
            rotate()
    raise last if last else RuntimeError("proxy_router: todos os proxies falharam")


if __name__ == "__main__":
    # Health-check: testa o pool e persiste vivos/mortos em proxy_health.json.
    import sys
    pool = _load()
    print(f"pool: {len(pool)} proxies em {PROXIES_FILE}")
    print("rodando health-check (pode levar ~1min)...")
    n_live, n_dead, det = health_check()
    for tag, status in det.items():
        mark = "OK" if status.startswith("OK") else "XX"
        print(f"  [{mark}] {tag}: {status}")
    print(f"\n{n_live}/{len(pool)} vivos | {n_dead} mortos (marcados 12h)")
    print(f"health salvo em: {HEALTH_FILE}")
    sys.exit(0 if n_live else 1)
