"""testes.py — registro das pastas/arquivos de TESTE, para nada de teste ficar enchendo o disco (dona 02/11/2026:
"sempre que forem feitos testes, têm que ser apagados quando se muda de teste e não precisa mais deles; documentado
pra que, se o chat fechar, outro agente possa ver o que apagar de imediato").

REGRA PARA TODO CHAT: criou pasta/arquivo de teste (vídeos de prova, prévias, comparações, renders de teste) ->
registre aqui ANTES de encher; mudou de teste ou terminou -> encerre. O que vencer e estiver parado há 6 h a faxina
diária (faxina_disco.py) limpa sozinha. Lista legível sempre atualizada: D:\\video-fila\\TESTES_TEMPORARIOS.md

    python testes.py registrar <caminho> --motivo "..." [--dias 3] [--drive] [--chat <nome>]
    python testes.py encerrar <caminho>      # acabou: limpa já (com --drive no registro, copia e confere antes)
    python testes.py listar
    python testes.py limpar [--simular]      # o que a faxina chama: limpa os vencidos

--drive = guarda no Drive (manhwa-drive:arquivo-pc1/testes/) antes de apagar — use quando o resultado pode ser útil
depois. Sem --drive = apaga direto (sobra de render, prévia, comparação já decidida).
"""
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REGISTRO = AQUI / "testes_temporarios.json"
LISTA_MD = AQUI / "TESTES_TEMPORARIOS.md"
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "manhwa-drive:arquivo-pc1/testes"
PARADO_H = 6  # mexido há menos que isso = ainda em uso, fica pra próxima
# nunca limpar: material de produção, logins, modelos, venv (registro errado aqui não pode virar desastre)
PROTEGIDO = [r"D:\hipercool-materiais\python", r"D:\hipercool-materiais\models", r"D:\hipercool-materiais\assets",
             r"D:\hipercool-materiais\panels", r"D:\logins-google", r"D:\caches", r"D:\tools",
             r"D:\hipercool-materiais\videos"]


def _ler():
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _gravar(itens):
    tmp = REGISTRO.with_suffix(".tmp")
    tmp.write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, REGISTRO)
    _escrever_md(itens)


def _escrever_md(itens):
    hoje = dt.datetime.now()
    linhas = ["# Testes temporários (gerado por testes.py — não editar à mão)", "",
              "Tudo aqui é TESTE e pode sair. Vencido = a faxina diária limpa sozinha (se parado há 6 h).",
              "Precisa de espaço já? `python D:\\video-fila\\testes.py encerrar <caminho>` em cada linha vencida.", "",
              "| Caminho | Para quê | Chat | Criado | Vence | Ao limpar |", "|---|---|---|---|---|---|"]
    for i in sorted(itens, key=lambda x: x["vence"]):
        venc = "**VENCIDO** " if dt.datetime.fromisoformat(i["vence"]) < hoje else ""
        linhas.append(f"| `{i['caminho']}` | {i['motivo']} | {i.get('chat', '?')} | {i['criado'][:16]} | "
                      f"{venc}{i['vence'][:16]} | {'Drive e apaga' if i.get('drive') else 'apaga'} |")
    if not itens:
        linhas.append("| (nenhum teste registrado) | | | | | |")
    LISTA_MD.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _norm(c):
    return str(Path(c).resolve()).rstrip("\\")


def _protegido(c):
    c = c.lower()
    if len(c) <= 3:  # raiz de disco
        return True
    return any(c == p.lower() or c.startswith(p.lower() + "\\") for p in PROTEGIDO)


def _ultima_mexida(p):
    p = Path(p)
    if p.is_file():
        return p.stat().st_mtime
    m = p.stat().st_mtime
    for r, _d, fs in os.walk(p, onerror=lambda e: None):
        for f in fs:
            try:
                m = max(m, os.path.getmtime(os.path.join(r, f)))
            except OSError:
                pass
    return m


def _tam(p):
    p = Path(p)
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file() and not f.is_symlink())


