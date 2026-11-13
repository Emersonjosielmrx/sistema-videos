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
import threading
import urllib.request
from pathlib import Path

PROXIES_FILE = Path(__file__).resolve().parent.parent / "secrets" / "proxies.txt"

_lock = threading.RLock()
_pool = None
_pool_mtime = 0.0
_idx = 0


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


def has_proxy():
    return bool(_load())


def _tag(proxy):
    """Usuário do proxy (sem senha) pra log — nunca vaza credencial."""
    try:
        return proxy.split("//", 1)[-1].split(":", 1)[0]
    except Exception:
        return "?"


def current():
    """Proxy atual. RAISE se o pool está vazio (regra: nunca sem proxy)."""
    pool = _load()
    if not pool:
        raise RuntimeError(
            "proxy_router: pool VAZIO — regra proíbe chamada sem proxy. "
            "Preencha secrets/proxies.txt."
        )
    with _lock:
        return pool[_idx % len(pool)]


def rotate():
    """Avança pro próximo proxy (chamar quando o atual falha). Retorna o novo."""
    global _idx
    pool = _load()
    if not pool:
        raise RuntimeError("proxy_router: pool VAZIO — chamada sem proxy proibida.")
    with _lock:
        _idx = (_idx + 1) % len(pool)
        return pool[_idx]


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
    # Autoteste: valida quantos proxies do pool respondem (via ipv4.webshare.io).
    import sys
    pool = _load()
    print(f"pool: {len(pool)} proxies em {PROXIES_FILE}")
    ok = 0
    for p in pool:
        try:
            op = build_opener(p)
            ip = op.open("https://ipv4.webshare.io/", timeout=15).read().decode().strip()
            print(f"  ✓ {_tag(p)} → {ip}")
            ok += 1
        except Exception as e:
            print(f"  ✗ {_tag(p)}: {str(e)[:60]}")
    print(f"\n{ok}/{len(pool)} proxies OK")
    sys.exit(0 if ok else 1)
