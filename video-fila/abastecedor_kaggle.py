"""abastecedor_kaggle.py — mantém as linhas de curto do Kaggle sempre com trabalho (tarefa AbastecedorKaggle, 10 em 10 min).

03/11 dona: "a ideia é deixar cada fila do Kaggle rodando 24 h por dia, cada fila que eu disponibilizar, pra bater essa
meta" + "continuar usando também os PCs locais normal no máximo; o Kaggle é pra ajudar a encher o estoque mais rápido".
Antes o Kaggle só recebia o Short que a produção normal do PC1 preparava, e ela esperava ele voltar antes do próximo:
com o PC1 ocupado a GPU ficava parada.

Aqui: Shorts EXTRAS, além dos PCs. Cada um é um anime_auto que só PREPARA no PC1 (baixa pela vez do yt-dlp, reedita,
roteiro) e manda a RENDERIZAÇÃO pra fila_shorts do Kaggle (SHORTS_NO_KAGGLE=1); SHORTS_SO_KAGGLE=1 = nunca renderiza no
PC1. Marca -X abastecedor_kaggle: o medidor de máquinas e a trava do parceiro_diario não contam como trabalho do PC1.
Meta: POR_LINHA Shorts em andamento por linha de curto viva no pool (papel da conta ou da linha/IP, como a central),
até MAXIMO. 1 Short novo por rodada (downloads espaçados: regra do yt-dlp sem rajada). Canal = o mais abaixo da meta
de 7 dias (mesma escolha do PC2: parceiro_diario._prioridade), fonte reservada na hora (ocioso._reservar).
  python abastecedor_kaggle.py [--simular]
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROD = Path(r"D:\recapd-ambientes\producao")
POOL = PROD / "colab" / "kaggle_pool.json"
ESTADO = BASE / "estado" / "abastecedor_kaggle.json"
LOG = BASE / "logs" / "abastecedor_kaggle.log"
POR_LINHA = 2  # 06/11: 3 x 4 linhas = 12 Shorts consultando o Drive juntos travavam o alimentador dos longos
MAXIMO = 16  # 06/11: 14 contas verificadas com cota até sexta 21h
MARCA = "abastecedor_kaggle"
BELOW_NORMAL, SEM_JANELA = 0x00004000, 0x08000000


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def linhas_curto():
    """IPs (linhas) de curto com conta viva no pool — mesma regra da central (vps_central._papel / _ip_da_conta)."""
    p = json.loads(POOL.read_text(encoding="utf-8"))
    mapa = p.get("linhas") or {}
    ips = set()
    for c in p.get("contas") or []:
        if c.get("banida") or c.get("bloqueada") or not c.get("verificada"):
            continue
        if c.get("pausada"):
            continue
        # mesma regra do vps_central._ip_da_conta (05/11: proxy_fixo caía em "direto" e 4 linhas viravam 1)
        ip = (f"webshare-{c['webshare_ip']}" if c.get("webshare_ip") else
              f"proxy-{c['proxy_fixo'].split('://')[-1].split(':')[0]}" if c.get("proxy_fixo") else
              f"direto-{c.get('saida', 'hermes-prod')}")
        if (c.get("papel") or mapa.get(ip) or "longo") == "curto" or _longo_vazio():
            ips.add(ip)
    return ips


_LONGO_VAZIO = None


def _longo_vazio():
    """06/11 dona ("gastar tudo antes da renovação"): sem recap longo na fila, a central empresta as linhas de longo
    para os Shorts (vps_central "linha assume trabalho de curto"); aqui elas contam para a meta. Lê a fila 1x."""
    global _LONGO_VAZIO
    if _LONGO_VAZIO is None:
        try:
            sys.path.insert(0, r"D:\recap_central_casa")
            import vps_central
            _LONGO_VAZIO = vps_central._trabalho_pendente("longo") == 0
        except Exception:  # noqa: BLE001
            _LONGO_VAZIO = False
    return _LONGO_VAZIO


def vivos():
    """{pid: info} dos Shorts extras ainda rodando (processo raiz com a marca)."""
    import psutil
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    out = {}
    for pid, info in (est.get("vivos") or {}).items():
        try:
            if MARCA in " ".join(psutil.Process(int(pid)).cmdline()):
                out[pid] = info
        except (psutil.Error, ValueError):
            pass
    return out


def gravar(v):
    ESTADO.parent.mkdir(exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps({"vivos": v, "em": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False,
                              indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def main(simular=False):
    """06/11 dona ("ligue a produção ao máximo, hoje renova os limites — gastar tudo"): cada rodada enche até a meta,
    um disparo por vez com POR_RODADA_ESPACO s entre eles (o yt-dlp do IP de casa nunca em rajada)."""
    for _ in range(POR_RODADA if not simular else 1):
        if _um(simular) is not True:
            return
        time.sleep(POR_RODADA_ESPACO)


POR_RODADA = 4
POR_RODADA_ESPACO = 75


def _um(simular=False):
    sys.path.insert(0, str(BASE))
    sys.path.insert(0, str(PROD / "bin"))
    import controle
    ok, motivo = controle.ligado("parceiro", "producao")
    if not ok:
        return log(f"desligado: {motivo}")
    try:
        if not json.loads((PROD / "config" / "shorts_kaggle.json").read_text(encoding="utf-8")).get("ligado"):
            return log("shorts_kaggle.json ligado=false — nada")
    except (OSError, ValueError):
        return log("sem config/shorts_kaggle.json — nada")
    # 05/11 05:20: o D chegou a 1,5 GB livres (reel da Globo 03:01 "No space left on device"). Cliente (solar/açaí)
    # vem antes: com menos de 6 GB livres no D o abastecedor não baixa Short extra.
    import shutil
    livre_gb = shutil.disk_usage("D:\\").free / 1e9
    if livre_gb < 6:
        return log(f"D: com {livre_gb:.1f} GB livres (< 6) — sem Short extra até liberar espaço")
    linhas = linhas_curto()
    meta = min(MAXIMO, POR_LINHA * len(linhas))
    v = vivos()
    gravar(v)
    if len(v) >= meta:
        return log(f"{len(v)}/{meta} Shorts extras em andamento ({len(linhas)} linha(s) de curto: "
                   f"{', '.join(sorted(linhas)) or '-'}) — cheio")
    import ytdlp_vez
    if ytdlp_vez.pausado() or getattr(ytdlp_vez, "espera_download_s", lambda: 0)() > 120:
        return log("yt-dlp em pausa/espaçando (IP da casa) — sem download novo nesta rodada")
    import ocioso
    import parceiro_diario as pdi
    import anime_discover
    ocioso.log = log
    c = pdi.cfg()
    if simular:
        return log(f"[simular] {len(v)}/{meta} em andamento, {len(linhas)} linha(s) de curto — dispararia 1")
    esc = ocioso._escolher_pc2(pdi, anime_discover, c)  # canal mais abaixo da meta + fonte já RESERVADA
    if not esc:
        return log("nenhum canal com vídeo novo pra fazer agora")
    alvo, escolha, cand = esc
    fonte, tipo = escolha[0], escolha[1]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PARCEIRO_HANDLE=alvo["handle"],
               PARCEIRO_CANAL=alvo["canal"], ANIME_IDIOMAS="", PARCEIRO_TIPO=tipo, ANIME_MAX_CPU_PCT="0",
               SHORTS_NO_KAGGLE="1", SHORTS_SO_KAGGLE="1", SHORTS_SEM_WHISPER="1",
               SHORTS_KAGGLE_ESPERA_MIN="300")  # com fila de vários por linha, a vez pode passar dos 90 min de antes
    logf = PROD / "workspace" / "anime" / f"_abastecedor_kaggle_{datetime.now():%Y%m%d}.log"
    cmd = [str(PROD / "venv" / "Scripts" / "python.exe"), "-X", "utf8", "-X", MARCA, str(PROD / "bin" / "anime_auto.py"),
           "--modo", "short", "--fonte", fonte, "--engine", "local", "--limit", "1", "--top", "5", "--id", cand["id"]]
    with open(logf, "a", encoding="utf-8") as fh:
        p = subprocess.Popen(cmd, cwd=str(PROD / "bin"), env=env, stdout=fh, stderr=subprocess.STDOUT,
                             creationflags=BELOW_NORMAL | SEM_JANELA)
    if len(escolha) == 3:
        pdi._rodizio_registrar(escolha[2])
    v[str(p.pid)] = {"id": cand["id"], "canal": alvo["nome"], "fonte": fonte, "inicio": datetime.now().isoformat(
        timespec="seconds")}
    gravar(v)
    log(f"DISPAROU Short extra {cand['id']} [{tipo}] pra {alvo['nome']} (pid {p.pid}; {len(v)}/{meta}; "
        f"render no Kaggle; log {logf.name})")
    return True


if __name__ == "__main__":
    try:
        main(simular="--simular" in sys.argv)
    except Exception as e:  # noqa: BLE001
        log(f"[!] {type(e).__name__}: {str(e)[:300]}")
