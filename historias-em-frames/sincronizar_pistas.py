"""sincronizar_pistas.py — leva o codigo da RAIZ (onde se desenvolve e testa) para as
pistas prod/beta/teste, que rodam a producao (botoes LIGAR Prod/Beta/Teste).

O que faz em cada pista:
  - copia bin/*.py (menos backups "_*"), os .py/.md da raiz e os configs novos;
  - settings.json: MANTEM os valores da pista e so acrescenta chaves novas da raiz;
  - copia secrets/omniroute.json (chave do gateway);
  - conserta workspace/assets (junction -> D:\\hipercool-materiais\\assets) e troca
    junctions mortas (apontavam pro hipercool-inferior-fix, apagado) por pastas normais;
  - roda o doctor da pista.

Uso:  venv\\Scripts\\python.exe sincronizar_pistas.py [prod beta teste] [--dry-run]
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ASSETS = Path(r"D:\hipercool-materiais\assets")
RAIZ_ARQ = ["auto_producer.py", "launch_daemon.py", "stop_auto_producer.py", "CLAUDE.md",
            "LEIA_PRIMEIRO.md", "LEIA_PRODUCAO_AUTOMATICA.md", "requirements.txt"]
CONFIG_ARQ = ["gatilhos_palavras.json", "memes_catalogo.json", "temas.json"]
SECRETS_ARQ = ["omniroute.json"]


def _copia(src, dst, dry, log):
    if dst.exists() and src.read_bytes() == dst.read_bytes():
        return 0
    log.append(f"    {'(simulado) ' if dry else ''}copia {src.relative_to(RAIZ)}")
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return 1


def _junction(link, alvo, dry, log):
    if os.path.isjunction(link) and Path(link).resolve() == Path(alvo).resolve():
        return
    if Path(link).exists() or os.path.isjunction(link):
        antigo = Path(str(link) + "_ANTIGO_" + datetime.now().strftime("%Y%m%d%H%M"))
        log.append(f"    {'(simulado) ' if dry else ''}{link.name} -> renomeado p/ {antigo.name}")
        if not dry:
            os.rename(link, antigo)
    log.append(f"    {'(simulado) ' if dry else ''}junction {link} -> {alvo}")
    if not dry:
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(alvo)], check=True,
                       capture_output=True)


def sincroniza(pista, dry=False):
    p = RAIZ / pista
    log = [f"== {pista} ({p})"]
    if not p.exists():
        log.append("    NAO EXISTE — pulei")
        return log
    n = 0
    for src in sorted((RAIZ / "bin").glob("*.py")):
        # 22/10 (HEF-03): "_" barrava _tg_safe.py e _tts_filter.py (módulos de verdade) — as pistas ficavam com
        # cópias de julho. Agora só backups/rascunhos ficam de fora.
        if not src.name.startswith(("_PRE_", "_ESTAVEL_", "_BACKUP", "_VERSAO_")):
            n += _copia(src, p / "bin" / src.name, dry, log)
    for nome in RAIZ_ARQ:
        if (RAIZ / nome).exists():
            n += _copia(RAIZ / nome, p / nome, dry, log)
    for nome in CONFIG_ARQ:
        if (RAIZ / "config" / nome).exists():
            n += _copia(RAIZ / "config" / nome, p / "config" / nome, dry, log)
    for nome in SECRETS_ARQ:
        if (RAIZ / "secrets" / nome).exists():
            n += _copia(RAIZ / "secrets" / nome, p / "secrets" / nome, dry, log)
    # settings.json: mantem os valores da pista ("pista", cenas...), acrescenta chaves novas
    sr, sp = RAIZ / "config" / "settings.json", p / "config" / "settings.json"
    if sr.exists() and sp.exists():
        r = json.loads(sr.read_text(encoding="utf-8"))
        d = json.loads(sp.read_text(encoding="utf-8"))
        novas = [k for k in r if k not in d]
        if novas:
            log.append(f"    settings.json: +{', '.join(k for k in novas if not k.startswith('_'))}")
            if not dry:
                d.update({k: r[k] for k in novas})
                sp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    # assets compartilhados + pastas padrao do workspace
    ws = p / "workspace"
    if not dry:
        for sub in ("", "narration_cache", "images", "videos", "tmp", "cache", "stories"):
            (ws / sub).mkdir(parents=True, exist_ok=True)
    _junction(ws / "assets", ASSETS, dry, log)
    # junctions mortas viram pastas normais vazias
    if ws.exists():
        for item in ws.iterdir():
            if os.path.isjunction(item) and not item.exists():
                log.append(f"    {'(simulado) ' if dry else ''}junction morta {item.name} -> pasta normal")
                if not dry:
                    os.rmdir(item)       # remove so o link
                    item.mkdir()
    log.append(f"    {n} arquivo(s) atualizado(s)")
    return log


def doctor(pista):
    p = RAIZ / pista
    py = p / "venv" / "Scripts" / "python.exe"
    r = subprocess.run([str(py), str(p / "bin" / "doctor.py")], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"},
                       timeout=300, cwd=str(p))
    linhas = [l for l in r.stdout.splitlines() if "[!]" in l or "[-]" in l or "RESULTADO" in l]
    return linhas or [r.stdout[-300:]]


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    pistas = [a for a in sys.argv[1:] if not a.startswith("--")] or ["prod", "beta", "teste"]
    for pista in pistas:
        print("\n".join(sincroniza(pista, dry)))
        if not dry:
            print("\n".join("    doctor: " + l.strip() for l in doctor(pista)))
