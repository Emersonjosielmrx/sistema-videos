"""Gera amostras_voz\\kaggle_conversor_rvc.ipynb: converte na GPU do Kaggle as narrações da gpu_fila (vídeos grandes).
Plano: D:\\video-fila\\GPU_KAGGLE_VIDEOS_GRANDES.md. Rodar de novo depois de mudar este arquivo."""
import json
from pathlib import Path

SAIDA = Path(r"D:\hipercool-materiais\amostras_voz\kaggle_conversor_rvc.ipynb")

MD = """# Conversor RVC (Applio) — vozes clonadas dos vídeos grandes na GPU

Converte as narrações da fila (`jobs/<id>/job.json` + `entrada.wav`) com o timbre do narrador
(`vozes/<voz>/<voz>.pth + .index`), com o MESMO Applio do PC (commit 5379cf2) e o NOSSO `rvc/infer/pipeline.py`
(`applio_patch/`: APPLIO_F0_ESCALA e APPLIO_F0_FINAL_ST), pra sair igual à produção.

**Antes de rodar:** Accelerator **GPU T4 x2**, Internet **On**, Add Input: o dataset do lote.
**Resultado (aba Output):** `saidas.zip` (`<id>.wav` de cada pedido) e `RESUMO.txt` (`<id>: OK (...)` ou `<id>: FALHOU: ...`).
"""

C1 = """# 1. Applio na mesma versão do PC (commit de 17/10/2026), fora de /kaggle/working para não virar saída
!rm -rf /tmp/applio && mkdir -p /tmp/applio
!cd /tmp/applio && git init -q && git remote add origin https://github.com/IAHispano/Applio.git && git fetch -q --depth 1 origin 5379cf261fa7d8085c3b077aa42dabca7c85310b && git checkout -q FETCH_HEAD
%pip install -q -r /tmp/applio/requirements-engine.txt
"""

C2 = r"""# 2. Nosso pipeline.py, modelos base (contentvec + rmvpe) e a lista de pedidos
# Nada de numpy/librosa no kernel: o %pip da célula 1 troca o numpy no disco; cada conversão roda em processo próprio.
import json, os, shutil, subprocess, sys, time, zipfile
from pathlib import Path

APPLIO = Path("/tmp/applio")
os.chdir(APPLIO)
sys.path.insert(0, str(APPLIO))
import torch
assert torch.cuda.is_available(), "Sem GPU: Settings > Accelerator > GPU T4 x2"
ENTRADA = Path("/kaggle/input")
patch = next(ENTRADA.rglob("applio_patch/pipeline.py"), None)
if patch:
    shutil.copyfile(patch, APPLIO / "rvc" / "infer" / "pipeline.py")
    print("pipeline.py nosso aplicado (APPLIO_F0_ESCALA / APPLIO_F0_FINAL_ST)")
from core import run_prerequisites_script
print(run_prerequisites_script(pretraineds_hifigan=False, models=True, exe=False))
jobs = sorted(ENTRADA.rglob("jobs/*/job.json"))
assert jobs, "Dataset sem jobs/<id>/job.json"
print(f"{len(jobs)} pedido(s)")
"""

C3 = r"""# 3. Converte cada pedido (fcpe como no PC; se falhar, rmvpe). Zip e RESUMO refeitos a cada pedido.
SAIDA = Path("/kaggle/working/saidas")
SAIDA.mkdir(parents=True, exist_ok=True)
ZIP, RESUMO = Path("/kaggle/working/saidas.zip"), Path("/kaggle/working/RESUMO.txt")
resumo = {}


def empacotar():
    texto = "\n".join(f"{k}: {v}" for k, v in resumo.items()) + "\n"
    RESUMO.write_text(texto)
    with zipfile.ZipFile(ZIP, "w") as zf:
        for f in sorted(SAIDA.glob("*.wav")):
            zf.write(f, f.name)
        zf.writestr("RESUMO.txt", texto)


for jj in jobs:
    cfg = json.loads(jj.read_text())
    job, voz = jj.parent.name, cfg["voz"]
    saida = SAIDA / f"{job}.wav"
    t0 = time.time()
    try:
        modelo = next(ENTRADA.rglob(f"vozes/{voz}/{voz}.pth"))
        indice = next(ENTRADA.rglob(f"vozes/{voz}/{voz}.index"))
        amb = dict(os.environ, APPLIO_F0_ESCALA=str(cfg.get("f0_escala", 1)), APPLIO_F0_FINAL_ST=str(cfg.get("final_st", 0)))
        cmd = [sys.executable, "core.py", "infer", "--input-path", str(jj.parent / "entrada.wav"), "--output-path", str(saida),
               "--pth-path", str(modelo), "--index-path", str(indice), "--pitch", str(int(cfg.get("tom", 0))),
               "--index-rate", str(cfg.get("index_rate", 0.38)), "--protect", str(cfg.get("protect", 0.38)),
               "--volume-envelope", str(cfg.get("volume_envelope", 0.75)), "--export-format", "WAV",
               "--embedder-model", "contentvec", "--split-audio"]
        if cfg.get("formant"):
            cmd += ["--formant-shifting", "--formant-qfrency", str(cfg["formant"]["q"]), "--formant-timbre", str(cfg["formant"]["t"])]
        usado = None
        for metodo in ("fcpe", "rmvpe"):
            r = subprocess.run(cmd + ["--f0-method", metodo], cwd=APPLIO, env=amb, capture_output=True, text=True)
            if r.returncode == 0 and saida.exists() and saida.stat().st_size > 10_000:
                usado = metodo
                break
            print(f"  {job}: {metodo} falhou: {(r.stderr or r.stdout)[-400:]}", flush=True)
        if not usado:
            raise RuntimeError("nenhum método gerou saída")
        resumo[job] = f"OK ({usado}, {time.time() - t0:.0f} s)"
    except Exception as e:  # noqa: BLE001
        resumo[job] = f"FALHOU: {str(e)[:200]}"
    print(f"{job}: {resumo[job]}", flush=True)
    empacotar()
print("FIM")
"""


def celula(tipo, texto):
    c = {"cell_type": tipo, "metadata": {}, "source": texto.splitlines(keepends=True)}
    if tipo == "code":
        c.update(execution_count=None, outputs=[])
    return c


nb = {"cells": [celula("markdown", MD), celula("code", C1), celula("code", C2), celula("code", C3)],
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 4}
SAIDA.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] == "code":
        linhas = ["#" + l if l.lstrip().startswith(("!", "%")) else l for l in "".join(c["source"]).splitlines()]
        compile("\n".join(linhas), f"celula{i}", "exec")
print("gravado e compila:", SAIDA)
