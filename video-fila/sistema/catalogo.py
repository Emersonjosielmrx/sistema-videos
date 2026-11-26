# D:\video-fila\sistema\catalogo.py   (copia mestre: /mnt/win-bootcamp/claude-central/sistema/catalogo.py)
# Leitor e validador do CATALOGO UNICO (sistema.json) - OBRA etapa 1 (claude-central/PLANEJAMENTO_SISTEMA_UNICO.md).
# Roda no PC1 (Windows; le as tarefas agendadas ao vivo) e na Omarchy (le D:\video-fila\estado\tarefas_export.json copiado).
#
#   python catalogo.py validar     -> erros do catalogo (tarefa que nao existe mais, pasta/log sumido, JSON quebrado)
#   python catalogo.py ronda       -> linhas para a RONDA GERAL: tarefas sem dono, catalogo velho, projetos e estados
#   python catalogo.py md          -> tabela Markdown dos projetos (para o painel)
#   python catalogo.py projeto ID  -> tudo de um projeto
#
# Em codigo:  sys.path.insert(0, r"D:\video-fila\sistema"); import catalogo
#             catalogo.projetos(), catalogo.projeto("parceiro"), catalogo.dono_da_tarefa("CaparShorts"),
#             catalogo.logs_vigiados()  (lista no formato do config_processos_vigiados.json do vigilancia.py)
# Sem print fora do __main__ (pode ser importado por pythonw).
import json
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ARQ = AQUI / "sistema.json"
EXPORT = Path(r"D:\video-fila\estado\tarefas_export.json")


def carregar():
    return json.loads(ARQ.read_text(encoding="utf-8-sig"))


def projetos():
    return carregar()["projetos"]


def projeto(pid):
    return projetos().get(pid)


def dono_da_tarefa(nome):
    c = carregar()
    for pid, p in c["projetos"].items():
        if nome in p.get("tarefas", []):
            return pid
    if nome in c.get("avulsas", []):
        return "avulsa"
    if re.match(c.get("sistema_re", "^$"), nome):
        return "windows"
    return None


def logs_vigiados():
    """No formato do config_processos_vigiados.json (nome, log, sucesso, max_h, projeto[, desde])."""
    out = []
    for pid, p in projetos().items():
        if p.get("estado") == "parado":
            continue
        for lg in p.get("logs", []):
            d = {"nome": lg.get("nome") or f"{p['nome'][:40]}: {Path(lg['arq']).name}", "log": lg["arq"],
                 "sucesso": lg["sucesso"], "max_h": lg.get("prazo_h", 30), "projeto": pid}
            if lg.get("desde"):
                d["desde"] = lg["desde"]
            out.append(d)
    return out


def _tarefas_vivas():
    """{nome: ligada?} das tarefas do PC1. No Windows pergunta ao agendador; fora dele usa o export."""
    if os.name == "nt":
        ps = ("Get-ScheduledTask | ?{ $_.TaskPath -notlike '\\Microsoft*' } | "
              "%{ $_.TaskName + '|' + $_.State }")
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=120,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            txt = r.stdout.decode("utf-8", "replace") if b"\x00" not in r.stdout else r.stdout.decode("utf-16", "replace")
            if r.stdout and "|" not in txt:
                txt = r.stdout.decode("cp850", "replace")
            vivas = {}
            for l in txt.splitlines():
                if "|" in l:
                    n, e = l.rsplit("|", 1)
                    vivas[n.strip()] = e.strip() != "Disabled"
            if vivas:
                return vivas
        except Exception:  # noqa: BLE001
            pass
    try:
        return {t["nome"]: t["estado"] != "Disabled" for t in json.loads(EXPORT.read_text(encoding="utf-8-sig"))}
    except Exception:  # noqa: BLE001
        return None


def validar(checar_disco=None):
    """Lista de (nivel, texto). nivel: ERRO (catalogo errado) | AVISO (algo sumiu/ninguem acompanha)."""
    if checar_disco is None:
        checar_disco = os.name == "nt"
    out = []
    try:
        c = carregar()
    except Exception as e:  # noqa: BLE001
        return [("ERRO", f"sistema.json ilegivel: {e}")]
    vivas = _tarefas_vivas()
    vistas = {}
    for pid, p in c["projetos"].items():
        for campo in ("nome", "categoria"):
            if not p.get(campo):
                out.append(("ERRO", f"projeto {pid} sem '{campo}'"))
        if p.get("categoria") not in c.get("categorias", {}):
            out.append(("ERRO", f"projeto {pid}: categoria desconhecida {p.get('categoria')}"))
        for n in p.get("tarefas", []):
            if n in vistas:
                out.append(("ERRO", f"tarefa {n} em 2 projetos: {vistas[n]} e {pid}"))
            vistas[n] = pid
            if vivas is not None and n not in vivas:
                out.append(("AVISO", f"projeto {pid}: tarefa {n} nao existe mais no PC1"))
            elif vivas is not None and vivas.get(n) and p.get("estado") == "parado":
                out.append(("AVISO", f"projeto {pid} esta 'parado' no catalogo mas a tarefa {n} esta LIGADA"))
        if checar_disco:
            for pasta in p.get("pastas", []):
                if re.match(r"^[A-Za-z]:\\", pasta) and not Path(pasta).exists():
                    out.append(("AVISO", f"projeto {pid}: pasta sumiu {pasta}"))
            for lg in p.get("logs", []):
                a = lg["arq"]
                if "{" not in a and re.match(r"^[A-Za-z]:\\", a) and not Path(a).exists():
                    out.append(("AVISO", f"projeto {pid}: log sumiu {a}"))
    if vivas is not None:
        sre = re.compile(c.get("sistema_re", "^$"))
        avulsas = set(c.get("avulsas", []))
        for n, ligada in sorted(vivas.items()):
            if n in vistas or n in avulsas or sre.match(n):
                continue
            out.append(("AVISO", f"TAREFA SEM DONO no catalogo ({'ligada' if ligada else 'desligada'}): {n}"))
        for n in avulsas:
            if n not in vivas:
                out.append(("AVISO", f"avulsa {n} nao existe mais (tirar da lista)"))
    return out


