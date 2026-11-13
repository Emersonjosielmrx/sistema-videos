# -*- coding: utf-8 -*-
# COMUM — fonte única: D:\hipercool-materiais\comum\groq_api.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir groq_api.py --de <projeto>
"""groq_api.py — Whisper large-v3 do Groq com rodízio de chaves, sempre pelo proxy Webshare.

Dono (15/10): toda chamada ao Groq sai pelo proxy Webshare. Sem proxy disponível o pedido NÃO vai direto: devolve None.
Proxies e estado (cooldown) são os do postador, comuns a todos os projetos. 18/10: versão única (hipercool + manhwa-react).
Chaves: D:\\postador-de-videos\\secrets\\groq_keys.json (só status "ok"; a que der 401 vira "invalida").

  python bin/groq_api.py --testar     # status de cada chave pelo proxy (não mostra a chave)
"""
import datetime
import json
import os
import time
from pathlib import Path

import requests

try:
    from hp_common import log  # hipercool
except ImportError:
    from .common import log  # manhwa-react (pacote mr)

ARQ_CHAVES = [Path(os.environ.get("HIPER_GROQ_KEYS", r"D:\postador-de-videos\secrets\groq_keys.json"))]
ARQ_PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")
PROXY_ESTADO_FILE = Path(r"D:\postador-de-videos\secrets\proxies_estado.json")
URL = "https://api.groq.com/openai/v1"
PROXY_TENTATIVAS = 6  # proxies tentados por chave antes de passar pra próxima
_vez = 0  # rodízio: cada pedido começa numa chave diferente (espalha a cota)

# Estado compartilhado de proxy (arquivo JSON, mesmo do hipercool)
_proxy_idx = 0
_proxy_list = []


def _load_proxies():
    """Carrega lista de proxies do arquivo, começando em posição aleatória."""
    global _proxy_list, _proxy_idx
    if not ARQ_PROXIES.exists():
        return
    try:
        import random
        linhas = ARQ_PROXIES.read_text(encoding="utf-8").strip().split("\n")
        _proxy_list = []
        # 11/11 (postagem dos parceiros caiu 06:56 'groq: proxy .webshare.io:80 fora'): pula as contas grátis que a
        # tarefa WebshareSaude marcou 402 (sem banda) em D:\video-fila\estado\webshare.json. WEBSHARE_PULA_402=0 desliga.
        sem_banda = set()
        if os.environ.get("WEBSHARE_PULA_402", "1") != "0":
            try:
                j = json.loads(Path(r"D:\video-fila\estado\webshare.json").read_text(encoding="utf-8"))
                sem_banda = {c["conta"] for c in j.get("contas", []) if "402" in str(c.get("estado"))}
            except (OSError, ValueError, KeyError):
                sem_banda = set()
        for linha in linhas:
            linha = linha.strip()
            if linha and linha.split("//", 1)[-1].split("-rotate", 1)[0] in sem_banda:
                continue
            if linha and not linha.startswith("#"):
                # Não adiciona http:// se já tem o prefixo
                _proxy_list.append(linha if linha.startswith("http") else f"http://{linha}")
        if _proxy_list:
            _proxy_idx = random.randrange(len(_proxy_list))
    except (OSError, ValueError):
        pass


def _conta_proxy(proxy):
    """Extrai identificador único do proxy (user@host:port)."""
    import re
    m = re.search(r"//([^/]+)", proxy or "")
    return m.group(1) if m else proxy


def _mascara(proxy):
    """Mascara proxy para log."""
    if not proxy:
        return "-"
    return proxy[-15:] if len(proxy) > 15 else proxy


def _estado_proxies():
    """Lê estado compartilhado de proxies (cooldowns)."""
    try:
        if PROXY_ESTADO_FILE.exists():
            return json.loads(PROXY_ESTADO_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {}


def _gravar_estado_proxies(est):
    """Grava estado de proxies (compartilhado entre projetos)."""
    tmp = PROXY_ESTADO_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, PROXY_ESTADO_FILE)
    except OSError:
        pass


def _proxy_falhou(proxy, motivo):
    """Tira proxy da rotação: 1h (1ª falha) ou 24h (falhas seguidas)."""
    est = _estado_proxies()
    e = est.get(_conta_proxy(proxy), {})
    falhas = e.get("falhas", 0) + 1
    volta_ts = time.time() + (3600 if falhas == 1 else 86400)
    est[_conta_proxy(proxy)] = {
        "falhas": falhas,
        "motivo": str(motivo)[:120],
        "desde": e.get("desde") or time.strftime("%Y-%m-%d %H:%M"),
        "testar_de_novo": time.strftime("%Y-%m-%d %H:%M", time.localtime(volta_ts)),
        "_ts": volta_ts
    }
    _gravar_estado_proxies(est)
    log(f"  groq: proxy {_mascara(proxy)} fora ({str(motivo)[:70]}) -> testa de novo {est[_conta_proxy(proxy)]['testar_de_novo']}")


def _proxy_ok(proxy):
    """Remove proxy do estado de fora (voltou a funcionar)."""
    est = _estado_proxies()
    if est.pop(_conta_proxy(proxy), None) is not None:
        _gravar_estado_proxies(est)
        log(f"  groq: proxy {_mascara(proxy)} voltou a funcionar")


