"""02/11 dona: "usar o Kaggle pra produzir em LOTES os Shorts de corte (parceiros) e os cortes dos longos — um só não
compensa, lote sim — e liberar RAM/CPU daqui pros Veo 3".

O PC1 (anime_auto.fazer_short com SHORTS_NO_KAGGLE=1) faz o leve: baixa (yt-dlp só pelo IP da casa), reedita o
parceiro, escreve o roteiro e escolhe a voz. A RENDERIZAÇÃO (anime-pipeline.py --formato short: TTS, voz clonada,
clipes, legenda MIX/cartões/efeitos) vai pra fila_shorts no Drive; a linha paralela do kaggle_trabalhador (a mesma dos
Shorts de comentários) pega em lote enquanto o longo renderiza na GPU, e devolve o vídeo. Aqui espera e baixa.
Sem resposta no prazo (SHORTS_KAGGLE_ESPERA_MIN, 90) = desiste e o anime_auto renderiza aqui como antes."""
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe" if os.name == "nt" else "rclone"
FILA = "manhwa-drive:colab_recap/fila_shorts"
# envs do pipeline que mudam o Short (variantes T3-T11, voz clonada, parceiro...) — vão junto pro Kaggle
_ENV_PREFIXOS = ("VOZ_CLONADA", "CORTES_", "PARCEIRO_", "ANIME_", "NICHO_CLONE", "TEXTO_VIDEO_")


