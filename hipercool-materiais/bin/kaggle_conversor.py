"""kaggle_conversor.py — leva os pedidos da gpu_fila pro Kaggle (GPU) e traz as narrações convertidas (vídeos grandes).

Plano: D:\\video-fila\\GPU_KAGGLE_VIDEOS_GRANDES.md. Fila: D:\\hipercool-materiais\\gpu_fila (comum\\gpu_fila.py).
Roda com python\\venv (tem o Playwright); a tarefa GpuKaggleFila chama "auto" de 20 em 20 min:
  kaggle_conversor.py auto      com lote: confere/baixa; sem lote: manda os pendentes (espera lote de treino/piloto)
  kaggle_conversor.py enviar    manda já (se não houver outro lote)
  kaggle_conversor.py conferir  confere/baixa já
  kaggle_conversor.py status    mostra o estado
Reaproveita as etapas de página do kaggle_rpa.py (cofre, dataset novo, notebook novo, GPU, Save & Run, baixar) e a
trava do navegador de lá. Pedido que falhar volta pra fila; depois de 2 tentativas vai pra falhas\\ (o projeto que
pediu segue sem o clone: nunca segurar postagem). Última linha impressa: "CONVERSOR: <EVENTO> <info>".
"""
import json
import re
import shutil
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\bin")
sys.path.insert(0, r"D:\hipercool-materiais\comum")
import gpu_fila as gf  # noqa: E402
import kaggle_rpa as kr  # noqa: E402

RAIZ = Path(r"D:\hipercool-materiais")
NOTEBOOK = RAIZ / "amostras_voz" / "kaggle_conversor_rvc.ipynb"
PASTA = RAIZ / "amostras_voz" / "kaggle_conversor"
ESTADO = PASTA / "estado.json"
LOG = PASTA / "conversor.log"
ZIP = PASTA / "pedidos.zip"
PATCH = RAIZ / "tools" / "applio" / "rvc" / "infer" / "pipeline.py"
OUTROS = {"treino": RAIZ / "amostras_voz" / "kaggle" / "estado.json",
          "piloto": RAIZ / "amostras_voz" / "kaggle_piloto" / "estado.json"}
MAX_LOTE_BYTES = 1_500_000_000
CHECAR_MIN = 10
LOTE_MAX_H = 6
MAX_TENTATIVAS = 2
kr.PASTA = PASTA  # prints de erro do Navegador vão pra cá


def log(msg):
    PASTA.mkdir(parents=True, exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        print(linha, flush=True)


def fim(evento, info):
    log(f"CONVERSOR: {evento} {info}")


def ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gravar(est):
    PASTA.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def _outro_lote():
    for nome, arq in OUTROS.items():
        try:
            if json.loads(arq.read_text(encoding="utf-8")).get("lote"):
                return nome
        except (OSError, ValueError):
            continue
    return None


def _job_cfg(pasta):
    return json.loads((pasta / "job.json").read_text(encoding="utf-8"))


def _empacotar(jobs):
    """jobs/<id>/{job.json, entrada.wav} + vozes/<voz>/{.pth,.index} (1 vez por voz) + applio_patch/pipeline.py."""
    vozes = sorted({_job_cfg(gf.PENDENTES / j)["voz"] for j in jobs})
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_STORED) as zf:
        for j in jobs:
            for nome in ("job.json", "entrada.wav"):
                zf.write(gf.PENDENTES / j / nome, f"jobs/{j}/{nome}")
        for v in vozes:
            try:  # 23/10: o .index de voz parada fica no Drive; traz antes de empacotar (bin\vozes_drive.py)
                import vozes_drive
                vozes_drive.garantir(v)
            except Exception as e:  # noqa: BLE001
                print(f"vozes_drive: {e}", flush=True)
            for ext in (".pth", ".index"):
                zf.write(gf.VOZES / v / f"{v}{ext}", f"vozes/{v}/{v}{ext}")
        zf.write(PATCH, "applio_patch/pipeline.py")
    return ZIP, vozes


