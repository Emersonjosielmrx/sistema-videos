"""29/10 dona: lista de longos "nessa ordem mesmo, um em cada GPU, só 4 por vez, sempre um por cada VPS e outro pelo IP
do PC local" (kaggle_pool.json gpus_por_saida = 1 em cada uma das 4 saídas).
  1. prepara UM vídeo por vez (yt-dlp sem rajada; corta a intro do parceiro; roteiro) e manda com pid
     20261027_00NN00_<id>: o trabalhador pega o 1º pedido livre por NOME, então a lista passa na frente dos pedidos
     antigos e sai na ordem dela;
  2. recolhe cada pronto.json como o esperar_e_publicar.py (cortes, Drive, ficha) — a postagem (agendada) é a
     RecapPostarLongos de sempre.
Estado em fila_dona.json (retoma de onde parou se for rodado de novo).
    pythonw fila_dona.py <url> [<url> ...]     (sem url = continua a lista salva)      log: fila_dona.log"""
import json
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import cliente  # noqa: E402

EST = AQUI / "fila_dona.json"
LOG = AQUI / "fila_dona.log"


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {m}\n")


def salvar(est):
    EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def vid_de(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
    return m.group(1) if m else None


est = json.loads(EST.read_text(encoding="utf-8")) if EST.exists() else {"itens": []}
ja = {i["vid"] for i in est["itens"]}
for url in sys.argv[1:]:
    v = vid_de(url)
    if v and v not in ja:
        est["itens"].append({"vid": v, "url": f"https://www.youtube.com/watch?v={v}", "estado": "esperando"})
        ja.add(v)
salvar(est)
log(f"lista: {[i['vid'] for i in est['itens']]}")


def _pedido_sem_rede(it):
    """30/10: o recolher chamava cliente.preparar(url) só pra saber o nome — com a pasta de trabalho limpa ele BAIXAVA o
    original de novo (e com o yt-dlp em pausa o pronto nunca era recolhido). Com o título salvo, o nome sai daqui."""
    if not it.get("titulo"):
        return cliente.preparar(it["url"])
    aa = cliente._projeto()
    nome = f"{it['vid']}_{aa._slug(it['titulo'])}"
    work = aa.BASE / nome
    work.mkdir(parents=True, exist_ok=True)
    return {"vid": it["vid"], "titulo": it["titulo"], "nome": nome, "url": it["url"], "work": work,
            "video": work / "source.mp4", "roteiro": work / "roteiro.txt"}


def recolher():
    for n, it in enumerate(est["itens"], 1):
        if it["estado"] != "enviado":
            continue
        pasta = f"{cliente.FILA}/{it['pid']}"
        pronto = cliente._ler_json(f"{pasta}/pronto.json")
        if not pronto:
            if cliente._ler_json(f"{pasta}/erro.json"):
                it["estado"] = "erro no render"
                log(f"{it['vid']}: ERRO no render ({pasta}/erro.json)")
                salvar(est)
            continue
        try:
            p = _pedido_sem_rede(it)
            # 30/10: capítulos e roteiro feitos no trabalhador ficavam na fila e eram apagados no limpar() — o Pastor
            # (LAei) e o P-dj foram ao ar sem capítulos na descrição. Igual ao alimentador: copia pra pasta de trabalho
            # (o publicar_drive leva pra ficha). O roteiro do PC, se existe, manda.
            for arq in ("capitulos.json", "roteiro.txt"):
                if arq == "roteiro.txt" and Path(p["roteiro"]).exists():
                    continue
                try:
                    cliente._rc("copyto", f"{pasta}/{arq}", str(p["work"] / arq))
                except RuntimeError:
                    pass
            # 30/10: o pronto do Kaggle/VPS já está no manhwa-drive — move lá dentro (igual ao alimentador) em vez de
            # baixar ~1 GB pro PC e subir de novo pela internet de casa
            remoto = f"{cliente.FILA_SRC}/{it['pid']}/final_anime_deitado.mp4"
            try:
                no_drive = "final_anime_deitado.mp4" in cliente._rc("lsf", f"{cliente.FILA_SRC}/{it['pid']}", saida=True)
            except RuntimeError:
                no_drive = False
            final = remoto if no_drive else p["work"] / "final_anime_deitado.mp4"
            # 01/11: o alimentador/cliente pode ter recolhido antes (6d2a: na_nuvem\...\nuvem.json às 09:58, vídeo já no
            # 1_youtube_pendente) — sem isto o fila_dona tentava baixar o mp4 já movido a cada ~15 min pra sempre
            ja = cliente._projeto().ANIMES_FICHAS.parent / "na_nuvem" / p["nome"] / "nuvem.json"
            if not no_drive and ja.exists():
                cliente.limpar(it["pid"])
                it["estado"] = "no Drive (postagem agendada pela RecapPostarLongos)"
                log(f"{it['vid']}: já recolhido por outra rotina — {ja.parent.name}")
                salvar(est)
                continue
            if not no_drive:
                cliente.baixar_final(it["pid"], final)
            cliente.guardar_cortes(it["pid"], p["nome"])
            cliente.publicar_drive(p, final, f"{pronto.get('por', 'kaggle')} (fila_dona)")
            ficha = cliente._projeto().ANIMES_FICHAS / p["nome"]
            (ficha / "render.json").write_text(json.dumps(pronto, ensure_ascii=False, indent=1), encoding="utf-8")
            cliente._rc("copyto", f"{pasta}/pipeline.log", str(ficha / "pipeline.log"))
            cliente.limpar(it["pid"])
            it["estado"] = "no Drive (postagem agendada pela RecapPostarLongos)"
            log(f"{it['vid']}: pronto e no Drive — {p['nome']}")
        except Exception:  # noqa: BLE001
            log(f"{it['vid']}: recolher falhou, tenta de novo:\n{traceback.format_exc()[-600:]}")
        salvar(est)


try:
    for tentativa in range(3):  # quem falhou ao preparar (download/IA fora) tenta de novo depois
        for n, it in enumerate(est["itens"], 1):
            if it["estado"] not in ("esperando", "falhou ao preparar"):
                continue
            try:
                log(f"{n}. {it['vid']}: preparando")
                p = cliente.preparar(it["url"])
                it["pid"] = f"20261027_00{n:02d}00_{it['vid']}"
                cliente.enviar(p["work"], p["video"], p["roteiro"], p["titulo"], pid=it["pid"])
                it["estado"], it["titulo"] = "enviado", p["titulo"]
                log(f"{n}. {it['vid']}: na fila como {it['pid']} — {p['titulo'][:70]}")
            except Exception:  # noqa: BLE001
                it["estado"] = "falhou ao preparar"
                log(f"{n}. {it['vid']}: falhou ao preparar:\n{traceback.format_exc()[-600:]}")
            salvar(est)
            recolher()
        if not any(i["estado"] == "falhou ao preparar" for i in est["itens"]):
            break
        time.sleep(30 * 60)
    fim = time.time() + 96 * 3600
    while time.time() < fim and any(i["estado"] == "enviado" for i in est["itens"]):
        recolher()
        time.sleep(300)
    log("fim: " + ", ".join(f"{i['vid']}={i['estado']}" for i in est["itens"]))
except BaseException:
    log("MORREU:\n" + traceback.format_exc())
    raise
