"""webshare_saude.py — estado REAL de cada conta grátis do Webshare (02/11, gerente do Kaggle).

Não temos chave de API das contas (só usuário/senha do proxy), então o saldo em bytes não é legível. O que é real:
um pedido mínimo por conta (~2 KB) pelo proxy rotativo. 200 = tem banda; 402 = banda do mês acabou; 407 = senha
inválida. Também mede o IP de saída. Saída: D:\\video-fila\\estado\\webshare.json (o painel mostra).

Achado 02/11: o vídeo NUNCA passa pela Webshare (o kernel do Kaggle baixa/sobe direto do Drive); a Webshare só leva
os comandos da API do Kaggle das contas com webshare_ip (KB) e falas do edge-tts quando o direto é bloqueado.

    python webshare_saude.py
"""
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")
SAIDA = Path(r"D:\video-fila\estado\webshare.json")
TESTE = "http://ipv4.webshare.io/"


def testar(linha):
    conta = linha.split("//", 1)[-1].split("-rotate", 1)[0]
    proxy = linha if linha.startswith("http") else "http://" + linha
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    try:
        ip = op.open(TESTE, timeout=20).read().decode().strip()[:40]
        return {"conta": conta, "estado": "ok", "ip": ip}
    except urllib.error.HTTPError as e:
        return {"conta": conta, "estado": {402: "sem banda (402)", 407: "senha inválida (407)"}.get(e.code, f"HTTP {e.code}")}
    except Exception as e:  # noqa: BLE001
        return {"conta": conta, "estado": f"falhou: {type(e).__name__}"}


def main():
    linhas = [x.strip() for x in PROXIES.read_text(encoding="utf-8").splitlines() if "-rotate:" in x and not x.startswith("#")]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(testar, linhas))
    ok = sum(1 for r in res if r["estado"] == "ok")
    sem = sum(1 for r in res if "402" in r["estado"])
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "total": len(res), "ok": ok,
                                 "sem_banda": sem, "contas": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    if sys.stdout:
        print(f"{ok} ok · {sem} sem banda · {len(res) - ok - sem} outro erro · de {len(res)} contas")


if __name__ == "__main__":
    main()
