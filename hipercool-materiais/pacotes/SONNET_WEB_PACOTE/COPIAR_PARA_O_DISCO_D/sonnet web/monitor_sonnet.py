# -*- coding: utf-8 -*-
r"""monitor_sonnet.py — vigia das contas Sonnet web (claude-web do OmniRoute), no molde do monitor_argon.py.
Tarefa MonitorSonnet a cada 10 min (oculta). Avisos pelo portão D:\video-fila\avisos.py:
  - TODAS as contas sem uso agora (limitadas ou com erro): avisa uma vez, com a hora da 1ª que volta;
  - voltou depois disso: confirma com DOIS pedidos reais pelo claude-web (id "chatcmpl-") antes de avisar
    (regra "aviso só com prova real").
  - poucas contas boas (< 5): avisa uma vez por dia.
Estado: D:\sonnet web\monitor_sonnet.json.  `--status` só imprime.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: F401  (nenhuma janela na tela da dona)
except ImportError:
    pass
sys.path.insert(0, r"D:\video-fila")

BASE = Path(r"D:\sonnet web")
STATE = BASE / "monitor_sonnet.json"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SEM_JANELA = 0x08000000
RUINS = ("expired", "error", "invalid")  # status que não voltam sozinhos (cookie)


def ssh(cmd, entrada=None, timeout=120):
    # sem entrada: stdin fechado (sob a tarefa oculta o ssh herdava um stdin que nunca fecha e podia esperar à toa)
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR",
                        "hermes-bloqueio", cmd], input=entrada, stdin=None if entrada is not None else subprocess.DEVNULL,
                       capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
    return r.stdout.decode("utf-8", "replace")


def estado_vps():
    saida = ssh("python3 /opt/omniroute/sonnet_estado.py")
    try:
        return json.loads(saida)
    except ValueError:
        raise RuntimeError("VPS não respondeu o estado: " + (" ".join(saida.split())[-150:] or "vazio")) from None


def _data(iso):
    """ISO -> datetime com fuso (os antigos sem fuso eram hora da VPS, CET)."""
    d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    if d.tzinfo is None:
        from datetime import timedelta
        d = d.replace(tzinfo=timezone(timedelta(hours=1)))
    return d


def resumo(d):
    contas = [c for c in d["contas"] if c["ativa"]]
    ruins = [c for c in contas if (c["status"] or "") in RUINS]
    limitadas = [c for c in contas if c["limitada_ate"] and c not in ruins]
    prontas = [c for c in contas if c not in ruins and c not in limitadas]
    volta = min((c["limitada_ate"] for c in limitadas), default=None)
    return {"total": len(contas), "prontas": len(prontas), "limitadas": len(limitadas), "ruins": len(ruins),
            "nomes_ruins": [c["nome"].replace("claude-web ", "") for c in ruins], "volta": volta}


def confirmar():
    """2 pedidos reais ao cw/claude-sonnet-5-5 na VPS; ok só se os 2 vierem do claude-web (id chatcmpl-)."""
    cmd = ("K=$(sqlite3 /opt/omniroute/data/storage.sqlite \"SELECT key FROM api_keys WHERE revoked_at IS NULL "
           "AND is_active=1 LIMIT 1;\"); for i in 1 2; do curl -s -m 90 http://localhost:20128/v1/chat/completions "
           "-H \"Authorization: Bearer $K\" -H 'Content-Type: application/json' -d '{\"model\":\"cw/claude-sonnet-5-5\","
           "\"stream\":false,\"messages\":[{\"role\":\"user\",\"content\":\"responda so: ok\"}]}'; echo; done")
    linhas = [x for x in ssh(cmd, timeout=240).splitlines() if x.strip()]
    ok = [x for x in linhas if '"id":"chatcmpl-' in x and '"content"' in x]
    return len(ok) >= 2, (linhas[-1][:150] if linhas else "sem resposta")


def ler_estado():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gravar_estado(e):
    STATE.write_text(json.dumps(e, indent=2, ensure_ascii=False), encoding="utf-8")


def enviar(msg, chave):
    try:
        import avisos
        return bool(avisos.enviar(msg, "sonnet-monitor", importante=True, chave=chave))
    except Exception as ex:  # noqa: BLE001
        print("aviso não saiu:", ex, "|", msg)
        return False


def enviar_rotina(msg):
    try:
        import avisos
        avisos.enviar(msg, "sonnet-monitor", importante=False, html_ok=False)
    except Exception as ex:  # noqa: BLE001
        print("aviso não saiu:", ex, "|", msg)


def hora_local(iso):
    if not iso:
        return "?"
    return _data(iso).astimezone().strftime("%d/%m %H:%M")


def main(a):
    est = ler_estado()
    agora = datetime.now()
    try:
        d = estado_vps()
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as ex:
        # 30/10: antes o monitor caía com JSONDecodeError e ninguém sabia. 3 falhas seguidas (30 min) = 1 aviso.
        est["falhas_vps"] = est.get("falhas_vps", 0) + 1
        print(f"{agora:%d/%m %H:%M} sem estado da VPS ({est['falhas_vps']}x seguidas): {ex}")
        if est["falhas_vps"] == 3 and "--status" not in a:
            enviar(f"<b>Monitor Sonnet</b>: não consigo ler a VPS do OmniRoute há 30 min ({str(ex)[:120]}).",
                   f"sonnet-vps:{agora:%Y-%m-%d %H}")
        gravar_estado(est)
        return
    est.pop("falhas_vps", None)
    r = resumo(d)
    r["visto"] = agora.isoformat(timespec="minutes")
    print(f"{agora:%d/%m %H:%M} {r['prontas']}/{r['total']} prontas | {r['limitadas']} limitadas | {r['ruins']} com erro de cookie"
          + (f" | 1ª volta {hora_local(r['volta'])}" if r["volta"] else ""))
    # 30/10: o sonnet-oi da VPS manda "oi" em cada conta quando o limite dela vence; aqui só repasso as voltas novas
    try:
        oi = json.loads(ssh("python3 /opt/omniroute/sonnet_oi.py --status"))
        print(f"esperando oi: {len(oi['esperando_oi'])} | últimas voltas: "
              + ", ".join(f"{n} {hora_local(v)[6:]}" for v, n in oi["ultimas_voltas"][:5]))
        corte = _data(est["ultima_volta_avisada"]) if est.get("ultima_volta_avisada") else None
        novas = sorted((_data(v), n) for v, n in oi["ultimas_voltas"] if not corte or _data(v) > corte)
        if novas and "--status" not in a:
            enviar_rotina("Sonnet web: conta(s) de volta (confirmado com 'oi' na própria conta): "
                          + ", ".join(f"{n} às {v.astimezone():%H:%M}" for v, n in novas))
            est["ultima_volta_avisada"] = novas[-1][0].isoformat(timespec="minutes")
    except (ValueError, KeyError, TypeError) as ex:
        print("sonnet_oi sem status:", ex)
    if "--status" in a:
        return
    if r["prontas"] == 0 and not est.get("sem_conta_desde"):
        est["sem_conta_desde"] = r["visto"]
        enviar(f"<b>Sonnet web SEM conta</b> ({agora:%H:%M})\n\nAs {r['total']} contas do claude.ai estão sem uso agora "
               f"({r['limitadas']} no limite, {r['ruins']} com cookie ruim).\n1ª volta prevista: {hora_local(r['volta'])}.\n"
               f"Enquanto isso o VS Code cai nas contas do Claude Code (sonnet-fila).", f"sonnet-sem:{r['visto'][:13]}")
    elif r["prontas"] > 0 and est.get("sem_conta_desde"):
        ok, detalhe = confirmar()
        if ok:
            enviar(f"<b>Sonnet web VOLTOU</b> ({agora:%H:%M})\n\n{r['prontas']} conta(s) prontas; confirmado com 2 respostas "
                   f"reais do claude-web.", f"sonnet-voltou:{r['visto'][:13]}")
            est.pop("sem_conta_desde", None)
        else:
            print("ainda não confirmou:", detalhe)
    dia = agora.strftime("%Y-%m-%d")
    if r["ruins"] and est.get("ruins_avisado") != dia and r["total"] - r["ruins"] < 5:
        enviar(f"<b>Sonnet web</b>: só {r['total'] - r['ruins']} conta(s) com cookie bom. Com erro: "
               f"{', '.join(r['nomes_ruins'][:10])}. O zelador_sonnet renova; se repetir, olhar D:\\sonnet web.",
               f"sonnet-ruins:{dia}")
        est["ruins_avisado"] = dia
    est["ultimo"] = r
    gravar_estado(est)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
