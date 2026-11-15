"""vigia_cruzamento.py — procura no pool do Kaggle o que liga contas entre si (10/11/2026, depois do 2º banimento).
SÓ LÊ ARQUIVOS: não fala com Kaggle, Google, Webshare nem navegador. Roda 1x/dia (tarefa VigiaCruzamentoKaggle).

O que procura (cada item = motivo real de um dos banimentos):
  1. saída (webshare_ip -N / proxy_fixo rnprmtfo-N) usada por 2 contas — 2 contas pelo mesmo IP (02/11)
  2. saída de conta VIVA que já foi de conta BANIDA — o Kaggle liga pelo histórico do IP (09/11, IPs 1/4/5/6)
  3. ip_real repetido entre contas (a Webshare troca o IP por trás do mesmo N)
  4. conta Google do pool usada no Flow nos últimos 7 dias — a mesma conta em vários IPs de casa (09/11, família verse)
Achou algo = aviso no Telegram (video-fila\\avisos.py, origem "kaggle-gerente") e relatório em VIGIA_CRUZAMENTO.md.

    python vigia_cruzamento.py
"""
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

POOL = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
FLOW = Path(r"D:\flow-imagens")
SAIDA = Path(__file__).with_name("VIGIA_CRUZAMENTO.md")


def chave(c):
    if c.get("proxy_fixo"):
        return "px-" + c["proxy_fixo"].split("//", 1)[-1].split("@", 1)[0].split(":", 1)[0]
    if c.get("webshare_ip"):
        return f"ws-{c['webshare_ip']}"
    return None  # VPS: saída compartilhada de propósito, revezada pela _guarda_ip da central


def flow_7d():
    arq = next(FLOW.rglob("geracoes.jsonl"), None)
    if not arq:
        return {}
    usos, lim = defaultdict(int), time.time() - 7 * 86400
    for linha in arq.read_text(encoding="utf-8", errors="ignore").splitlines()[-20000:]:
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        q = str(d.get("quando") or "")
        try:
            t = datetime.fromisoformat(q[:19]).timestamp()
        except ValueError:
            t = time.time()
        if t >= lim and d.get("conta"):
            usos[str(d["conta"]).lower()] += 1
    return usos


def main():
    contas = json.loads(POOL.read_text(encoding="utf-8"))["contas"]
    vivas = [c for c in contas if not c.get("banida") and c.get("ativa", True) is not False]
    banidas = [c for c in contas if c.get("banida")]
    achados = []
    por_saida = defaultdict(list)
    for c in vivas:
        k = chave(c)
        if k:
            por_saida[k].append(c["username"])
    for k, us in por_saida.items():
        if len(us) > 1:
            achados.append(f"MESMA SAÍDA {k}: {', '.join(us)}")
    queimadas = {chave(c): c["username"] for c in banidas if chave(c)}
    for c in vivas:
        k = chave(c)
        if k and k in queimadas:
            achados.append(f"IP QUEIMADO: {c['username']} usa {k}, que foi da banida {queimadas[k]}")
    por_ip = defaultdict(list)
    for c in contas:
        if c.get("ip_real"):
            por_ip[c["ip_real"]].append(c["username"] + (" (banida)" if c.get("banida") else ""))
    for ip, us in por_ip.items():
        if len(us) > 1:
            achados.append(f"IP REAL REPETIDO {ip}: {', '.join(us)}")
    usos = flow_7d()
    for c in vivas:
        s = str(c.get("cofre") or "").split("@")[0].lower()
        if s and usos.get(s):
            achados.append(f"NO FLOW: {c['username']} ({s}) gerou {usos[s]} imagens em 7 dias por IPs de casa")
    # 5. (14/11, 3º banimento) canal de conta VIVA do Kaggle que subiu por HTTP SEM passar pelo IP fixo — o upload HTTP
    #    saía de casa. Desde 14/11 23h30 cada envio dessas contas grava "HTTP pelo IP fixo dela" antes do "subiu por HTTP".
    try:
        mapa = json.loads(Path(r"D:\gemini-argo\youtube_canais_http.json").read_text("utf-8")) \
            if Path(r"D:\gemini-argo\youtube_canais_http.json").exists() else {}
    except (OSError, ValueError):
        mapa = {}
    try:
        sys.path.append(r"D:\gemini-argo")
        import youtube_http as _yh
        slug_email = {s: str(v.get("email") or "").lower() for s, v in _yh._mapa().items()}
    except Exception:  # noqa: BLE001
        slug_email = {}
    viv_mail = {str(c.get("cofre") or "").lower(): c["username"] for c in vivas}
    try:
        linhas = Path(r"D:\postador-de-videos\logs\youtube_http.log").read_text("utf-8", "ignore").splitlines()[-4000:]
    except OSError:
        linhas = []
    hoje, ontem = datetime.now().strftime("%d/%m"), datetime.fromtimestamp(time.time() - 86400).strftime("%d/%m")
    fixo = set()
    sem_fixo = defaultdict(int)
    for ln in linhas:
        if not ln.startswith((f"[{hoje}", f"[{ontem}")):
            continue
        s = ln.split("] ", 1)[-1].split(":", 1)[0]
        if "HTTP pelo IP fixo dela" in ln:
            fixo.add(s)
        elif "subiu por HTTP" in ln and viv_mail.get(slug_email.get(s, "")) and s not in fixo:
            sem_fixo[s] += 1
    for s, n in sem_fixo.items():
        achados.append(f"HTTP DE CASA: canal {s} (conta viva do Kaggle {viv_mail[slug_email[s]]}) subiu {n} vídeo(s) "
                       f"por HTTP sem o IP fixo em 48 h")
    texto = (f"# Vigia de cruzamento do Kaggle — {datetime.now():%d/%m/%Y %H:%M}\n\n"
             f"{len(vivas)} contas vivas, {len(banidas)} banidas. Só leitura de arquivos.\n\n"
             + ("\n".join(f"- {a}" for a in achados) if achados else "- nada encontrado") + "\n")
    SAIDA.write_text(texto, encoding="utf-8")
    print(texto, flush=True)
    graves = achados  # 12/11: NO FLOW também avisa — foi o que baniu a animescomia (62 imagens/7d pela casa)
    if graves:
        try:
            subprocess.run([sys.executable, r"D:\video-fila\avisos.py", "kaggle-gerente",
                            "Cruzamento no pool do Kaggle (risco de banimento):\n" + "\n".join(graves[:8])],
                           timeout=60, creationflags=0x08000000)
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()
