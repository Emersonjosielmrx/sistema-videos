r"""vigia_flow.py — vigia das 2 rotas do Flow (12/11, dona: "tem que ter vigilância caso pare de funcionar de novo e
qualquer coisa que trocar na interface; trocar pro normal pra não parar; ir consertar a rota nova; e se o normal parar
também, avisar").

Rotas: HTTP ("sem navegador", flow_gerar.imagem_beluga) e TELA (Chrome/Playwright, gera_auto / gera_imagem).
A cada rodada (tarefa VigiaFlow, 10 em 10 min) lê o que REALMENTE aconteceu:
  - HTTP: maquina_remota.log ("Flow por HTTP imagem/video ...: ok|FLOW_...") — de todas as máquinas;
  - TELA: veo\beta\logs\worker_*.log (rc=0 / OK video salvo) e claude-code-video cron.log ("[imagem] cena N: flow").
Decide e grava logs\vigia_flow.json (lido por cadeia_veo.http_remoto_ligado):
  1. HTTP quebrou (>= 6 pedidos em 30 min e < 25% ok, sem contar recusa de CONTEÚDO, que é do prompt): HTTP DESLIGADO
     (tudo vai pela tela, sem parar a produção) + guarda a evidência (últimos erros) + avisa "interface do Flow mudou?".
  2. HTTP desligado pelo vigia: a cada 60 min libera 1 pedido de teste (modo "teste"); deu ok = religa e avisa.
  3. As 2 rotas sem nenhum ok há 2 h com pedido acontecendo = aviso "Flow PAROU nas duas rotas".
FLOW_VIGIA=0 (ou "desligado": true no json) = o vigia não decide nada.

    python vigia_flow.py           # 1 rodada
    python vigia_flow.py estado    # mostra a decisão atual
"""
import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
EST = os.path.join(BASE, "logs", "vigia_flow.json")
LOG_REMOTO = r"D:\postador-de-videos\logs\maquina_remota.log"
CCV = r"D:\claude-code-video\estado\cron.log"
JANELA_MIN, MIN_PEDIDOS, TAXA_MIN = 30, 6, 0.25
RETESTE_MIN, PARADA_H = 60, 2
CONTEUDO = re.compile(r"PUBLIC_ERROR_(SEXUAL|UNSAFE|VIOLEN|MINOR|CHILD|CELEB|PERSON|HATE)", re.I)


def _log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    with open(os.path.join(BASE, "logs", "vigia_flow.log"), "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ler():
    try:
        with open(EST, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def gravar(d):
    tmp = EST + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, EST)


def http_permitido(tipo="imagem"):
    """Lido por cadeia_veo.http_remoto_ligado: False = o vigia desligou a rota HTTP desse tipo (vai pela tela).
    Em modo teste, deixa passar 1 pedido e marca que passou."""
    if os.environ.get("FLOW_VIGIA") == "0":
        return True
    d = ler()
    r = (d.get("rotas") or {}).get(tipo) or {}
    if d.get("desligado") or r.get("estado", "ligado") == "ligado":
        return True
    if r.get("estado") == "teste" and not r.get("teste_usado"):
        r["teste_usado"] = datetime.now().isoformat(timespec="seconds")
        d.setdefault("rotas", {})[tipo] = r
        gravar(d)
        return True
    return False


def _avisar(texto, chave):
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "vigia do Flow", importante=True, chave=chave)
    except Exception as e:  # noqa: BLE001
        _log(f"aviso não foi ({type(e).__name__}: {e})")


def _http_recentes(desde):
    out = []
    try:
        with open(LOG_REMOTO, encoding="utf-8", errors="replace") as f:
            linhas = f.readlines()[-6000:]
    except OSError:
        return out
    ano = datetime.now().year
    for l in linhas:
        m = re.match(r"\[(\d\d)/(\d\d) (\d\d:\d\d:\d\d)\] (\w+): Flow por HTTP (imagem|video-pedir|video)\s*\(([^)]*)\): (.*)", l)
        if not m:
            continue
        t = datetime.strptime(f"{ano}-{m.group(2)}-{m.group(1)} {m.group(3)}", "%Y-%m-%d %H:%M:%S")
        if t < desde:
            continue
        resto = m.group(7)
        tipo = "imagem" if m.group(5) == "imagem" else "video"
        out.append({"t": t, "maq": m.group(4), "tipo": tipo, "conta": m.group(6), "ok": resto.startswith("ok"),
                    "conteudo": bool(CONTEUDO.search(resto)), "msg": resto.strip()[:240]})
    return out


def _tela_ok(desde):
    """Quantos ok pela TELA desde `desde` (vídeo do Veo + imagem do Claude Code Video)."""
    n = 0
    for f in glob.glob(os.path.join(BASE, "logs", "worker_*.log")):
        try:
            if datetime.fromtimestamp(os.path.getmtime(f)) < desde:
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
            n += "OK video salvo" in txt
        except OSError:
            continue
    try:
        ano = datetime.now().year
        with open(CCV, encoding="utf-8", errors="replace") as f:
            for l in f.readlines()[-3000:]:
                m = re.match(r"\[(\d\d)/(\d\d) (\d\d:\d\d:\d\d)\]\s+\[imagem\] cena \d+: flow", l)
                if m and datetime.strptime(f"{ano}-{m.group(2)}-{m.group(1)} {m.group(3)}", "%Y-%m-%d %H:%M:%S") >= desde:
                    n += 1
    except OSError:
        pass
    return n