def _rc(*a, timeout=900):
    r = subprocess.run([RCLONE, *a], capture_output=True, text=True, timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0:
        raise RuntimeError(f"rclone {a[0]}: {r.stderr[-300:]}")
    return r.stdout


VOZES_PC = Path(r"D:\hipercool-materiais\models\rvc\vozes")


def _garantir_voz_no_drive(nome):
    """03/11: 27 das 101 vozes não estavam no cache colab_recap/vozes — o Kaggle baixava nada e o Short morria em
    'No such file … vozes/<voz>.pth' (testes de 02/11 e 03/11). Falta lá = sobe daqui antes do pedido."""
    try:
        if f"{nome}.pth" in _rc("lsf", f"manhwa-drive:colab_recap/vozes/{nome}", timeout=180).split():
            return
    except (RuntimeError, subprocess.TimeoutExpired):
        pass  # pasta não existe (ou Drive lento): sobe
    if (VOZES_PC / nome / f"{nome}.pth").exists():
        logging.info(f"[kaggle-lote] voz {nome} não está no cache do Drive — subindo")
        _rc("copy", str(VOZES_PC / nome), f"manhwa-drive:colab_recap/vozes/{nome}", "--exclude", ".ultimo_uso",
            "--exclude", "*.bkp*", timeout=1800)


STATUS_CENTRAL = "https://produtos.opus-sem-limites.com.br/recap-5a857ed863/status.json"
POOL = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")


def _curto_rodando():
    """10/11: com 0 conta de papel curto/duplo no ar (curtas banidas), o Short ia pra fila e esperava 90 min à toa;
    um longo pegava 6 h depois, o PC já tinha desistido (ou o processo morrido) -> 33 Shorts prontos ÓRFÃOS no Drive
    e o PC fazendo 1 Short a cada ~2 h. Só usa o lote se o status público da central mostra uma conta curto/duplo
    rodando. Falha de leitura = None (decide o chamador). SHORTS_KAGGLE_SEM_CURTO=1 manda mesmo assim."""
    try:
        import urllib.request
        st = json.loads(urllib.request.urlopen(STATUS_CENTRAL, timeout=20).read().decode("utf-8"))
        papel = {c.get("username"): c.get("papel") for c in json.loads(POOL.read_text("utf-8"))["contas"]}
        vivas = [g["conta"] for g in st.get("gpus") or [] if g.get("conta") and g.get("status") in ("rodando", "lançado")]
        return any(papel.get(c) in ("curto", "duplo") for c in vivas)
    except Exception:  # noqa: BLE001
        return None


def renderizar(work, video, roteiro, cand, short_kind, env, vf):
    """Manda o pedido, espera o Kaggle e baixa o vídeo pra vf. True = vf pronto."""
    if os.environ.get("SHORTS_KAGGLE_SEM_CURTO") != "1" and _curto_rodando() is False:
        logging.info("[kaggle-lote] nenhuma conta de curto rodando no Kaggle — renderizo no PC agora (sem esperar 90 min)")
        return False
    work = Path(work)
    pid = f"{datetime.now():%Y%m%d_%H%M%S}_{str(cand.get('id', 'x'))[:11]}"
    pasta = work / "_kaggle"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir()
    shutil.copy2(video, pasta / "source.mp4")
    shutil.copy2(roteiro, pasta / "roteiro.txt")
    for extra in ("roteiro_tempos.json", "roteiro_falas.json", "roteiro_narrador.txt", "_impactos.json",
                  "legenda_tempos.json"):
        if (work / extra).exists():
            shutil.copy2(work / extra, pasta / extra)
    envs = {k: v for k, v in env.items() if k.startswith(_ENV_PREFIXOS)}
    envs.pop("VOZ_CLONADA_RESUMO", None)  # caminho do PC
    voz = envs.get("VOZ_CLONADA")
    pedido = {"titulo": cand.get("title", ""), "short_kind": short_kind, "env": envs,
              "vozes": [Path(voz).name] if voz else [], "enviado": datetime.now().isoformat(timespec="seconds")}
    if voz:
        envs["VOZ_CLONADA"] = Path(voz).name  # no Kaggle a voz fica em models/rvc/vozes/<nome>
        _garantir_voz_no_drive(Path(voz).name)
    (pasta / "pedido.json").write_text(json.dumps(pedido, ensure_ascii=False, indent=1), encoding="utf-8")
    _rc("copy", str(pasta), f"{FILA}/{pid}", timeout=1800)
    logging.info(f"[kaggle-lote] Short {pid} na fila_shorts — esperando o Kaggle")
    t0 = time.time()
    prazo = t0 + float(os.environ.get("SHORTS_KAGGLE_ESPERA_MIN", "90")) * 60
    # 12/11 (auditoria): 3 Shorts hoje esperaram os 90 min INTEIROS (≈270 min do PC1 parado) porque nenhuma GPU pegou
    # o pedido (fila atrás de longos). Agora: se em SHORTS_KAGGLE_PEGAR_MIN (25) nenhuma GPU começou (sem
    # "em_andamento"), desiste e renderiza no PC; se uma GPU JÁ pegou, espera até os 90 como antes (crédito gasto).
    pegar_s = float(os.environ.get("SHORTS_KAGGLE_PEGAR_MIN", "25")) * 60
    pegou = False
    while time.time() < prazo:
        time.sleep(60)
        try:
            nomes = set(_rc("lsf", f"{FILA}/{pid}", timeout=120).split())
        except (RuntimeError, subprocess.TimeoutExpired):  # 02/11: 1 travada do Drive desistia do Kaggle na hora
            continue
        pegou = pegou or any(n.startswith("em_andamento") and "SEGURADO" not in n for n in nomes)
        if not pegou and time.time() - t0 > pegar_s and "pronto.json" not in nomes:
            logging.info(f"[kaggle-lote] {pid}: nenhuma GPU pegou em {pegar_s / 60:.0f} min — renderizo no PC")
            break
        if "pronto.json" in nomes and "video.mp4" in nomes:
            _rc("copyto", f"{FILA}/{pid}/video.mp4", str(vf), timeout=1800)
            for extra in ("marcas_visuais.json", "_testes_usados.json"):
                if extra in nomes:
                    _rc("copyto", f"{FILA}/{pid}/{extra}", str(work / extra), timeout=300)
            _rc("purge", f"{FILA}/{pid}", timeout=300)
            shutil.rmtree(pasta, ignore_errors=True)
            return vf.exists() and vf.stat().st_size > 300_000
        if "erro.json" in nomes:
            logging.warning(f"[kaggle-lote] {pid} deu erro no Kaggle: {_rc('cat', f'{FILA}/{pid}/erro.json')[:400]}")
            break
    # desistiu: tira da fila (se ainda ninguém pegou) pra não renderizar 2x. 02/11: tenta 3x — com o Drive lento a
    # pasta ficava na fila e uma GPU nova renderizava o mesmo Short que o PC já fazia
    for _ in range(3):
        try:
            nomes = set(_rc("lsf", f"{FILA}/{pid}", timeout=120).split())
            if not any(n.startswith("em_andamento") for n in nomes):
                _rc("purge", f"{FILA}/{pid}", timeout=300)
            break
        except (RuntimeError, subprocess.TimeoutExpired):
            time.sleep(30)
    shutil.rmtree(pasta, ignore_errors=True)
    return False
