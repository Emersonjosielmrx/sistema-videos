#!/usr/bin/env python3
r"""vigia_melhorias.py - mantem os projetos de video com as mesmas melhorias (pedido do dono, 18/10).

Dois avisos, no Telegram (bot da postagem) e no canto da tela:
  1. novidade da tabela "Novidades" de D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md que um projeto
     ainda nao tratou (aplicou ou "nao se aplica"). Repete todo dia ate alguem marcar.
  2. "vice-versa": projeto que mudou codigo desde a ultima checagem e nao pos linha nova em Novidades - lembrete de
     registrar o que serve aos outros.

Marcar (quem levou a novidade pro projeto, ou decidiu que nao serve):
  python bin/vigia_melhorias.py --marcar manhwa-react a1b2c3 feito
  python bin/vigia_melhorias.py --marcar recapd a1b2c3 nao --motivo "usa a voz do criador"
Ver o que falta:  python bin/vigia_melhorias.py --listar      Testar sem avisar:  --ensaio
Estado: config/vigia_melhorias.json. Tarefa VigiaMelhorias (pythonw, 1x por dia, sem janela).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parent
ESTADO = BIN.parent / "config" / "vigia_melhorias.json"
LOG = BIN.parent / "logs" / "vigia_melhorias.log"
TELEGRAM = BIN.parent / "config" / "telegram.json"
DOC = Path(r"D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md")
SEM_JANELA = 0x08000000

# nomes = como o projeto aparece nas colunas "Codigo" (origem) e "Serve pra" (destino) da tabela
PROJETOS = {
    "hipercool": {"dir": Path(r"D:\hipercool-videos"), "git": True, "nomes": ["hipercool"]},
    "historias": {"dir": Path(r"D:\historias-em-frames"), "git": True, "nomes": ["historias", "histórias"]},
    "manhwa-react": {"dir": Path(r"D:\manhwa-react"), "nomes": ["manhwa-react", "manhwareact", "react"],
                     "codigo": ["manhwareact.py", "mr/*.py", "scripts/*.py", "scripts/*.bat"]},
    "recapd": {"dir": Path(r"D:\recapd-ambientes"), "nomes": ["recapd", "recap de anime", "parceiro", "anime"],
               "codigo": ["producao/bin/*.py", "producao/*.bat"]},
    # 22/10 (HUB-09): o postador (coração da postagem) e o veo ficavam fora da cobrança — novidade "pra todos"
    # nunca chegava neles, e mudança de código lá não era conferida contra a tabela de Novidades.
    "postador": {"dir": Path(r"D:\postador-de-videos"), "nomes": ["postador"],
                 "codigo": ["bin/*.py", "*.cmd"]},
    "veo": {"dir": Path(r"D:\veo"), "git": True, "nomes": ["veo"],
            "codigo": ["beta/*.py", "beta/pos_producao/*.py", "*.py"]},
}


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    try:
        print(linha, flush=True)
    except (OSError, UnicodeEncodeError):
        pass
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def telegram(msg):
    try:  # 19/10: portão único (D:\video-fila\avisos.py) — relatório do dia é rotina: vai no resumo das 9h/14h/21h
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(msg, "vigia de melhorias", html_ok=False)
        return True
    except Exception as e:  # noqa: BLE001
        log(f"portão de avisos fora ({e}); mando direto")
    try:
        d = json.loads(TELEGRAM.read_text(encoding="utf-8"))
        import urllib.parse
        import urllib.request
        dados = urllib.parse.urlencode({"chat_id": str(d["chat_id"]), "text": msg[:4000],
                                        "disable_web_page_preview": "true"}).encode()
        with urllib.request.urlopen(f"https://api.telegram.org/bot{d['bot_token']}/sendMessage", data=dados,
                                    timeout=15) as r:
            return r.status == 200
    except Exception as e:  # noqa: BLE001  (avisar nunca derruba nada)
        log(f"telegram falhou: {e}")
        return False


def tela(titulo, texto):
    esc = lambda t: str(t).replace("'", "''").replace("\n", " ")[:250]
    ps = ("Add-Type -AssemblyName System.Windows.Forms;$n = New-Object System.Windows.Forms.NotifyIcon;"
          "$n.Icon = [System.Drawing.SystemIcons]::Information;$n.Visible = $true;"
          f"$n.ShowBalloonTip(15000, '{esc(titulo)}', '{esc(texto)}', [System.Windows.Forms.ToolTipIcon]::Warning);"
          "Start-Sleep -Seconds 15;$n.Dispose()")
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=SEM_JANELA)
    except OSError:
        pass


def _cita(texto, proj):
    t = texto.lower()
    return any(n in t for n in PROJETOS[proj]["nomes"])


def novidades():
    """Linhas da tabela Novidades: [{id, data, titulo, origem, destino}]."""
    linhas, dentro = [], False
    for ln in DOC.read_text(encoding="utf-8").splitlines():
        if re.match(r"##\s+Novidades", ln):
            dentro = True
            continue
        if dentro and ln.startswith("## "):
            break
        if not dentro or not ln.startswith("|"):
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 4 or cols[0] in ("Data", "") or set(cols[0]) <= set("-: "):
            continue
        data = re.sub(r"[*\s]", "", cols[0])
        titulo = re.sub(r"\s+", " ", re.sub(r"\*\*|`", "", cols[1])).strip()
        origem = [p for p in PROJETOS if _cita(cols[2], p)]
        serve = cols[3].lower()
        citados = [p for p in PROJETOS if _cita(serve, p)]
        destino = [p for p in PROJETOS if p not in origem and ("todos" in serve or not citados or p in citados)]
        linhas.append({"id": hashlib.md5(f"{data}|{titulo[:80]}".encode()).hexdigest()[:6], "data": data,
                       "titulo": titulo, "origem": origem, "destino": destino})
    return linhas


def _data_linha(data, hoje):
    try:
        d, m = (int(x) for x in data.split("/")[:2])
        return datetime(hoje.year, m, d).date()
    except ValueError:
        return None


def mudancas(proj, desde):
    """O que mudou no codigo do projeto desde a ultima checagem (assunto do commit ou nome do arquivo)."""
    p = PROJETOS[proj]
    if p.get("git"):
        try:
            r = subprocess.run(["git", "log", f"--since={desde.isoformat(timespec='seconds')}", "--no-merges",
                                "--format=%s"], cwd=p["dir"], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=30, creationflags=SEM_JANELA)
            return [s for s in r.stdout.splitlines() if s.strip()]
        except (OSError, subprocess.SubprocessError):
            return []
    limite = desde.timestamp()
    return sorted({str(f.relative_to(p["dir"])) for g in p["codigo"] for f in p["dir"].glob(g)
                   if f.is_file() and f.stat().st_mtime > limite})


def pendentes(linhas, estado):
    feitas = estado.setdefault("tratadas", {})
    return {proj: [n for n in linhas if proj in n["destino"] and n["id"] not in feitas.get(proj, {})]
            for proj in PROJETOS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensaio", action="store_true", help="mostra o aviso sem mandar nem gravar")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--marcar", nargs=3, metavar=("PROJETO", "ID", "feito|nao"))
    ap.add_argument("--motivo", default="")
    a = ap.parse_args()
    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    linhas = novidades()

    if a.marcar:
        proj, nid, como = a.marcar
        if proj not in PROJETOS or como not in ("feito", "nao") or nid not in {n["id"] for n in linhas}:
            raise SystemExit(f"projeto ({', '.join(PROJETOS)}), id (--listar) ou feito|nao invalido")
        estado.setdefault("tratadas", {}).setdefault(proj, {})[nid] = \
            f"{como} {datetime.now():%d/%m/%Y}" + (f": {a.motivo}" if a.motivo else "")
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{proj} {nid}: {como}")
        return

    pend = pendentes(linhas, estado)
    if a.listar:
        for proj, ns in pend.items():
            print(f"{proj}: {len(ns)} pendente(s)")
            for n in ns:
                print(f"  [{n['id']}] {n['data']} {n['titulo'][:110]}")
        return

    agora = datetime.now()
    partes = []
    for proj, ns in pend.items():
        if ns:
            partes.append(f"{proj}: {len(ns)} novidade(s) pra aplicar\n" +
                          "\n".join(f"  [{n['id']}] {n['data']} {n['titulo'][:90]}" for n in ns[:6]) +
                          (f"\n  ... e mais {len(ns) - 6}" if len(ns) > 6 else ""))
    checado = estado.setdefault("checado", {})
    for proj in PROJETOS:
        desde = datetime.fromisoformat(checado[proj]) if proj in checado else agora - timedelta(days=1)
        registrou = any(proj in n["origem"] and (_data_linha(n["data"], agora) or agora.date()) >= desde.date()
                        for n in linhas)
        mud = [] if registrou else mudancas(proj, desde)
        if mud:
            partes.append(f"{proj}: mudou desde {desde:%d/%m %H:%M} sem linha nova em Novidades - algo serve aos "
                          f"outros projetos? Registre la.\n" + "\n".join(f"  - {m[:90]}" for m in mud[:6]) +
                          (f"\n  ... e mais {len(mud) - 6}" if len(mud) > 6 else ""))
        if not a.ensaio:
            checado[proj] = agora.isoformat(timespec="seconds")

    if not partes:
        log("tudo em dia: nenhuma novidade pendente e nenhuma mudanca sem registro")
    else:
        msg = ("Melhorias entre projetos\n\n" + "\n\n".join(partes) +
               f"\n\nDoc: {DOC}\nMarcar: python D:\\postador-de-videos\\bin\\vigia_melhorias.py "
               "--marcar <projeto> <id> feito|nao")
        log(msg)
        if a.ensaio:
            log("[ensaio] nao avisou")
        else:
            ok = telegram(msg)
            tela("Melhorias entre projetos", "; ".join(p.split("\n")[0] for p in partes))
            log(f"avisado (telegram={'ok' if ok else 'falhou'})")
    if not a.ensaio:
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