def rodada():
    if os.environ.get("FLOW_VIGIA") == "0":
        return
    d = ler()
    if d.get("desligado"):
        return
    agora = datetime.now()
    rotas = d.setdefault("rotas", {})
    recentes = _http_recentes(agora - timedelta(minutes=JANELA_MIN))
    for tipo in ("imagem", "video"):
        r = rotas.setdefault(tipo, {"estado": "ligado"})
        tent = [x for x in recentes if x["tipo"] == tipo and not x["conteudo"]]
        oks = sum(1 for x in tent if x["ok"])
        r["janela"] = {"pedidos": len(tent), "ok": oks, "em": agora.isoformat(timespec="minutes")}
        if r["estado"] == "ligado":
            if len(tent) >= MIN_PEDIDOS and oks / len(tent) < TAXA_MIN:
                erros = [x["msg"] for x in tent if not x["ok"]][-8:]
                r.update(estado="desligado", desde=agora.isoformat(timespec="seconds"), evidencia=erros,
                         proximo_teste=(agora + timedelta(minutes=RETESTE_MIN)).isoformat(timespec="seconds"))
                _log(f"HTTP {tipo} DESLIGADO: {oks}/{len(tent)} ok em {JANELA_MIN} min — vai tudo pela tela. "
                     f"Erros: {erros[-3:]}")
                _avisar(f"Flow: a rota SEM NAVEGADOR ({tipo}) quebrou — {oks}/{len(tent)} ok em {JANELA_MIN} min. "
                        f"Troquei pra tela sozinho (a produção segue). Provável mudança na interface do Flow; "
                        f"erro: {erros[-1][:160] if erros else '?'}", f"vigia_flow_{tipo}_caiu")
        else:  # desligado ou teste
            depois = [x for x in recentes if x["tipo"] == tipo and r.get("teste_usado")
                      and x["t"] >= datetime.fromisoformat(r["teste_usado"])]
            if any(x["ok"] for x in depois):
                _log(f"HTTP {tipo} RELIGADO: o pedido de teste deu certo")
                _avisar(f"Flow: a rota SEM NAVEGADOR ({tipo}) voltou a funcionar no teste — religada.",
                        f"vigia_flow_{tipo}_voltou")
                rotas[tipo] = {"estado": "ligado", "religado": agora.isoformat(timespec="seconds"), "janela": r.get("janela")}
                continue
            if r["estado"] == "teste" and r.get("teste_usado") and depois and not any(x["ok"] for x in depois):
                r.update(estado="desligado", teste_usado=None,
                         proximo_teste=(agora + timedelta(minutes=RETESTE_MIN)).isoformat(timespec="seconds"))
                _log(f"HTTP {tipo}: teste falhou ({depois[-1]['msg'][:120]}) — segue pela tela, novo teste em {RETESTE_MIN} min")
            elif r["estado"] == "desligado" and agora >= datetime.fromisoformat(r.get("proximo_teste") or agora.isoformat()):
                r.update(estado="teste", teste_usado=None)
                _log(f"HTTP {tipo}: liberando 1 pedido de TESTE")
    # as 2 rotas paradas
    desde = agora - timedelta(hours=PARADA_H)
    http_ok = sum(1 for x in _http_recentes(desde) if x["ok"])
    tela_ok = _tela_ok(desde)
    houve_pedido = bool(_http_recentes(desde)) or bool(glob.glob(os.path.join(BASE, "logs", "worker_*.log")))
    d["ultimas_2h"] = {"http_ok": http_ok, "tela_ok": tela_ok, "em": agora.isoformat(timespec="minutes")}
    if houve_pedido and http_ok == 0 and tela_ok == 0:
        _log(f"ALERTA: nenhuma imagem/vídeo do Flow em {PARADA_H} h por NENHUMA rota")
        _avisar(f"Flow PAROU nas duas rotas: nenhuma imagem/vídeo em {PARADA_H} h (HTTP 0, tela 0). "
                "Conta/crédito/login ou mudança grande no Flow — precisa olhar.", "vigia_flow_tudo_parado")
    gravar(d)
    _log(f"rodada: imagem={rotas['imagem']['estado']} ({rotas['imagem'].get('janela')}) "
         f"video={rotas['video']['estado']} | 2h: http_ok={http_ok} tela_ok={tela_ok}")


if __name__ == "__main__":
    # 12/11: pela tarefa (pythonw, sem console) sys.stdout é None — o reconfigure quebrava e a tarefa saía com 0x1
    # sem rodar nada (o vigia nunca vigiava de verdade)
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1 and sys.argv[1] == "estado":
        print(json.dumps(ler(), ensure_ascii=False, indent=1))
    else:
        rodada()
