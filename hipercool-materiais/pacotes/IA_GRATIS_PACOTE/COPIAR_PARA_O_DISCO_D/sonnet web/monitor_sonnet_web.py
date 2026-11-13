# -*- coding: utf-8 -*-
r"""monitor_sonnet_web.py — vigia as contas do Claude web (provedor claude-web do OmniRoute na VPS 157), como o
monitor_argon faz com o Argon (Fable 29/10, D26). Só leitura. Tarefa SonnetWebMonitor (1 h).

Lê na VPS (ler_claude_web.py, só o banco): contas, limitadas, uso 24 h por status/latência. Lê local
(segredos\cookies.json): quando cada sessão vence ("expira"). Grava D:\sonnet web\estado.json (o painel, aba Modelos,
mostra) e avisa no Telegram quando: todas limitadas, alguma com 401/403 (sessão caiu), ou sessão vencendo em < 7 dias
(renovar: pegar_cookies.py no PC2 + recadastrar). Nunca imprime cookie.

    python "D:\sonnet web\monitor_sonnet_web.py" [--status]
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SSH_EXE = r"C:\Program Files\Git\usr\bin\ssh.exe" if __import__("os").path.exists(r"C:\Program Files\Git\usr\bin\ssh.exe") else "ssh"  # 29/10 (Fable): sob tarefa agendada o "ssh" do PATH e o OpenSSH do Windows, que trava ate o timeout

sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: F401
except ImportError:
    pass

AQUI = Path(__file__).resolve().parent
ESTADO = AQUI / "estado.json"
SEGREDOS = AQUI / "segredos" / "cookies.json"
VPS = "hermes-bloqueio"
REMOTO = "/opt/omniroute/ler_claude_web.py"
SEM_JANELA = 0x08000000


def _avisar(texto):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, origem="sonnet-web", importante=False, chave="<SEGREDO_REMOVIDO>" + texto[:50])
    except Exception:  # noqa: BLE001
        pass


def ler_vps():
    r = subprocess.run([SSH_EXE, "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "-o", "LogLevel=ERROR", VPS, f"python3 {REMOTO}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, creationflags=SEM_JANELA)
    if r.returncode != 0 or not r.stdout.strip().startswith("{"):
        raise RuntimeError((r.stderr or r.stdout)[-200:])
    return json.loads(r.stdout)


def vencimentos():
    try:
        d = json.loads(SEGREDOS.read_text("utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for email, info in d.items():
        exp = info.get("expira") or 0
        out[email.split("@")[0]] = {"vence_em": datetime.fromtimestamp(exp).strftime("%Y-%m-%d") if exp > 0 else None,
                                    "dias": round((exp - time.time()) / 86400, 1) if exp > 0 else None,
                                    "colhido_em": info.get("em"), "maquina": info.get("maquina")}
    return out


def main(a):
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--status" in a:
        print(ESTADO.read_text("utf-8") if ESTADO.exists() else "sem estado ainda")
        return 0
    est = {"em": datetime.now().isoformat(timespec="seconds")}
    try:
        v = ler_vps()
    except Exception as e:  # noqa: BLE001
        est.update({"erro": f"VPS: {type(e).__name__}: {str(e)[:150]}", "alerta": True, "resumo": "não li a VPS"})
        ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
        print(est["erro"])
        return 1
    venc = vencimentos()
    contas = v["contas"]
    for c in contas:
        apelido = c["nome"].replace("claude-web ", "")
        c.update(venc.get(apelido, {}))
    ativas = [c for c in contas if c["ativa"]]
    limitadas = [c for c in ativas if c["limitada_agora"]]
    caidas = [c for c in ativas if any(s in c["uso_24h"] for s in ("401", "403"))]
    # o zelador_sonnet renova a partir de 14 dias; < 7 dias aqui = o zelador não está dando conta
    vencendo = [c for c in ativas if c.get("dias") is not None and c["dias"] < 7]  # desligada (barrada) não conta
    ok24 = sum((c["uso_24h"].get("200") or {}).get("n", 0) for c in contas)
    err24 = sum(u["n"] for c in contas for s, u in c["uso_24h"].items() if s != "200")
    alertas = []
    if ativas and len(limitadas) == len(ativas):
        alertas.append("todas as contas do Claude web estão limitadas (429) agora")
    if caidas:
        alertas.append("sessão caiu (401/403): " + ", ".join(c["nome"] for c in caidas))
    if vencendo:
        vencendo.sort(key=lambda c: c["dias"])
        alertas.append(f"{len(vencendo)} sessão(ões) vencem em < 7 dias (o zelador_sonnet não deu conta): "
                       + ", ".join(f"{c['nome'].replace('claude-web ', '')} ({c.get('vence_em')})" for c in vencendo[:5])
                       + (" …" if len(vencendo) > 5 else ""))
    est["opus"] = v.get("opus") or {}  # Opus 4.6 do Antigravity: sonda "oi" por conta (probe_opus na VPS)
    est.update({"contas": len(contas), "ativas": len(ativas), "limitadas": len(limitadas), "caidas": [c["nome"] for c in caidas],
                "ok_24h": ok24, "erros_24h": err24, "detalhe": contas, "alertas": alertas, "alerta": bool(alertas),
                "resumo": f"{len(ativas) - len(limitadas)} livres · {ok24} ok / {err24} erros em 24 h · "
                          + (f"vence {min((c.get('vence_em') for c in ativas if c.get('vence_em')), default='?')}")})
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
    print(json.dumps({k: est[k] for k in ("contas", "ativas", "limitadas", "ok_24h", "erros_24h", "alertas", "resumo")}, ensure_ascii=False))
    for t in alertas:
        if t.startswith("todas as contas"):
            continue  # 30/10: esse aviso é do monitor_sonnet.py (10 min, com prova real da volta); aqui só no painel
        _avisar("🟠 Claude web: " + t)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
