"""alimentar_pc2.py — mantém o PC2 cheio de Shorts entre as rodadas do controlador (30/10/2026, D39; dona: "o PC2 deve
ser nossa máquina mais produtiva... cada segundo ligado o processador deve estar a 100%").

Dado (29/10): o PC2 trabalhou 20 % das 24 h. O controlador dispara 1 Short por rodada e a rodada leva 15–20 min,
porque escolher o vídeo + baixar a fonte/legendas pelo proxy leva 10+ min AQUI; o Short leva ~10 min lá.
Este alimentador faz só isso, fora da rodada: traz os Shorts prontos, e se `ocioso.pc2_vaga_short()` deixa (até 3
juntos, folga de CPU/RAM/disco) dispara mais 1. Mesmas travas do controlador: produção "parceiro" ligada, vez do PC2
(`fila_render.vez(..., maquina="pc2")`), outro despacho em andamento = sai.

    python alimentar_pc2.py       # 1 rodada (tarefa AlimentarPC2, a cada 5 min, pythonw)
Log: logs\\alimentar_pc2.log.
"""
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
LOG = BASE / "logs" / "alimentar_pc2.log"
TRAVA = BASE / "estado" / "alimentar_pc2.lock"


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")
    if LOG.stat().st_size > 2_000_000:
        LOG.write_text(LOG.read_text("utf-8")[-500_000:], "utf-8")


def rodada():
    import controle
    import fila_render
    import ocioso
    ocioso.log = log
    if not controle.ligado("parceiro", "producao")[0] or not controle.ligado("controlador", "producao")[0]:
        return
    cfg = fila_render._cfg()
    rod = fila_render._ler(fila_render._pastas("pc2")[0], cfg.get("max_h", 6))
    if any(d.get("rotulo", "").startswith("disparo") for _p, d in rod):
        return  # o controlador (ou outro alimentador) está despachando pro PC2 agora
    try:
        ocioso._buscar_parceiro_pc2()  # traz os prontos: libera a contagem de Shorts rodando lá
    except Exception as e:  # noqa: BLE001
        log(f"[!] trazer prontos do PC2: {type(e).__name__}: {str(e)[:150]}")
    vaga, motivo = ocioso.pc2_vaga_short()
    if not vaga and "disco" in motivo:
        # 05/11: o PC2 ficou de 04/11 19:33 a 05/11 12:30 sem Short por "disco 7.6 GB" (mín. 8): 454 pastas de trabalho
        # de Shorts JÁ trazidos (13.8 GB) em C:\recapd-e-animes\workspace\anime. Apaga as de mais de 48 h e mede de novo.
        try:
            r = ocioso._ssh('powershell -NoProfile -Command "$lim=(Get-Date).AddHours(-48); '
                            "$v=Get-ChildItem 'C:\\recapd-e-animes\\workspace\\anime' -Directory | "
                            "Where-Object { $_.LastWriteTime -lt $lim }; $v.Count; "
                            '$v | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"', timeout=600)
            log(f"disco do PC2 baixo: apaguei {r.stdout.decode(errors='replace').strip()} pastas de trabalho > 48 h")
            vaga, motivo = ocioso.pc2_vaga_short()
        except Exception as e:  # noqa: BLE001
            log(f"[!] limpar disco do PC2: {type(e).__name__}: {str(e)[:150]}")
    if vaga and len(rod) < int((cfg.get("slots_maquina") or {}).get("pc2", 1)):
        with fila_render.vez("parceiro", "disparo de Short no PC2 (alimentador)", espera_max_h=0.01, maquina="pc2"):
            t0 = time.time()
            if ocioso._disparar_parceiro_pc2():
                log(f"DISPAROU Short no PC2 ({motivo}; preparo {round(time.time() - t0)} s)")
    # 30/10 (D39): com o PC2 ocupado (ou logo depois de disparar), o PC1 já baixa o próximo — o preparo levava
    # 438–793 s com o PC2 parado esperando
    try:
        ocioso.preparar_proximo_pc2()
    except Exception as e:  # noqa: BLE001
        log(f"[!] preparar o próximo: {type(e).__name__}: {str(e)[:150]}")


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import msvcrt
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return
    try:
        rodada()
    except Exception as e:  # noqa: BLE001
        log(f"[!] {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__" and os.name == "nt":
    main()
