r"""redistribuir.py — passa Shorts PRONTOS de parceiro presos em canal REMOVIDO/TRAVADO para um canal VIVO do mesmo
assunto, trocando a @ gravada no vídeo (remarcar.py). Dona 19/11: "temos muitos vídeos sobrando e poucos canais" —
526 prontos presos em 13 canais removidos 17-18/11.

    python redistribuir.py                 # simula: mostra o que iria pra onde
    python redistribuir.py --executar      # faz um lote (padrão 12 vídeos)
    opções: --lote N, --teto 30 (estoque de prontos por canal vivo depois do lote), --maquina sti

Fluxo de um lote: baixa do Drive (rclone, _NO_DRIVE.txt) -> mede a @ antiga no PC1 (leve: 24 quadros) -> sobe os
vídeos + PNGs pro STI num scp, roda TODOS os ffmpeg num ssh só (regra: sem rajada), traz de volta num scp -> troca o
video.mp4 e grava no postar.json: canal novo, "canal_original", "remarcado". O original continua no Drive.
Recusa (sem mexer): @ não achada, caixa fora do centro, fonte já usada no canal de destino (vídeo único por canal).

Desliga: REMARCAR_LIGADO=0 (ou apague o lote do agendador). Desfazer 1 item: no postar.json, canal = canal_original,
apagar video.mp4 e recriar _NO_DRIVE.txt com remarcado.drive (volta a ser o do canal removido, que não posta).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(1, r"D:\recapd-ambientes\producao\bin")
import parceiro_diario as pd  # noqa: E402

RCLONE = r"D:\tools\rclone.exe"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
NO_WIN = 0x08000000
LOG = AQUI / "redistribuir.log"
TRAB = Path(r"D:\tmp\remarcar\lote")

# canal removido -> canais vivos do mesmo assunto (o de menor estoque recebe primeiro)
MAPA = {
    "novo_esportenoturno": ["novo_curiosidadesnoturnas", "novo_inovareq8l"],
    "novo_bichonoturno": ["novo_curiosidadesnoturnas", "novo_inovareq8l"],
    "novo_mundoquenaoexiste": ["novo_inovareq8l", "novo_curiosidadesnoturnas"],
    "novo_ia_agora_h3n": ["novo_forjareact", "novo_inovareu8b"],
    "novo_cartuchoreact": ["novo_inovareu8b", "novo_forjareact"],
    "novo_gamenoturno": ["novo_inovareu8b", "novo_forjareact"],
    "novo_dicasfinanceirasdaia": ["novo_bilionarionoturno", "novo_historias_em_frames", "novo_codigo_inteligente_n7j"],
    "novo_doramanoturno": ["novo_historias_em_frames", "novo_codigo_inteligente_n7j"],
    "novo_manhwanoturno": ["novo_animenoturno", "hNQrW5ouNe0Ni5Me"],
    "novo_manhwareact_ia": ["novo_animenoturno", "hNQrW5ouNe0Ni5Me"],
    "KOpyXE9rBy1YirlZ": ["novo_animenoturno", "hNQrW5ouNe0Ni5Me"],
}


def log(m):
    linha = f"{time.strftime('%d/%m %H:%M:%S')} {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


RECUSAS = AQUI / "recusas.json"  # {pasta: nº de recusas} — 2 recusas = não tenta mais (REMARCAR_RETENTA=1 ignora)


def _recusas():
    try:
        return json.loads(RECUSAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _recusou(pasta):
    r = _recusas()
    r[pasta] = r.get(pasta, 0) + 1
    RECUSAS.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")


def planejar(lote, teto):
    rec = {} if os.environ.get("REMARCAR_RETENTA") == "1" else _recusas()
    c = json.loads(pd.CFG.read_text(encoding="utf-8"))
    trav = pd._canais_travados(c)
    handle = {d["canal"]: d.get("handle") for d in c["pt"]}
    its = pd.itens(c)
    estoque = Counter(x["canal"] for x in its if x["estado"] == "pronto")
    fontes = {}
    for x in its:
        fontes.setdefault(x["canal"], set()).add(x["fonte"])
    plano = []
    # mais antigos primeiro, alternando os canais removidos pra não esvaziar um só
    por_morto = {}
    for x in its:
        if (x["estado"] == "pronto" and x["canal"] in MAPA and x["canal"] in trav and x["lang"] == "pt"
                and rec.get(x["pj"].parent.name, 0) < 2):
            por_morto.setdefault(x["canal"], []).append(x)
    fila = []
    while any(por_morto.values()):
        for k in list(por_morto):
            if por_morto[k]:
                fila.append(por_morto[k].pop(0))
    for x in fila:
        if len(plano) >= lote:
            break
        alvos = [a for a in MAPA[x["canal"]] if a not in trav and estoque[a] < teto and x["fonte"] not in fontes.get(a, ())]
        if not alvos:
            continue
        a = min(alvos, key=lambda k: estoque[k])
        estoque[a] += 1
        fontes.setdefault(a, set()).add(x["fonte"])
        plano.append({"x": x, "de": x["canal"], "para": a, "antigo": handle.get(x["canal"]) or "", "novo": handle[a]})
    return plano, estoque


def executar(plano, maquina):
    if TRAB.exists():
        shutil.rmtree(TRAB, ignore_errors=True)
    TRAB.mkdir(parents=True)
    prontos = []
    for i, p in enumerate(plano):
        x = p["x"]
        nome = f"v{i:02d}"
        ent = TRAB / f"{nome}.mp4"
        if x["mp4"].exists():
            shutil.copy2(x["mp4"], ent)
            drive = ""
        else:
            nd = x["pj"].parent / "_NO_DRIVE.txt"
            if not nd.exists():
                log(f"PULA {x['pj'].parent.name}: sem vídeo e sem _NO_DRIVE.txt")
                continue
            drive = nd.read_text(encoding="utf-8").strip()
            # 19/11: um download travou 15 min e o TimeoutExpired derrubava o lote inteiro — agora só pula este
            try:
                subprocess.run([RCLONE, "copyto", drive, str(ent), "--retries", "3", "--timeout", "2m",
                                "--contimeout", "60s"], capture_output=True, timeout=600, creationflags=NO_WIN)
            except subprocess.TimeoutExpired:
                log(f"PULA {x['pj'].parent.name}: download do Drive travou")
                ent.unlink(missing_ok=True)
                continue
            if not ent.exists():
                log(f"PULA {x['pj'].parent.name}: não baixou do Drive")
                continue
        p.update(nome=nome, drive=drive)
        prontos.append(p)
    if not prontos:
        log("lote vazio (nada baixou)")
        return 0
    # 19/11: medir + render TUDO no STI (o commit do PC1 zerou com voz_clonada/anime-pipeline e o cv2 nem carregava).
    # Um script só, uma conexão só (regra: sem rajada). Cada linha devolve "R vNN {json do remarcar.py}".
    sh = ["set -u", "cd ~/remarcar", "rm -f *_ok.mp4", "export REMARCAR_FFMPEG=$HOME/bin/ffmpeg"]
    for p in prontos:
        n = p["nome"]
        sh.append(f"echo R {n} $(venv/bin/python remarcar.py {n}.mp4 {n}_ok.mp4 '{p['novo']}' "
                  f"--antigo '{p['antigo']}' 2>/dev/null | tail -1)")
    (TRAB / "lote.sh").write_text("\n".join(sh) + "\n", encoding="utf-8", newline="\n")
    arquivos = [str(TRAB / "lote.sh"), str(AQUI / "remarcar.py")] + [str(TRAB / f"{p['nome']}.mp4") for p in prontos]
    subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", maquina,
                    "mkdir -p ~/remarcar && rm -f ~/remarcar/v*.mp4 ~/remarcar/*.png"], capture_output=True, timeout=60)
    t0 = time.time()
    for _t in range(3):  # 19/11: scp 255 (queda de conexão) derrubava o lote inteiro — tenta 3x
        if subprocess.run([SCP, "-q", "-o", "ConnectTimeout=30"] + arquivos + [f"{maquina}:remarcar/"],
                          timeout=3600).returncode == 0:
            break
        log(f"scp pro {maquina} falhou (tentativa {_t + 1}/3)")
        time.sleep(60)
    else:
        raise RuntimeError(f"não consegui mandar o lote pro {maquina}")
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", maquina, "bash ~/remarcar/lote.sh"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=7200)
    feitos = set()
    for ln in (r.stdout or "").splitlines():
        if not ln.startswith("R "):
            continue
        _, n, *resto = ln.split(" ", 2)
        try:
            j = json.loads(resto[0]) if resto else {}
        except ValueError:
            j = {"ok": False, "motivo": resto[0][:200] if resto else "sem saída"}
        p = next(q for q in prontos if q["nome"] == n)
        if j.get("ok"):
            feitos.add(n)
            p["caixa"] = j.get("caixa")
        else:
            log(f"RECUSA {p['x']['pj'].parent.name} ({p['de']}): {j.get('motivo') or 'sem saída do remarcar'}")
            _recusou(p["x"]["pj"].parent.name)
    for n in sorted(feitos):  # 1 arquivo por scp (vários remotos num scp só traziam só o 1º)
        subprocess.run([SCP, "-q", f"{maquina}:remarcar/{n}_ok.mp4", str(TRAB)], timeout=1800)
    log(f"render em {maquina}: {len(feitos)}/{len(prontos)} em {time.time() - t0:.0f} s")
    n_ok = 0
    for p in prontos:
        saida = TRAB / f"{p['nome']}_ok.mp4"
        x = p["x"]
        if p["nome"] not in feitos or not saida.exists() or saida.stat().st_size < 100_000:
            log(f"FALHOU render {x['pj'].parent.name}")
            continue
        d = json.loads(x["pj"].read_text(encoding="utf-8"))
        if d.get("canal") != p["de"] or pd._estado(d) != "pronto":
            log(f"PULA {x['pj'].parent.name}: mudou enquanto renderizava")
            continue
        shutil.move(str(saida), str(x["mp4"]))
        d["canal_original"] = p["de"]
        d["canal"] = p["para"]
        d["remarcado"] = {"em": time.strftime("%Y-%m-%dT%H:%M:%S"), "de": p["antigo"], "para": p["novo"],
                          "caixa": p["caixa"], "drive": p["drive"], "por": "video-fila/remarcar/redistribuir.py"}
        tmp = x["pj"].with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        os.replace(tmp, x["pj"])
        (x["pj"].parent / "_NO_DRIVE.txt").unlink(missing_ok=True)
        n_ok += 1
        log(f"OK {x['pj'].parent.name}: {p['antigo']} -> {p['novo']} ({p['para']})")
    shutil.rmtree(TRAB, ignore_errors=True)
    return n_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--executar", action="store_true")
    ap.add_argument("--lote", type=int, default=12)
    ap.add_argument("--teto", type=int, default=30)
    ap.add_argument("--maquina", default="sti")
    a = ap.parse_args()
    if os.environ.get("REMARCAR_LIGADO", "1") == "0":
        print("desligado (REMARCAR_LIGADO=0)")
        return 0
    plano, est = planejar(a.lote, a.teto)
    for p in plano:
        print(f"{p['x']['pj'].parent.name[:45]:45} {p['antigo']:24} -> {p['novo']}")
    print("estoque depois:", {k: v for k, v in est.items() if k in {b for l in MAPA.values() for b in l}})
    if not a.executar or not plano:
        return 0
    n = executar(plano, a.maquina)
    log(f"lote: {n}/{len(plano)} redistribuídos")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — pela tarefa agendada não há console: o erro vai pro log
        import traceback
        log("ERRO: " + traceback.format_exc()[-1500:])
        sys.exit(1)
