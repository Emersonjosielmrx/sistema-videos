# -*- coding: utf-8 -*-
r"""cenas_veo.py — Reel do CLONE em 2 ou 3 cenas, cada uma num ambiente (dona 31/10/2026: "por que os vídeos estão
saindo com um vídeo Veo só e não 2 ou 3, em ambientes diferentes, como no escritório, lá em cima dos painéis, na casa
de clientes perto de inversores").

A fala do roteiro é dividida por frase (a última cena é o convite: "Orçamento com a ..."); cada frase vira 1 clipe
Veo do clone num ambiente diferente (foto do clone criada na hora para aquele ambiente + image-to-video), cada clipe
passa na MESMA trava do clipe único (qa_ms.checar_clipe: rosto do clone, fala, texto na tela, deformação), é cortado
logo depois da última palavra e as cenas são emendadas. Devolve o clipe emendado e as palavras com o tempo já
deslocado; o gerar_short_veo segue para a montagem normal. Qualquer cena que não sai = None (o gerar_short_veo faz o
clipe único de antes). MS_MULTICENA=0 desliga. Custa 1 crédito do Veo por cena.
"""
import json
import re
import subprocess
from pathlib import Path

import roteiro_ms

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
W, H = 1080, 1920
TENTATIVAS_CENA = 3
FOLGA_FIM_S = 0.35

# ambientes novos (os de roteiro_ms.CENARIOS seguem valendo: casa, telhado, rural, comercio)
AMBIENTES = {
    "escritorio": ("sitting at a desk inside a small, tidy solar energy company office in northern Brazil (Para state), "
                   "a laptop and a few printed project sheets on the desk, a single solar panel leaning on the wall "
                   "behind, soft natural window light"),
    "inversor": ("standing in the covered garage of a client's house in northern Brazil (Para state), next to a plain "
                 "white wall-mounted solar inverter with no logo, no brand and no text on it, neat grey conduits on "
                 "the wall, natural daylight"),
    "paineis": ("standing on a sloped ceramic-tile roof between neat rows of dark blue solar panels, wearing a white "
                "safety helmet, bright tropical sun, small town in northern Brazil (Para state) behind"),
}
ORDEM = ["paineis", "escritorio", "inversor", "casa", "comercio"]


def _ambientes():
    for k, v in AMBIENTES.items():
        roteiro_ms.CENARIOS.setdefault(k, v)


def dividir(fala, cta):
    """['frase 1', 'frase 2'..., cta] com 2 ou 3 partes (frases muito curtas se juntam)."""
    frases = [f.strip() for f in re.findall(r"[^.!?]+[.!?]?", fala) if f.strip()]
    partes = []
    for f in frases:
        if partes and len(partes[-1].split()) < 4:
            partes[-1] = f"{partes[-1]} {f}"
        else:
            partes.append(f)
    if len(partes) > 2:
        partes = [partes[0], " ".join(partes[1:])]
    return partes + [cta]


def _probe(v):
    r = subprocess.run([FF.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(v)], capture_output=True, text=True, timeout=30)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _uma_cena(texto, cenario, foto, bases, destino, log):
    """Clipe aprovado da cena: (caminho, palavras, medidas) ou None."""
    import gerar_short_veo as g
    import qa_ms
    sub = {"tipo": "apresentador", "fala_final": texto, "clone_bases": bases}
    prompt = roteiro_ms.prompt_clone(texto)
    for n in range(TENTATIVAS_CENA):
        sessao = g.escolher_sessao()
        if sessao is None:
            log("  [CENAS] sem conta livre no Flow")
            return None
        g.aplicar_sessao(sessao)
        log(f"  [CENAS] cena '{cenario}' tentativa {n + 1} | conta={sessao['session']} | fala: {texto}")
        ok = g.gerar_video_robusto(prompt, foto, str(destino), log=log)
        if isinstance(ok, tuple) and ok[0] == "NO_CREDITS":
            g.marcar_creditos_esgotados(sessao["session"], padrao_texto=ok[1] if len(ok) > 1 else "")
            continue
        if ok in ("SESSAO", "RECAPTCHA", "TRAVOU"):
            g.marcar_conta_fora(sessao["session"], f"cenas: {ok}", horas=6 if ok == "SESSAO" else 0.5)
            continue
        if ok in ("PAUSED",):
            return None
        if ok is not True:
            # 31/10: 1º teste insistiu 3x na seebotsia sem cota (USER_QUOTA) -> a falha tira a conta por 1 h e a
            # próxima tentativa vai para outra (o clipe único faz o mesmo trocando de conta)
            g.registrar_falha_sessao(sessao["session"], f"cenas: {ok}")
            g.marcar_conta_fora(sessao["session"], "cenas: falhou (cota/Flow)", horas=1)
            continue
        g.registrar_sucesso_sessao(sessao["session"])
        qa = qa_ms.checar_clipe(destino, sub, log=log)
        if qa["ok"] and qa["palavras"]:
            return destino, qa["palavras"], qa["medidas"]
        g._guardar_reprovado(destino, sub, qa, n + 1)
    return None