def linhas_ronda():
    c = carregar()
    ps = c["projetos"]
    por_estado = {}
    for p in ps.values():
        por_estado[p.get("estado", "ativo")] = por_estado.get(p.get("estado", "ativo"), 0) + 1
    v = validar()
    sem_dono = [t for n, t in v if "SEM DONO" in t]
    yield (f"[CATALOGO] {len(ps)} projetos (" + ", ".join(f"{k} {n}" for k, n in sorted(por_estado.items())) +
           f") | {sum(len(p.get('tarefas', [])) for p in ps.values())} tarefas com dono | {len(c.get('avulsas', []))} avulsas"
           f" | sem dono: {len(sem_dono)} | avisos: {len(v)}")
    for nivel, t in v[:25]:
        yield f"  !! {nivel} catalogo: {t}"
    if os.name == "nt":
        ok, ruim = [], []
        for pid, h, lim in producao():
            if h is None:
                ruim.append(f"{pid} sem nenhum mp4")
            elif h > lim:
                ruim.append(f"{pid} parado ha {h:.0f} h (limite {lim} h)")
            else:
                ok.append(f"{pid} {h:.0f}h")
        yield "[PRODUCAO DE VIDEO] (do catalogo) ok: " + ", ".join(ok)
        for r in ruim:
            yield "  !! " + r


def producao():
    """Saida de cada projeto com 'saida' (mp4 mais novo x parado_h). So no PC1 (precisa do disco)."""
    import time
    for pid, p in projetos().items():
        s = p.get("saida")
        if not s or not s.get("parado_h") or p.get("estado") == "parado":
            continue
        mais_novo = 0
        try:
            for raiz, _, arqs in os.walk(s["pasta"]):
                for a in arqs:
                    if a.lower().endswith(".mp4"):
                        try:
                            mais_novo = max(mais_novo, os.path.getmtime(os.path.join(raiz, a)))
                        except OSError:
                            pass
        except OSError:
            pass
        h = (time.time() - mais_novo) / 3600 if mais_novo else None
        yield pid, h, s["parado_h"]


def md():
    c = carregar()
    linhas = ["| Cat. | Projeto | Estado | Tarefas (ligadas/total) | Saída vigiada | Logs vigiados | Chat dono |",
              "|---|---|---|---|---|---|---|"]
    vivas = _tarefas_vivas() or {}
    for pid, p in sorted(c["projetos"].items(), key=lambda x: (x[1]["categoria"], x[0])):
        ts = p.get("tarefas", [])
        lig = sum(1 for t in ts if vivas.get(t))
        s = p.get("saida")
        linhas.append(f"| {p['categoria'][0]} | **{pid}** — {p['nome']} | {p.get('estado', 'ativo')} | {lig}/{len(ts)} | "
                      f"{('parado > ' + str(s['parado_h']) + ' h') if s and s.get('parado_h') else '—'} | "
                      f"{len(p.get('logs', []))} | {p.get('chat_dono', '—')} |")
    return "\n".join(linhas)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:] or ["validar"]
    if a[0] == "validar":
        v = validar()
        for nivel, t in v:
            print(f"{nivel}: {t}")
        print(f"{len(v)} item(ns); {sum(1 for n, _ in v if n == 'ERRO')} erro(s)")
        sys.exit(1 if any(n == "ERRO" for n, _ in v) else 0)
    elif a[0] == "ronda":
        for l in linhas_ronda():
            print(l)
    elif a[0] == "md":
        print(md())
    elif a[0] == "projeto" and len(a) > 1:
        print(json.dumps(projeto(a[1]), ensure_ascii=False, indent=1))
    elif a[0] == "logs":
        print(json.dumps(logs_vigiados(), ensure_ascii=False, indent=1))
    else:
        print(__doc__ if __doc__ else "uso: catalogo.py validar|ronda|md|projeto ID|logs")
