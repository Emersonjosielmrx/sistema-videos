# D:\sistema\catalogo\motivos.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/motivos.py)
# OBRA etapa 2 - UMA RESPOSTA para "por que nao postou / nao produziu?". Junta, so lendo, TODOS os lugares que seguram
# alguma coisa no sistema (antes eram 8 arquivos espalhados):
#   1 controle.json (controle.py)          2 POSTAGEM_DESLIGADA.json do postador     3 POSTAGEM/FILA_DESLIGADA do hipercool
#   4 parceiro.json "ligado"               5 youtube_navegador.json canal usar=false  6 contas_travadas.json (YouTube)
#   7 fb_fila_estado.json parada_ate       8 reuso_plataformas.json conta pausada    9 Facebook: conta em repouso
# Nao muda nada. Uso:  python motivos.py            (texto)
#                      python motivos.py --json     (para o botao C da barra)
#                      python motivos.py --resumo   (1 linha para a ronda)
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
agora = datetime.now()


def ler(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def mtime(p):
    try:
        return datetime.fromtimestamp(os.path.getmtime(p)).strftime("%d/%m %H:%M")
    except OSError:
        return "?"


itens = []  # (gravidade, onde, o_que, motivo, arquivo)   gravidade: GERAL (para tudo) | PROJETO | CONTA | CANAL


def add(g, onde, oque, motivo, arq):
    itens.append({"nivel": g, "onde": onde, "o_que": oque, "motivo": (motivo or "").strip()[:160], "arquivo": arq})


# 1 controle.json
sys.path.insert(0, r"D:\video-fila")
try:
    import controle
    for p in controle.PROJETOS:
        for e in (("producao",) if p in ("desktop", "celulares") else controle.ETAPAS):
            ok, mot = controle.ligado(p, e)
            if not ok:
                add("GERAL" if p == "tudo" else "PROJETO", p, e + " desligada", mot, r"D:\video-fila\controle.json")
except Exception as ex:  # noqa: BLE001
    add("ERRO", "controle.py", "nao li", str(ex), r"D:\video-fila\controle.py")

# 2 e 3 botoes antigos
for arq, onde, oque in ((r"D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json", "postador (todos)", "POSTAGEM DESLIGADA"),
                        (r"D:\hipercool-videos\config\POSTAGEM_DESLIGADA.json", "hipercool", "postagem desligada"),
                        (r"D:\hipercool-videos\config\FILA_DESLIGADA.json", "hipercool", "fila/producao desligada")):
    if os.path.exists(arq):
        j = ler(arq) or {}
        add("GERAL" if "postador" in onde else "PROJETO", onde, oque, f"{j.get('motivo', '')} (desde {mtime(arq)})", arq)

# 4 parceiro.json
pj = ler(r"D:\recapd-ambientes\producao\config\parceiro.json") or {}
if pj.get("ligado") is False:
    add("PROJETO", "parceiro", "parceiro.json ligado=false", pj.get("motivo", ""), r"D:\recapd-ambientes\producao\config\parceiro.json")

# 5 youtube_navegador usar=false
yn = ler(r"D:\postador-de-videos\config\youtube_navegador.json") or {}
for cid, c in (yn.get("canais") or {}).items():
    if isinstance(c, dict) and c.get("usar") is False:
        add("CANAL", f"YouTube {c.get('nome', cid)}", "usar=false (navegador)", c.get("_mudado_em") or c.get("motivo") or "",
            r"D:\postador-de-videos\config\youtube_navegador.json")

# 6 contas_travadas
ct = ler(r"D:\postador-de-videos\config\contas_travadas.json") or {}
for cid, c in ct.items():
    if cid.startswith("_") or not isinstance(c, dict):
        continue
    ate = c.get("ate") or ""
    if ate:
        try:
            if datetime.fromisoformat(ate[:19]) < agora:
                continue
        except ValueError:
            pass
    add("CANAL", f"YouTube {c.get('nome', cid)}", f"travado: {c.get('tipo', '?')}" + (f" ate {ate[:16]}" if ate else ""),
        c.get("trecho", ""), r"D:\postador-de-videos\config\contas_travadas.json")

# 7 e 9 Facebook
fb = ler(r"D:\postador-de-videos\logs\fb_fila_estado.json") or {}
for conta, c in (fb.get("contas") or {}).items():
    pa = (c or {}).get("parada_ate") or ""
    if pa:
        try:
            if datetime.fromisoformat(pa[:19]) > agora:
                add("CONTA", f"Facebook {conta}", f"em repouso ate {pa[:16].replace('T', ' ')}", (c or {}).get("motivo", ""),
                    r"D:\postador-de-videos\logs\fb_fila_estado.json")
        except ValueError:
            pass

# 8 reuso_plataformas (TikTok/Instagram)
rp = ler(r"D:\postador-de-videos\config\reuso_plataformas.json") or {}
for plat, contas in rp.items():
    if plat.startswith("_") or not isinstance(contas, (dict, list)):
        continue
    lista = contas.items() if isinstance(contas, dict) else enumerate(contas)
    for k, c in lista:
        if isinstance(c, dict) and c.get("pausada"):
            add("CONTA", f"{plat} {c.get('nome') or c.get('conta') or k}", "pausada",
                str(c.get("pausada") if not isinstance(c.get("pausada"), bool) else c.get("motivo", "")),
                r"D:\postador-de-videos\config\reuso_plataformas.json")

ordem = {"ERRO": 0, "GERAL": 1, "PROJETO": 2, "CONTA": 3, "CANAL": 4}
itens.sort(key=lambda x: (ordem.get(x["nivel"], 9), x["onde"].lower()))
cont = {}
for i in itens:
    cont[i["nivel"]] = cont.get(i["nivel"], 0) + 1

if "--json" in sys.argv:
    print(json.dumps({"em": agora.strftime("%d/%m %H:%M"), "contagem": cont, "itens": itens}, ensure_ascii=False))
elif "--resumo" in sys.argv:
    print("[O QUE ESTA SEGURADO] " + (", ".join(f"{k} {v}" for k, v in cont.items()) or "nada")
          + " (python D:\\sistema\\catalogo\\motivos.py)")
    for i in itens:
        if i["nivel"] in ("ERRO", "GERAL"):
            print(f"  !! {i['nivel']}: {i['onde']} - {i['o_que']} - {i['motivo']}")
else:
    print(f"O QUE ESTA SEGURADO AGORA ({agora:%d/%m %H:%M}) - " + (", ".join(f"{k} {v}" for k, v in cont.items()) or "nada"))
    atual = None
    for i in itens:
        if i["nivel"] != atual:
            atual = i["nivel"]
            print(f"\n== {atual} ==")
        print(f"  {i['onde']:34} {i['o_que']:40} {i['motivo'][:90]}")