def _rodar_versao(pg):
    """Igual ao kaggle_rpa.rodar_versao, mas confere o notebook do CONVERSOR (o de lá exige 'Treino RVC')."""
    kr._abrir_barra(pg)
    if "Conversor RVC" not in kr._sumario(pg):
        raise kr.Falha("o editor não está com o notebook do conversor (sumário sem 'Conversor RVC')")
    kr._esperar(pg, lambda: kr._rascunho_salvo(pg), 120, "rascunho não salvou antes da versão")

    def versoes():
        v = re.findall(r"Save Version\s+(\d+)", kr._texto(pg))
        return int(v[0]) if v else -1
    antes = versoes()
    pg.locator("button[aria-label='Save Version']").first.click()
    try:
        pg.get_by_text("Save & Run All (Commit)").first.wait_for(state="visible")
    except Exception:  # noqa: BLE001
        raise kr.Falha("gaveta de versão sem 'Save & Run All (Commit)'") from None
    pg.wait_for_timeout(1500)
    pg.get_by_role("button", name="Save", exact=True).last.click()
    kr._esperar(pg, lambda: versoes() > antes, 180, f"Kaggle não criou a versão (contador continuou em {antes})")
    pg.wait_for_timeout(10000)
    return re.search(r"/code/[^/]+/([^/?]+)", pg.url).group(1)


def enviar(est):
    if est.get("lote"):
        return conferir(est)
    outro = _outro_lote()
    if outro:
        return fim("ESPERA", f"lote do {outro} rodando no Kaggle (1 sessão de GPU por vez)")
    gf.PENDENTES.mkdir(parents=True, exist_ok=True)
    jobs, total = [], 0
    for p in sorted(gf.PENDENTES.iterdir()):
        if not (p / "job.json").exists() or not (p / "entrada.wav").exists():
            continue
        tam = (p / "entrada.wav").stat().st_size
        if jobs and total + tam > MAX_LOTE_BYTES:
            break
        jobs.append(p.name)
        total += tam
    if not jobs:
        return fim("NADA", "nenhum pedido na fila")
    zip_, vozes = _empacotar([j for j in jobs])
    marca = datetime.now().strftime("%Y%m%d %H%M")
    log(f"enviando {len(jobs)} pedido(s) ({', '.join(vozes)}), {zip_.stat().st_size / 1e6:.0f} MB")
    with kr.Navegador() as pg:
        url_ds = kr.criar_dataset(pg, zip_, f"conversor {marca}")
        kr.novo_notebook(pg, NOTEBOOK, f"conversor rvc {marca}", marca="Conversor RVC")
        kr.adicionar_dataset(pg, url_ds)
        kr.internet_ligada(pg)
        aviso = kr.acelerador(pg, "GPU T4 x2")
        nb = _rodar_versao(pg)
    horas = re.search(r"You have ([\d.]+) hours? remaining", aviso or "")
    gf.ENVIADOS.mkdir(parents=True, exist_ok=True)
    for j in jobs:
        shutil.move(str(gf.PENDENTES / j), str(gf.ENVIADOS / j))
    est["lote"] = {"notebook": nb, "dataset": url_ds, "jobs": jobs, "enviado": datetime.now().isoformat(timespec="minutes"),
                   "checado": time.time()}
    if horas:
        est["gpu"] = f"{horas.group(1)} h de GPU restantes na semana (visto em {datetime.now():%d/%m %H:%M}, antes deste lote)"
    gravar(est)
    fim("ENVIADO", f"{len(jobs)} pedido(s) -> kaggle.com/code/{kr.USUARIO}/{nb}")


