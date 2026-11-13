"""gpu_fila.py — fila de conversões de voz clonada na GPU do Kaggle, pros vídeos GRANDES (dono 22/10).

Na CPU do PC1 a voz clonada leva 2-19x a duração do áudio; no Kaggle são minutos (plano:
D:\\video-fila\\GPU_KAGGLE_VIDEOS_GRANDES.md). Só biblioteca padrão: qualquer venv importa.

    sys.path.append(r"D:\\hipercool-materiais\\comum"); import gpu_fila
    job = gpu_fila.pedir("porao", r"...\\narracao.wav", origem="hipercool cap12", tom=-10, f0_escala=1.28)
    gpu_fila.estado(job)          # "pendente" | "enviado" | "pronto" | "falhou" | "sumiu"
    gpu_fila.saida(job)           # Path do wav convertido quando "pronto", senão None
    gpu_fila.esperar(job, 3600)   # espera até 1 h; None = não veio (o projeto segue como hoje: nunca segurar)

Quem manda pro Kaggle e traz de volta: D:\\hipercool-materiais\\bin\\kaggle_conversor.py (tarefa GpuKaggleFila).
Parâmetros iguais aos do voz_clonada.lote: tom, index_rate, protect, volume_envelope, f0_escala, final_st,
formant ({"q": , "t": } ou None). EQ fica no PC (ffmpeg) depois da conversão.
"""
import json
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais\gpu_fila")
PENDENTES, ENVIADOS, PRONTOS, FALHAS = (RAIZ / n for n in ("pendentes", "enviados", "prontos", "falhas"))
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
PADRAO = {"tom": 0, "index_rate": 0.38, "protect": 0.38, "volume_envelope": 0.75, "f0_escala": 1.0, "final_st": 0.0,
          "formant": None}


def pedir(voz, entrada, origem="", **params):
    """Copia a narração pra fila e devolve o id do pedido. O tom padrão é 0: passe o tom da base (tom_fixo)."""
    if not (VOZES / voz / f"{voz}.pth").exists():
        raise ValueError(f"voz '{voz}' sem modelo em {VOZES}")
    entrada = Path(entrada)
    if entrada.suffix.lower() != ".wav" or not entrada.is_file():
        raise ValueError(f"entrada tem que ser um .wav que existe: {entrada}")
    job = f"{datetime.now():%Y%m%d_%H%M%S}_{voz}_{uuid.uuid4().hex[:6]}"
    pasta = PENDENTES / job
    pasta.mkdir(parents=True)
    shutil.copyfile(entrada, pasta / "entrada.wav")
    cfg = {**PADRAO, **params, "voz": voz, "origem": origem, "pedido_em": datetime.now().isoformat(timespec="seconds"),
           "entrada_original": str(entrada)}
    (pasta / "job.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    return job


def estado(job):
    for nome, pasta in (("pronto", PRONTOS), ("falhou", FALHAS), ("enviado", ENVIADOS), ("pendente", PENDENTES)):
        if (pasta / job).exists():
            return nome
    return "sumiu"


def saida(job):
    p = PRONTOS / job / "saida.wav"
    return p if p.exists() else None


def motivo(job):
    try:
        return json.loads((FALHAS / job / "job.json").read_text(encoding="utf-8")).get("falha")
    except (OSError, ValueError):
        return None


def esperar(job, segundos, intervalo=60):
    fim = time.time() + segundos
    while time.time() < fim:
        e = estado(job)
        if e == "pronto":
            return saida(job)
        if e in ("falhou", "sumiu"):
            return None
        time.sleep(intervalo)
    return None
