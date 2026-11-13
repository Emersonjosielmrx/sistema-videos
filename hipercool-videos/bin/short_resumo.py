#!/usr/bin/env python3
"""Short de RESUMO: a história condensada num vídeo só, em vez de cortada em partes.

Por que existe (pedido do dono, 16/10/2026): o Short de trecho ("Parte 3 de 5") só interessa a quem
já viu as partes anteriores. O Short de resumo é a porta de entrada — conta a história do começo ao
gancho e manda o espectador pro vídeo longo. No canal de referência que o dono passou
(youtube.com/@kaijinre/shorts) a diferença entre os dois é gritante: o Short sem "Parte N" no título
fez 513 mil visualizações enquanto a "Parte 2" da MESMA obra fez 2,4 mil; outros três sem parte
fizeram 433 mil, 231 mil e 37 mil. É esse formato que o algoritmo empurra.

Como monta: não gera narração nova nem chama modelo. Usa o que o editorial já marcou no
`.meta.json` do vídeo — os 7 ou 8 momentos de IMPACTO ("flagra", "porta", "chorando") — e costura o
painel inteiro de cada um, do jeito que foi narrado. Painel inteiro porque a fronteira de painel é o
único ponto onde o pipeline garante que nenhuma fala está no meio.

    python short_resumo.py --video <mp4> --obra "The Inheritor" --capitulo 1

Também dá pra chamar `montar(...)` de dentro do pipeline.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, log  # noqa: E402

ALVO_S = 75.0        # Shorts de resumo do canal de referência ficam entre 60 s e 90 s
MIN_S = 45.0         # abaixo disso não conta história nenhuma
MAX_S = 170.0        # o limite do formato é 180 s; sobra folga pro cartão final
MIN_TRECHO = 1.8     # painel mais curto que isso é piscada, não momento
FPS = 30


def _meta(video_path):
    p = Path(video_path).with_suffix(".meta.json")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def escolher_trechos(meta, alvo=ALVO_S):
    """(inicio, fim) de cada BLOCO que entra no resumo, em ordem de tempo.

    Cada momento de impacto vira um bloco de painéis seguidos, não um painel solto: o painel do
    impacto dura 3 a 8 s e sozinho não conta nada ("ela chorou" sem o que levou ao choro). O bloco
    cresce PRA TRÁS a partir do impacto — é a fala que arma o momento — e só cresce pra frente se
    ainda faltar. Medido no cap 1: painel solto dava 28,7 s de resumo; com bloco de 10 s dá 73 s.

    Entra sempre a ABERTURA (onde o gancho é dito) e os blocos ficam na ordem do capítulo: resumo
    conta a história na sequência, não é apanhado solto. Painel dentro de janela censurada fica de
    fora — o Short é a vitrine do canal.
    """
    acab = (meta or {}).get("acabamento") or {}
    fr, du = acab.get("fronteiras") or [], acab.get("duracoes") or []
    if not fr or not du:
        return []
    n = min(len(fr), len(du))
    janelas = ((meta or {}).get("censura") or {}).get("janelas") or []

    def limpo(a, b):
        return not any(max(a, x) < min(b, y) for x, y in janelas)

    def ok(k):
        return 0 <= k < n and du[k] >= MIN_TRECHO and limpo(fr[k], fr[k] + du[k])

    def bloco(k, minimo):
        """Painéis seguidos em volta de k que somem `minimo` segundos, sem pegar painel censurado."""
        if not ok(k):
            return None
        ini = fim = k
        while fr[fim] + du[fim] - fr[ini] < minimo:
            cresceu = False
            if ok(ini - 1):                      # pra trás primeiro: é o que arma o momento
                ini -= 1
                cresceu = True
            elif ok(fim + 1):
                fim += 1
                cresceu = True
            if not cresceu:
                break
        return (fr[ini], fr[fim] + du[fim])

    impactos = [i.get("fala") for i in ((acab.get("editorial") or {}).get("impactos") or [])
                if isinstance(i.get("fala"), int)]
    # o alvo dividido pelos momentos dá o tamanho de cada bloco (com piso, pra não virar piscada)
    por_bloco = max(7.0, alvo / max(1, len(impactos) + 1))

    blocos = []
    for k in range(min(3, n)):                   # abertura: o primeiro painel limpo
        b = bloco(k, por_bloco)
        if b:
            blocos.append(b)
            break
    for k in impactos:
        b = bloco(k, por_bloco)
        if b:
            blocos.append(b)

    # juntar o que encostou (blocos vizinhos viram um só) e cortar no alvo
    blocos.sort()
    juntos = []
    for a, b in blocos:
        if juntos and a <= juntos[-1][1] + 0.05:
            juntos[-1] = (juntos[-1][0], max(juntos[-1][1], b))
        else:
            juntos.append((a, b))

    escolhidos, soma = [], 0.0
    for a, b in juntos:
        if soma + (b - a) > MAX_S:
            break
        escolhidos.append((a, b))
        soma += b - a
    return escolhidos


def montar(video_path, out_dir, obra, capitulo, alvo=ALVO_S, loop=True):
    """Monta o arquivo do Short de resumo. Devolve o caminho, ou None se não deu pra montar.
    loop: fecha com a frase do narrador que amarra no começo (short_loop)."""
    video_path = Path(video_path)
    meta = _meta(video_path)
    trechos = escolher_trechos(meta, alvo)
    if len(trechos) < 3:
        log(f"  [!] resumo não montado: só {len(trechos)} trecho(s) aproveitável(is)")
        return None

    total = sum(b - a for a, b in trechos)
    log(f"Resumo: {len(trechos)} momentos, {total:.0f}s "
        f"({', '.join(f'{a:.0f}-{b:.0f}' for a, b in trechos)})")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", obra.lower()).strip("-")
    saida = out_dir / f"{slug}_cap{capitulo}_resumo.mp4"

    # Fecho em loop (dono, 16/10): fala nova do narrador no fim que amarra no primeiro quadro.
    fecho = None
    if loop:
        try:
            import short_loop
            fecho = short_loop.preparar(video_path, trechos, meta, obra, out_dir)
        except Exception as e:  # noqa: BLE001 — enfeite: o resumo sai sem ele
            log(f"  [!] fecho em loop falhou: {str(e)[:120]}")

    # Um comando só, com trim/concat: cortar em pedaços e colar depois erra o ponto, porque corte
    # copiado só cai em keyframe e aqui os pontos vêm da narração, não do codec.
    partes, rotulos = [], ""
    for i, (a, b) in enumerate(trechos):
        partes.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];"
                      f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}];")
        rotulos += f"[v{i}][a{i}]"
    filtro = "".join(partes) + f"{rotulos}concat=n={len(trechos)}:v=1:a=1[v][a]"
    entradas, saida_v, saida_a = ["-i", str(video_path)], "[v]", "[a]"
    if fecho:
        # último quadro parado enquanto o narrador diz a frase, com a legenda dela; depois o loop
        import fx_acabamento as fx
        d, ms = fecho["dur"], int(fecho["inicio"] * 1000)
        entradas += ["-i", str(fecho["wav"])]
        filtro += (f";[v]tpad=stop_mode=clone:stop_duration={d:.3f},"
                   f"ass=filename={fx.ffpath(fecho['ass'])}:fontsdir={fx.ffpath(fx.FONTS_DIR)}[vf]"
                   f";[a]aformat=sample_rates=48000:channel_layouts=stereo,"
                   f"apad=whole_dur={fecho['inicio'] + d:.3f}[ap]"
                   f";[1:a]aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=7,"
                   f"aresample=48000,adelay={ms}|{ms}[vz]"
                   f";[ap][vz]amix=inputs=2:normalize=0:duration=first[af]")
        saida_v, saida_a = "[vf]", "[af]"

    base = ["ffmpeg", "-y", *entradas, "-filter_complex", filtro, "-map", saida_v, "-map", saida_a]
    tentativas = [base + ["-c:v", "h264_qsv", "-global_quality", "23", "-c:a", "aac", "-b:a", "192k", str(saida)],
                  base + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", str(saida)]]
    for k, cmd in enumerate(tentativas):
        r = subprocess.run(cmd, capture_output=True, timeout=1800)
        if r.returncode == 0 and saida.exists() and saida.stat().st_size > 10000:
            return saida
        if k == len(tentativas) - 1:
            log(f"  [!] resumo falhou: {(r.stderr or b'').decode('utf-8', 'replace')[-300:]}")
            if fecho:  # o fecho é o que mais muda o comando: tenta de novo sem ele
                log("  [!] refazendo o resumo sem o fecho em loop")
                return montar(video_path, out_dir, obra, capitulo, alvo, loop=False)
            return None
        log("  [!] resumo pelo Quick Sync falhou — refazendo no x264")
    return None


def metadados(meta, obra, capitulo, idioma=None):
    """Título/descrição/tags do Short de resumo.

    SEM "Parte N" — é isso que separa o resumo do Short de trecho, tanto pro público quanto pra
    medir depois qual dos dois rende mais. O gancho do editorial já é uma frase pronta em caixa
    alta, no mesmo formato dos títulos do canal de referência.
    """
    ed = ((meta or {}).get("acabamento") or {}).get("editorial") or {}
    gancho = (ed.get("gancho") or "").strip()
    emoji = next((i.get("emoji") for i in (ed.get("impactos") or []) if i.get("emoji")), "🔥")
    titulo = f"{emoji} {gancho}... #manhwa #manga #anime"[:100] if gancho else \
             f"{emoji} Resumo #manhwa #manga #anime"
    pergunta = (ed.get("pergunta") or "").strip()
    desc = (f"{gancho}\n{pergunta}\n\n"
            f"A história toda está no canal — veja o vídeo completo.\n\n"
            f"#Manhwa #Manga #Anime #Recap #Webtoon #Shorts")
    return {
        "tipo": "resumo",            # é por aqui que o postador e as métricas separam os dois
        "capitulo": capitulo,
        "idioma": idioma,
        "pt": {"title": titulo, "description": desc,
               "tags": ["manhwa", "recap manhwa", "manhwa recap", "webtoon",
                        "resumo manhwa", "manhwa completo", "shorts", "anime"]},
    }


def main():
    ap = argparse.ArgumentParser(description="Monta o Short de RESUMO de um capítulo")
    ap.add_argument("--video", required=True)
    ap.add_argument("--obra", required=True)
    ap.add_argument("--capitulo", type=int, required=True)
    ap.add_argument("--out-dir")
    ap.add_argument("--alvo", type=float, default=ALVO_S)
    a = ap.parse_args()

    video = Path(a.video)
    if not video.exists():
        print(f"ERRO: vídeo não encontrado: {video}", file=sys.stderr)
        sys.exit(1)

    slug = re.sub(r"[^a-z0-9]+", "-", a.obra.lower()).strip("-")
    out_dir = Path(a.out_dir) if a.out_dir else (PROJECT_DIR / "workspace" / "shorts" / f"{slug}-cap{a.capitulo}")
    saida = montar(video, out_dir, a.obra, a.capitulo, a.alvo)
    if not saida:
        sys.exit(2)

    meta = _meta(video)
    (out_dir / "meta_resumo.json").write_text(
        json.dumps({**metadados(meta, a.obra, a.capitulo), "arquivo": saida.name},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"✅ Short de resumo: {saida}")


if __name__ == "__main__":
    main()