def _devolver(job, motivo):
    """Pedido sem resultado: volta pra fila (nova tentativa) ou vai pra falhas\\ depois de MAX_TENTATIVAS."""
    pasta = gf.ENVIADOS / job
    if not pasta.exists():
        return
    cfg = _job_cfg(pasta)
    cfg["tentativas"] = cfg.get("tentativas", 0) + 1
    cfg.setdefault("historico", []).append(f"{datetime.now():%d/%m %H:%M} {motivo[:200]}")
    destino = gf.FALHAS if cfg["tentativas"] >= MAX_TENTATIVAS else gf.PENDENTES
    if destino is gf.FALHAS:
        cfg["falha"] = motivo[:300]
    (pasta / "job.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    destino.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pasta), str(destino / job))


def conferir(est, forcar=False):
    lote = est.get("lote")
    if not lote:
        return fim("NADA", "nenhum lote do conversor no Kaggle")
    idade_h = (time.time() - datetime.fromisoformat(lote["enviado"]).timestamp()) / 3600
    if not forcar and time.time() - lote.get("checado", 0) < CHECAR_MIN * 60:
        return fim("RODANDO", f"{lote['notebook']} (próxima conferida em até {CHECAR_MIN} min)")
    lote["checado"] = time.time()
    gravar(est)
    nb = lote["notebook"]
    with kr.Navegador() as pg:
        sit = kr.situacao(pg, nb)
        if sit == "rodando" and idade_h < LOTE_MAX_H:
            return fim("RODANDO", f"{nb} ainda rodando ({idade_h * 60:.0f} min)")
        resumo = kr.ler_resumo(pg, nb) if sit == "terminou" else []
        zip_ = None
        try:
            if sit == "sem versao":
                raise kr.SemSaida("o notebook ficou sem versão rodando (o Save Version não pegou)")
            if sit == "rodando":
                raise kr.SemSaida(f"rodando há mais de {LOTE_MAX_H} h: desisti deste lote")
            zip_ = kr.baixar_saida(pg, nb, "saidas.zip", PASTA / nb)
        except kr.SemSaida as e:
            for j in lote["jobs"]:
                _devolver(j, f"lote {nb}: {e}")
            est.setdefault("historico", []).append({**lote, "terminado": datetime.now().isoformat(timespec="minutes"),
                                                    "prontos": [], "erro": str(e), "resumo": resumo})
            est.pop("lote")
            gravar(est)
            return fim("FALHOU", f"{nb}: {e}")
    prontos = []
    with zipfile.ZipFile(zip_) as zf:
        nomes = set(zf.namelist())
        texto = zf.read("RESUMO.txt").decode("utf-8", "replace") if "RESUMO.txt" in nomes else "\n".join(resumo)
        linha = {l.split(":", 1)[0]: l.split(":", 1)[1].strip() for l in texto.splitlines() if ":" in l}
        for j in lote["jobs"]:
            if f"{j}.wav" in nomes and (gf.ENVIADOS / j).exists():
                pasta = gf.ENVIADOS / j
                with zf.open(f"{j}.wav") as src, open(pasta / "saida.wav", "wb") as out:
                    shutil.copyfileobj(src, out)
                cfg = _job_cfg(pasta)
                cfg.update(pronto_em=datetime.now().isoformat(timespec="seconds"), resumo=linha.get(j, ""), notebook=nb)
                (pasta / "job.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
                gf.PRONTOS.mkdir(parents=True, exist_ok=True)
                shutil.move(str(pasta), str(gf.PRONTOS / j))
                prontos.append(j)
            else:
                _devolver(j, f"lote {nb}: sem saída ({linha.get(j, 'sem linha no RESUMO')})")
    est.setdefault("historico", []).append({**lote, "terminado": datetime.now().isoformat(timespec="minutes"),
                                            "prontos": prontos, "resumo": texto.splitlines()[:40]})
    est.pop("lote")
    gravar(est)
    fim("BAIXADO", f"{len(prontos)} de {len(lote['jobs'])} pedido(s) prontos ({nb})")


def status(est):
    def conta(p):
        return sum(1 for x in p.iterdir() if x.is_dir()) if p.exists() else 0
    linhas = [f"pendentes {conta(gf.PENDENTES)} | enviados {conta(gf.ENVIADOS)} | prontos {conta(gf.PRONTOS)} | "
              f"falhas {conta(gf.FALHAS)}", f"lote: {est.get('lote', {}).get('notebook', 'nenhum')}",
              f"GPU: {est.get('gpu', 'ainda não lida')}", f"outro lote no Kaggle: {_outro_lote() or 'nenhum'}"]
    print("\n".join(linhas))


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    estado = ler()
    try:
        if cmd == "auto":  # fila vazia e sem lote: sai calado (a tarefa roda de 20 em 20 min)
            if estado.get("lote"):
                conferir(estado)
            elif any((p / "job.json").exists() for p in gf.PENDENTES.glob("*")):
                enviar(estado)
        elif cmd == "enviar":
            enviar(estado)
        elif cmd == "conferir":
            conferir(estado, forcar=True)
        elif cmd == "status":
            status(estado)
        else:
            sys.exit(__doc__)
    except Exception as e:  # noqa: BLE001
        fim("FALHOU", f"{type(e).__name__}: {e}"[:400])
        sys.exit(2)