def gerar_clipes(roteiro, timestamp, log=print):
    """{'clip', 'palavras', 'medidas', 'prompts'} com as cenas emendadas, ou None."""
    import gerar_short_veo as g
    _ambientes()
    partes = dividir(roteiro["fala"], roteiro_ms.CTA_FALADO)
    if len(partes) < 2:
        return None
    primeiro = roteiro.get("cenario") or "casa"
    outros = list(roteiro.get("cenarios_extra") or []) + [a for a in ORDEM if a != primeiro]  # criativo: inusitados
    cenarios = [primeiro] + outros[:len(partes) - 1]
    log(f"  [CENAS] {len(partes)} cenas: {list(zip(cenarios, partes))}")
    pasta = g.DIR_CACHE_VEO / f"cenas_{timestamp}"
    pasta.mkdir(parents=True, exist_ok=True)
    feitas = []
    for i, (cen, txt) in enumerate(zip(cenarios, partes)):
        if i == 0:
            foto, bases = roteiro["quadro"], roteiro["clone_bases"]
        else:
            # 01/11: ambiente novo (painéis, inversor...) ainda sem foto aprovada + Flow lotado de madrugada = voltava
            # ao clipe único; agora tenta mais 1 ambiente ainda não usado neste Reel (de preferência com foto aprovada)
            r = roteiro_ms._clone(cen, txt, log)
            if not r:
                usados = set(cenarios[:i]) | {c for c, *_ in feitas}
                reserva = next((a for a in outros if a not in usados and a not in cenarios[i:]), None)
                if reserva:
                    log(f"  [CENAS] sem foto do clone para '{cen}' — tento o ambiente '{reserva}'")
                    r = roteiro_ms._clone(reserva, txt, log)
                    cen = reserva if r else cen
            if not r:
                log(f"  [CENAS] sem foto do clone para '{cen}' — volto ao clipe único")
                return None
            foto, bases = r
        res = _uma_cena(txt, cen, foto, bases, pasta / f"cena_{i + 1}.mp4", log)
        if not res:
            log(f"  [CENAS] cena {i + 1} ('{cen}') não saiu — volto ao clipe único")
            return None
        feitas.append((cen, txt) + res)

    # corta cada cena logo depois da última palavra e emenda (mesma escala/fps/áudio)
    entradas, filtros, palavras, t0, medidas = [], [], [], 0.0, []
    for i, (cen, txt, clip, pal, med) in enumerate(feitas):
        dur = _probe(clip)
        fim = min(dur - 0.3, max(p[2] for p in pal) + FOLGA_FIM_S)
        entradas += ["-i", str(clip)]
        filtros.append(f"[{i}:v]trim=0:{fim:.2f},setpts=PTS-STARTPTS,scale={W}:{H}:force_original_aspect_ratio="
                       f"increase,crop={W}:{H},fps=30,setsar=1,format=yuv420p[v{i}]")
        filtros.append(f"[{i}:a]atrim=0:{fim:.2f},asetpts=PTS-STARTPTS,aresample=48000,"
                       f"aformat=channel_layouts=stereo[a{i}]")
        palavras += [(w, round(s + t0, 2), round(e + t0, 2)) for w, s, e in pal]
        medidas.append({"cena": cen, "fala": txt, "corte_s": round(fim, 2), **med})
        t0 += fim
    n = len(feitas)
    filtros.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
    saida = pasta / "emendado.mp4"
    r = subprocess.run([FF, "-y", "-v", "error", *entradas, "-filter_complex", ";".join(filtros), "-map", "[v]",
                        "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac",
                        "-b:a", "192k", str(saida)], capture_output=True, text=True, timeout=900)
    if r.returncode or not saida.exists():
        log(f"  [CENAS] emenda falhou: {r.stderr[-300:]} — volto ao clipe único")
        return None
    log(f"  [CENAS] {n} cenas emendadas ({t0:.1f}s): {[m['cena'] for m in medidas]}")
    (pasta / "cenas.json").write_text(json.dumps(medidas, ensure_ascii=False, indent=1), "utf-8")
    return {"clip": saida, "palavras": palavras, "medidas": {"cenas": medidas},
            "prompts": [roteiro_ms.prompt_clone(t) for t in partes]}
