r"""painel_externo.py (PC, tarefa PainelExterno a cada 5 min) — manda ao painel de créditos da VPS a situação das
contas que rodam no PC: Argon (D:\gemini-argo), Genspark e 1min (D:\opus-gratis-v2-desktop).
Só LÊ os arquivos de estado locais; não chama nenhuma conta. Não manda chave nem cookie (só nome, números e situação).
Destino: /opt/omniroute/painel_externo.json na VPS 157 (o painel_creditos.py lê)."""
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone

ARGON = r"D:\gemini-argo\contas_argon.json"
GENSPARK = r"D:\opus-gratis-v2-desktop\contas_genspark.json"
UMIN = r"D:\opus-gratis-v2-desktop\umin\umin_contas.json"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if os.path.exists(r"C:\Program Files\Git\usr\bin\ssh.exe") else "ssh"
DESTINO = "/opt/omniroute/painel_externo.json"
SEM_JANELA = 0x08000000
LOCAL = datetime.now().astimezone().tzinfo


def ler(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)["contas"]


def utc(s):
    """Horário local do PC (sem fuso) -> ISO UTC."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).replace(tzinfo=LOCAL).astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def taxa(st):
    ok, er = st.get("ok", 0), st.get("erros", 0)
    return (round(100 * ok / (ok + er)) if ok + er else None), ok, ok + er


def argon(agora):
    out = []
    for c in ler(ARGON):
        t, ok, tot = taxa(c.get("stats", {}))
        mortos = c.get("cookies_mortos_ate") and c["cookies_mortos_ate"] > agora
        sem = c.get("sem_cota_ate") and c["sem_cota_ate"] > agora
        if c.get("bloqueada"):
            g, info = 3, "bloqueada"
        elif mortos:
            g, info = 1, "login vencido (cookies) até " + c["cookies_mortos_ate"][11:16]
        elif sem:
            g, info = 1, "sem cota"
        else:
            g, info = 0, "pronta"
        if c.get("ultimo_erro") and g:
            info += " · " + c["ultimo_erro"][:60]
        out.append(dict(nome=c["email"], grupo=g, ativa=not c.get("bloqueada"), taxa=t, ok=ok, tot=tot, info=info,
                        modelo="Gemini web (Argon)", quando=utc(c.get("ultimo_uso")),
                        libera=utc(c["sem_cota_ate"] if sem else (c["cookies_mortos_ate"] if mortos else None))))
    return out


def genspark(agora):
    out, hoje = [], agora[:10]
    for c in ler(GENSPARK):
        t, ok, tot = taxa(c.get("stats", {}))
        cred = 100 if c.get("data_cota") != hoje else c.get("creditos", 100)
        sem = c.get("sem_cota_ate") and c["sem_cota_ate"] > agora
        if c.get("bloqueada"):
            g, info = 3, "bloqueada"
        elif not c.get("logado"):
            g, info = 2, "precisa logar"
        elif c.get("opus") is False:
            g, info = 3, "sem Opus no grátis"
        elif sem or cred < 3:
            g, info = 1, "sem crédito hoje"
        else:
            g, info = 0, "pronta"
        out.append(dict(nome=c["email"], grupo=g, ativa=not c.get("bloqueada"), ps=float(cred), taxa=t, ok=ok, tot=tot,
                        info=info, modelo="Opus 5.5 grátis", quando=utc(c.get("ultimo_uso")),
                        libera=utc(c["sem_cota_ate"]) if sem else None))
    return out


def umin(agora):
    out = []
    for c in ler(UMIN):
        t, ok, tot = taxa(c.get("stats", {}))
        saldo = c.get("base", 265000) - c.get("usado", 0)
        sem = c.get("sem_cota_ate") and c["sem_cota_ate"] > agora
        g, info = (1, "sem crédito hoje") if sem else ((0, "pronta") if saldo >= 14000 else (1, "saldo baixo"))
        out.append(dict(nome=c.get("email") or c["apelido"], grupo=g, ps=max(0.0, round(100 * saldo / 265000, 1)),
                        taxa=t, ok=ok, tot=tot, info=f"{info} · saldo {saldo:,}".replace(",", "."),
                        modelo="Opus 5.5 (1min)", quando=utc(c.get("visto_em")), libera=utc(c["sem_cota_ate"]) if sem else None))
    return out


def main():
    agora = datetime.now().isoformat(timespec="minutes")
    dados = {"em": datetime.now(timezone.utc).isoformat(), "notas": {}}
    for nome, f in (("argon", argon), ("genspark", genspark), ("1min", umin)):
        try:
            dados[nome] = f(agora)
        except Exception as e:  # um arquivo quebrado não derruba as outras abas
            dados[nome] = []
            dados["notas"][nome] = f"erro lendo no PC: {e}"[:200]
    dados["notas"].setdefault("1min", "Cada conta ganha 15 mil por dia (visita diária); 1 Opus 5.5 gasta ~14 mil.")
    dados["notas"].setdefault("genspark", "100 créditos por dia por conta (~3 por mensagem); renova 00:05.")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(dados, tmp, ensure_ascii=False)
    try:
        with open(tmp.name, "rb") as fh:
            subprocess.run([SSH, "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", "hermes-bloqueio",
                            f"cat > {DESTINO}.tmp && mv {DESTINO}.tmp {DESTINO}"],
                           stdin=fh, check=True, timeout=60, creationflags=SEM_JANELA)
    finally:
        os.unlink(tmp.name)
    print({k: len(v) for k, v in dados.items() if isinstance(v, list)}, dados["notas"])


if __name__ == "__main__":
    main()