def _get_next_proxy():
    """Próximo proxy da rotação, pulando os que estão em cooldown."""
    global _proxy_idx
    if not _proxy_list:
        _load_proxies()
    if not _proxy_list:
        return None
    fora, agora = _estado_proxies(), time.time()
    for _ in range(len(_proxy_list)):
        proxy = _proxy_list[_proxy_idx % len(_proxy_list)]
        _proxy_idx += 1
        if fora.get(_conta_proxy(proxy), {}).get("_ts", 0) <= agora:
            return proxy
    return None  # todos em cooldown


def chaves():
    """[(arquivo, id, token)] das chaves com status ok; GROQ_API_KEY do ambiente vem primeiro."""
    out = [(None, "env", os.environ["GROQ_API_KEY"])] if os.environ.get("GROQ_API_KEY") else []
    vistas = {t for _a, _i, t in out}
    for arq in ARQ_CHAVES:
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for k, it in enumerate(dados if isinstance(dados, list) else dados.get("keys", [])):
            tok = it.get("token") if isinstance(it, dict) else it
            ok = not isinstance(it, dict) or it.get("status", "ok") == "ok"
            if isinstance(tok, str) and tok.startswith("gsk_") and ok and tok not in vistas:
                vistas.add(tok)
                out.append((arq, str(it.get("id", k + 1)) if isinstance(it, dict) else str(k + 1), tok))
    return out


def _marcar_invalida(arq, id_, motivo):
    """Chave recusada pelo Groq (401) sai do rodízio de todos os projetos (status "invalida" no arquivo)."""
    if arq is None:
        return
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        for it in dados:
            if isinstance(it, dict) and str(it.get("id")) == id_:
                it["status"] = "invalida"
                it["note"] = f"{motivo} em {datetime.date.today().isoformat()}"
        arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log(f"  groq: chave {id_} recusada ({motivo}) -> marcada como invalida")
    except (OSError, ValueError) as e:
        log(f"  groq: não deu pra marcar a chave {id_} ({str(e)[:80]})")


def _pedido(metodo, caminho, token, arquivo=None, **kw):
    """(status, json, proxy) de um pedido ao Groq por um proxy da rotação.
    status None = nenhum proxy disponível; 0 = todos os proxies tentados falharam."""
    cab = {"Authorization": f"Bearer {token}"}
    for _ in range(PROXY_TENTATIVAS):
        proxy = _get_next_proxy()
        if not proxy:
            log("  groq: nenhum proxy disponível (todos fora/sem banda) — não vai direto")
            return None, None, None
        prox = {"http": proxy, "https": proxy}
        try:
            if arquivo:
                with open(arquivo, "rb") as fh:
                    r = requests.request(metodo, URL + caminho, headers=cab, proxies=prox,
                                         files={"file": (Path(arquivo).name, fh)}, **kw)
            else:
                r = requests.request(metodo, URL + caminho, headers=cab, proxies=prox, **kw)
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout) as e:
            _proxy_falhou(proxy, f"groq: {type(e).__name__}")  # conta da Webshare fora/sem banda
            continue
        except requests.RequestException as e:  # leitura demorou/conexão caiu: tenta outro IP sem culpar a conta
            log(f"  groq: rede ({type(e).__name__}); outro proxy")
            continue
        try:
            j = r.json()
        except ValueError:
            j = None
        if not (isinstance(j, dict) and (r.status_code == 200 or "error" in j)):
            # página que não é da API (Cloudflare barrando o IP de saída): o rotativo sai por outro IP
            log(f"  groq: HTTP {r.status_code} que não veio da API; outro proxy")
            continue
        _proxy_ok(proxy)
        return r.status_code, j, proxy
    return 0, None, None


def transcrever(audio, idioma="pt", palavras=True, timeout=300):
    """JSON verbose do Whisper (segmentos e, com palavras=True, tempo por palavra) ou None."""
    global _vez
    lista = chaves()
    if not lista:
        log("  groq: sem chaves")
        return None
    dados = {"model": "whisper-large-v3", "response_format": "verbose_json", "language": idioma or "pt",
             "temperature": "0"}
    if palavras:
        dados["timestamp_granularities[]"] = ["word", "segment"]
    _vez += 1
    for i in range(len(lista)):
        arq, id_, tok = lista[(_vez + i) % len(lista)]
        st, j, _p = _pedido("POST", "/audio/transcriptions", tok, arquivo=audio, data=dados, timeout=timeout)
        if st is None:
            return None
        if st == 200:
            return j
        msg = ((j or {}).get("error") or {}).get("message", "") if isinstance(j, dict) else ""
        log(f"  groq: chave {id_} -> HTTP {st} {str(msg)[:90]}")
        if st == 401:
            _marcar_invalida(arq, id_, "401")
        elif st not in (0, 403, 429, 503):
            return None  # erro do pedido (arquivo grande demais, formato...): outra chave não resolve
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Groq pelo proxy Webshare")
    ap.add_argument("--testar", action="store_true", help="testa cada chave (lista de modelos) pelo proxy")
    a = ap.parse_args()
    if a.testar:
        for arq, id_, tok in chaves():
            st, _j, proxy = _pedido("GET", "/models", tok, timeout=30)
            print(f"chave {id_}: HTTP {st} via {_mascara(proxy)}")
            if st == 401:
                _marcar_invalida(arq, id_, "401")