def _rclone(*a):
    r = subprocess.run([RCLONE, *a, "--retries", "3"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", creationflags=0x08000000)
    return r.returncode, (r.stdout + r.stderr).strip()[-300:]


def _limpar_um(item, simular=False, forcar=False):
    """Devolve (bytes liberados, motivo se não limpou)."""
    p = Path(item["caminho"])
    if not p.exists():
        return 0, "não existe mais"
    if _protegido(item["caminho"]):
        return 0, "caminho protegido (produção/login) — não limpo"
    if not forcar and time.time() - _ultima_mexida(p) < PARADO_H * 3600:
        return 0, f"mexido há menos de {PARADO_H} h (em uso)"
    tam = _tam(p)
    if simular:
        return tam, None
    if item.get("drive"):
        destino = f"{DRIVE}/{p.name}_{item['criado'][:10]}"
        if p.is_file():
            cod, s = _rclone("copy", str(p), destino)
            if cod == 0:
                cod, s = _rclone("check", str(p.parent), destino, "--one-way", "--include", "/" + p.name)
        else:
            cod, s = _rclone("copy", str(p), destino, "--transfers", "8")
            if cod == 0:
                cod, s = _rclone("check", str(p), destino, "--one-way")
        if cod != 0:
            return 0, f"Drive falhou, fica no PC: {s}"
        item["no_drive"] = destino
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
    else:
        p.unlink()
    return (tam, None) if not p.exists() else (0, "não consegui apagar tudo (arquivo preso)")


def registrar(caminho, motivo, dias=3, drive=False, chat=""):
    c = _norm(caminho)
    if _protegido(c):
        sys.exit(f"recusado: {c} é pasta de produção/login, não é teste")
    itens = [i for i in _ler() if i["caminho"].lower() != c.lower()]
    agora = dt.datetime.now()
    itens.append({"caminho": c, "motivo": motivo, "chat": chat, "drive": drive,
                  "criado": agora.isoformat(timespec="minutes"),
                  "vence": (agora + dt.timedelta(days=dias)).isoformat(timespec="minutes")})
    _gravar(itens)
    print(f"registrado: {c} (vence em {dias} dia(s), {'Drive e apaga' if drive else 'apaga'})")


def encerrar(caminho):
    c = _norm(caminho)
    itens = _ler()
    alvo = next((i for i in itens if i["caminho"].lower() == c.lower()), None)
    if not alvo:
        sys.exit(f"não está registrado: {c}  (veja: python testes.py listar)")
    liberado, motivo = _limpar_um(alvo, forcar=True)
    if motivo and motivo != "não existe mais":
        sys.exit(f"não limpei {c}: {motivo}")
    _gravar([i for i in itens if i is not alvo])
    print(f"encerrado: {c} ({liberado / 1e9:.2f} GB){' -> ' + alvo['no_drive'] if alvo.get('no_drive') else ''}")


def limpar(simular=False, log=print):
    """Chamado pela faxina diária: limpa os vencidos parados. Devolve bytes liberados."""
    itens, ficam, total = _ler(), [], 0
    agora = dt.datetime.now()
    for i in itens:
        if dt.datetime.fromisoformat(i["vence"]) > agora:
            ficam.append(i)
            continue
        liberado, motivo = _limpar_um(i, simular)
        if motivo == "não existe mais" and not simular:
            continue
        if motivo:
            log(f"teste {i['caminho']}: {motivo}")
            ficam.append(i)
            continue
        total += liberado
        log(f"teste {i['caminho']}: {'liberaria' if simular else 'limpo'} {liberado / 1e9:.2f} GB"
            f"{' (Drive: ' + i['no_drive'] + ')' if i.get('no_drive') else ''}")
        if simular:
            ficam.append(i)
    if not simular:
        _gravar(ficam)
    return total


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("registrar")
    r.add_argument("caminho")
    r.add_argument("--motivo", required=True)
    r.add_argument("--dias", type=float, default=3)
    r.add_argument("--drive", action="store_true")
    r.add_argument("--chat", default="")
    sub.add_parser("encerrar").add_argument("caminho")
    sub.add_parser("listar")
    sub.add_parser("limpar").add_argument("--simular", action="store_true")
    a = ap.parse_args()
    if a.cmd == "registrar":
        registrar(a.caminho, a.motivo, a.dias, a.drive, a.chat)
    elif a.cmd == "encerrar":
        encerrar(a.caminho)
    elif a.cmd == "listar":
        _escrever_md(_ler())
        print(LISTA_MD.read_text(encoding="utf-8"))
    else:
        print(f"total: {limpar(a.simular) / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
