"""vigia_videos_novos.py — avisa CADA vídeo novo assim que fica pronto (dona 02/11: "acompanhar no monitor cada vídeo
que sair e analisar como o melhorador"). Uma linha por vídeo novo no stdout (o Monitor do chat transforma em aviso):
    NOVO <tipo> <caminho>
Tipos: CORTE (Short de Cortes/parceiro, PC1), KAGGLE_SHORT (Short de Cortes renderizado no Kaggle), LONGO (recap longo;
os Shorts de recap/cortes_longo vêm junto na revisão), COMEDIA, SOLAR, VEO.
1ª passada marca o que já existe como visto (não dispara tudo). Estado: estado\\vigia_videos_vistos.json.
    python vigia_videos_novos.py            # laço, 1 checagem por minuto
"""
import json
import re
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ESTADO = BASE / "estado" / "vigia_videos_vistos.json"
LOG_PARCEIRO = Path(r"D:\hipercool-materiais\anime")
NUVEM = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
COMEDIA = Path(r"D:\hipercool-materiais\videos-comentarios")
SOLARES = [Path(r"D:\ms-energy\videos\reels_advance"), Path(r"D:\ms-energy\videos\reels_globo"),
           Path(r"D:\ms-energy\videos\shorts_veo")]
VEO = Path(r"D:\veo\beta\videos_pos\cron_shorts")
RE_PRONTO = re.compile(r"\[auto\|short\] PRONTO: (.+)$")


SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")  # destino final de TODO Short de Cortes (PC1, desktop, Kaggle)
LONGOS_POSTAR = Path(r"D:\hipercool-materiais\_longos_postar")
PRODUTOS = [Path(r"D:\video-fila\produto_fila"), Path(r"D:\hipercool-materiais\produtos_ultimo_video")]
REMOTION = Path(r"D:\claude-code-video\saida")


def achar():
    """{chave: (tipo, caminho)} de tudo que está pronto agora."""
    out = {}
    # 02/11 19h40: o Short de Cortes do desktop (PC3) não passa pelo log do PC1 — a pasta final pega todos
    for mp4 in SHORTS.glob("*/*.mp4"):
        if mp4.name.startswith("_"):  # temporário (conversão em andamento)
            continue
        out["short:" + str(mp4)] = ("CORTE", str(mp4))
    logs = sorted(LOG_PARCEIRO.glob("_parceiro_2026????.log"))[-2:]
    for lg in logs:  # só pra avisar que o render foi no Kaggle (o vídeo em si aparece na pasta acima)
        try:
            linhas = lg.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        kaggle = False
        for l in linhas:
            if "renderizado no KAGGLE" in l:
                kaggle = True
            m = RE_PRONTO.search(l)
            if m and kaggle:
                out["kaggle:" + m.group(1).strip()] = ("KAGGLE_SHORT", m.group(1).strip())
                kaggle = False
    for mp4 in LONGOS_POSTAR.glob("*/*.mp4"):
        out["longofinal:" + str(mp4)] = ("LONGO_VIDEO", str(mp4))
    for d in PRODUTOS:
        for mp4 in d.rglob("*.mp4"):
            out["produto:" + str(mp4)] = ("PRODUTO", str(mp4))
    for mp4 in REMOTION.glob("*/*.mp4"):
        out["remotion:" + str(mp4)] = ("REMOTION", str(mp4))
    for nj in NUVEM.glob("*/nuvem.json"):
        out["longo:" + nj.parent.name] = ("LONGO", str(nj.parent))
    for pj in COMEDIA.glob("*/postar.json"):
        out["comedia:" + pj.parent.name] = ("COMEDIA", str(pj.parent))
    for d in SOLARES:
        for mp4 in d.glob("*.mp4"):
            out["solar:" + mp4.name] = ("SOLAR", str(mp4))
    for mp4 in VEO.glob("*.mp4"):
        out["veo:" + mp4.name] = ("VEO", str(mp4))
    return out


def main():
    try:
        vistos = set(json.loads(ESTADO.read_text(encoding="utf-8")))
        primeira = False
    except (OSError, ValueError):
        vistos, primeira = set(), True
    while True:
        try:
            agora = achar()
        except Exception as e:  # noqa: BLE001
            print(f"ERRO vigia: {type(e).__name__}: {e}", flush=True)
            time.sleep(60)
            continue
        # 02/11: avisava no meio da gravação ("moov atom not found"). Só vale arquivo parado há 90 s (pasta: sempre)
        def _pronto(k):
            p = Path(agora[k][1])
            try:
                return not p.is_file() or time.time() - p.stat().st_mtime > 90
            except OSError:
                return False
        novos = [k for k in agora if k not in vistos and _pronto(k)]
        # tipo que nunca foi visto (acabou de entrar no vigia) = linha de base, não aviso
        tipos_vistos = {k.split(":", 1)[0] for k in vistos}
        if not primeira:
            for k in sorted(novos):
                if k.split(":", 1)[0] not in tipos_vistos:
                    continue
                tipo, caminho = agora[k]
                print(f"NOVO {tipo} {caminho}", flush=True)
        vistos |= set(novos)
        primeira = False
        ESTADO.parent.mkdir(exist_ok=True)
        ESTADO.write_text(json.dumps(sorted(vistos), ensure_ascii=False), encoding="utf-8")
        if "--uma" in sys.argv:
            return
        time.sleep(60)


if __name__ == "__main__":
    main()
