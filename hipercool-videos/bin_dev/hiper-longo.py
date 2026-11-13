# -*- coding: utf-8 -*-
"""hiper-longo.py — VÍDEO LONGO DEITADO (16:9, 1920x1080) da obra, juntando os capítulos.

Reaproveita TUDO o que o vertical já pagou em IA — nenhuma chamada nova:
  narração (narration_cache), vozes (tts_cache), censura (score + regiões em cache: o +18 sai com
  mosaico local igual ao vertical), recortes/rostos (cache de máscaras/rostos), trilha (fx_music).

O formato deitado dá espaço pra mais de uma imagem na tela. Cada fala vira um "momento":
  tira    o painel da fala no meio, o anterior e o próximo apagados nas laterais (história em
          quadrinhos andando pro lado); painel alto desce devagar dentro do quadro;
  close   painel à esquerda + o ROSTO dele grande à direita (reação), só em painel não sugestivo;
  recorte painel à esquerda + o personagem RECORTADO saindo dele, grande, à direita.
Legenda desenhada no próprio quadro (sem segundo encode); vídeo no Quick Sync (GPU Intel).

  python bin/hiper-longo.py --obra the-inheritor --caps 1-3            # renderiza os caps que faltam
  python bin/hiper-longo.py --obra the-inheritor --caps 1-10 --compilar  # + junta tudo num vídeo só

Saída: workspace/videos/longo/<obra>/capNN.mp4 (um por capítulo, fica em cache) e, com --compilar,
<obra>_caps01-NN.mp4 + .json (capítulos com minuto pra descrição do YouTube) + .capa.jpg.
O vídeo "cresce" com a obra: cada compilação junta do cap 1 até o último pronto.
"""
import argparse
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import censura_visual  # noqa: E402
import effects_engine  # noqa: E402
import fx_acabamento  # noqa: E402
import fx_music  # noqa: E402
import fx_parallax  # noqa: E402
import hp_paineis  # noqa: E402
from hp_common import PROJECT_DIR, log  # noqa: E402
from tts_stage import tts_panel  # noqa: E402

import os  # noqa: E402
# vídeo longo NUNCA gera voz nova: só o cache do vertical (fala que faltar fica muda, sem chamar a API)
os.environ["TTS_CACHE_ONLY"] = "1"

W, H, FPS = 1920, 1080, 30
SAIDA = PROJECT_DIR / "workspace" / "videos" / "longo"
PAINEIS = Path(r"D:\hipercool-materiais\panels")
CW, CH = int(0.46 * W), int(0.93 * H)   # quadro do painel na tela
PASSO = int(0.56 * W)                   # distância entre painéis vizinhos na tira
T_TROCA = 0.4                           # s da transição entre momentos
FOLGA = 0.25                            # s de respiro depois de cada fala
AMARELO = (0, 212, 255)                 # BGR do #FFD400


# ─── capítulo: dados (tudo do cache) ─────────────────────────────────────────
def _ler_json_tolerante(p):
    raw = Path(p).read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("cp1252"))


def _dados_capitulo(pasta, skip_ini, skip_fim, idioma=None):
    """(paineis, capa_original, recap_pt, recap_do_video). Outra língua: a tradução em cache do vertical."""
    paineis, capa_orig = hp_paineis.selecionar_paineis(pasta, 120, 1, skip_fim, skip_ini, verbose=False)
    narr = hp_paineis.arquivo_narracao(pasta, len(paineis), 1, skip_fim, skip_ini)
    if not narr.exists():
        raise FileNotFoundError(f"sem narração em cache ({narr.name}) — renderize o vertical antes")
    recap = _ler_json_tolerante(narr)
    if not idioma:
        return paineis, capa_orig, recap, recap
    tr = narr.with_name(narr.stem + f"_{idioma}.json")
    if not tr.exists():
        raise FileNotFoundError(f"sem tradução {idioma} em cache ({tr.name}) — renderize o vertical {idioma} antes")
    return paineis, capa_orig, recap, _ler_json_tolerante(tr)


def _censurar(paineis, recap, tmp):
    """Mesma decisão do vertical (passo 1c do hiper-pipeline), só que lendo do cache: devolve
    (imagens a usar, scores). +18 vira a imagem com mosaico local; o resto, o painel original."""
    locs, descs = recap.get("locucoes", []), recap.get("descriptions", [])
    scores, textos = [], []
    for k, p in enumerate(paineis):
        txt = locs[k].get("text", "") if k < len(locs) else ""
        textos.append(effects_engine.is_nsfw_panel(descs[k] if k < len(descs) else "", txt))
        s, _ = censura_visual.detectar_score(p)
        scores.append(s if s is not None else (censura_visual.LIMIAR_NSFW if textos[k] else 0.0))
    usar = list(paineis)
    for k, s in enumerate(scores):
        tipo = None
        if s < censura_visual.LIMIAR_DUVIDA:
            viz = max([scores[j] for j in (k - 1, k + 1) if 0 <= j < len(scores)] or [0.0])
            if not (viz >= censura_visual.LIMIAR_NSFW and censura_visual.mancha_branca_frac(paineis[k]) >= 0.05):
                continue
            s, tipo = censura_visual.LIMIAR_DUVIDA, "branco"
        out = tmp / f"cens_{k:03d}.png"
        nivel, _det = censura_visual.censurar_imagem(paineis[k], out, s, tipo=tipo, texto_nsfw=textos[k])
        if nivel != "intacto" and out.exists():
            usar[k] = out
    return usar, scores


def _wav_dur(p):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, timeout=15)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


TRANSICOES = ("desliza", "sobe", "funde", "corte")


def _momentos(paineis, imagens, scores, recap, tmp, idioma=None, recap_pt=None):
    """Lista de momentos: {img, painel (original, p/ máscara/rosto), wav, dur, texto, layout, trans}.
    layout: tira | cheio (painel na largura toda, câmera desce) | duo (anterior + atual lado a lado) |
    close | recorte. Nunca a mesma transição/layout comum 3 vezes seguidas."""
    locs = recap.get("locucoes", [])
    descs = (recap_pt or recap).get("descriptions", [])
    out, ult_especial = [], -9
    rng = random.Random(len(paineis) * 31 + len(locs))
    for k, p in enumerate(paineis):
        loc = locs[k] if k < len(locs) else {}
        desc = descs[k] if k < len(descs) else ""
        texto = (loc.get("text") or "").strip()
        if effects_engine.is_propaganda(desc, texto):
            continue
        wav = None
        if texto:
            persona = loc.get("persona", "Narrador")
            gen = None if (persona or "").lower() in ("narrador", "narradora", "narrator") else loc.get("gender")
            wav = tmp / f"voz_{k:03d}.wav"
            if idioma:
                import idiomas
                ok = idiomas.falar(texto, wav, persona, gen, idioma)
            else:
                ok = tts_panel(texto, wav, persona=persona, gender=gen)
            if not ok:
                wav = None
        dur = (_wav_dur(wav) + FOLGA) if wav else 1.0
        sugestivo = scores[k] >= 0.25 or imagens[k] != p
        layout = None
        if k - ult_especial >= 3:
            rosto = None if sugestivo else fx_parallax.rosto_principal(p)
            if rosto and (effects_engine.is_reacao_panel(desc, texto) or rng.random() < 0.3):
                layout = "close"
            elif not sugestivo and fx_parallax.elegivel(p)[0] and fx_acabamento._recorte_limpo(p, 0.6) \
                    and rng.random() < 0.6:
                layout = "recorte"
        if layout:
            ult_especial = k
        else:
            ultimos = [o["layout"] for o in out[-2:]]
            opcoes = [l_ for l_ in ("tira", "tira", "cheio", "duo") if not (ultimos == [l_, l_])]
            layout = rng.choice(opcoes if out else ["tira"])
        ult_tr = [o["trans"] for o in out[-2:]]
        trans = rng.choice([t for t in TRANSICOES if ult_tr != [t, t]])
        out.append({"img": imagens[k], "painel": p, "wav": wav, "dur": max(dur, 1.0),
                    "texto": texto if wav else "", "layout": layout, "trans": trans})
    return out


# ─── desenho ─────────────────────────────────────────────────────────────────
def _cobrir(img, w, h):
    sc = max(w / img.shape[1], h / img.shape[0])
    r = cv2.resize(img, (int(img.shape[1] * sc) + 2, int(img.shape[0] * sc) + 2), interpolation=cv2.INTER_AREA)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]


def _fundo(img):
    return cv2.convertScaleAbs(cv2.GaussianBlur(_cobrir(img, W // 4, H // 4), (0, 0), 6), alpha=0.45)


def _cartao(img, cw=CW, ch=CH):
    """Painel no tamanho do quadro (largura cw). Alto demais: devolve a imagem inteira na escala e
    quem desenha desce uma janela de altura ch por ela."""
    sc = min(cw / img.shape[1], ch / img.shape[0]) if img.shape[0] / img.shape[1] <= 1.8 else cw / img.shape[1]
    return cv2.resize(img, (int(img.shape[1] * sc), int(img.shape[0] * sc)), interpolation=cv2.INTER_AREA)


def _colar(frame, img, cx, cy, alpha=None):
    """Cola img centrada em (cx, cy), cortando o que sair da tela. alpha: float 0..1 do tamanho de img."""
    h, w = img.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    src = img[ya - y0:yb - y0, xa - x0:xb - x0]
    if alpha is None:
        frame[ya:yb, xa:xb] = src
    else:
        a = np.ascontiguousarray(alpha[ya - y0:yb - y0, xa - x0:xb - x0])
        frame[ya:yb, xa:xb] = cv2.blendLinear(np.ascontiguousarray(src), np.ascontiguousarray(frame[ya:yb, xa:xb]),
                                              a, 1.0 - a)


def _janela(cartao, t, dur):
    """Parte visível do cartão: se for mais alto que o quadro, desce devagar do topo ao fim."""
    if cartao.shape[0] <= CH:
        return cartao
    e = min(1.0, t / max(0.1, dur))
    e = e * e * (3 - 2 * e)
    y = int((cartao.shape[0] - CH) * e)
    return cartao[y:y + CH]


def _com_borda(img, b=6):
    return cv2.copyMakeBorder(img, b, b, b, b, cv2.BORDER_CONSTANT, value=(255, 255, 255))


def _legendas(texto, dur, fonte_nome="Montserrat-ExtraBold.ttf"):
    """[(t0, t1, imagem RGBA)] — fala quebrada em pedaços de até 2 linhas, tempo proporcional ao tamanho."""
    if not texto:
        return []
    fonte = fx_acabamento._fonte(fonte_nome, 46)
    palavras, pedacos, cur = texto.split(), [], []
    for w in palavras:
        cur.append(w)
        if len(" ".join(cur)) >= 64 or w.endswith((".", "!", "?")) and len(" ".join(cur)) > 30:
            pedacos.append(" ".join(cur))
            cur = []
    if cur:
        pedacos.append(" ".join(cur))
    total = sum(len(p) for p in pedacos)
    fala = max(0.5, dur - FOLGA)
    out, t = [], 0.0
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    for p in pedacos:
        linhas, ln = [], ""
        for w in p.split():
            tst = (ln + " " + w).strip()
            if ln and d0.textlength(tst, font=fonte) > W * 0.62:
                linhas.append(ln)
                ln = w
            else:
                ln = tst
        linhas.append(ln)
        alt = len(linhas) * 58 + 24
        im = Image.new("RGBA", (W, alt), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i, l_ in enumerate(linhas):
            tw = d.textlength(l_, font=fonte)
            d.text(((W - tw) / 2, 10 + i * 58), l_, font=fonte, fill=(255, 255, 255),
                   stroke_width=5, stroke_fill=(0, 0, 0))
        d_ = fala * len(p) / max(1, total)
        arr = np.asarray(im)
        out.append((t, t + d_, cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2BGR), arr[..., 3].astype(np.float32) / 255))
        t += d_
    return out


def _rosto_zoom(painel_img, painel_orig, w, h):
    """Recorte do rosto do painel no tamanho w x h (enquadrado com folga)."""
    x, y, fw, fh = fx_parallax.rosto_principal(painel_orig)
    cx, cy = x + fw / 2, y + fh * 0.6
    lado_w = fw * 1.9  # rosto ocupa ~metade do quadro (2,6 deixava rosto pequeno quase igual ao painel)
    lado_h = lado_w * h / w
    x0, y0 = int(max(0, cx - lado_w / 2)), int(max(0, cy - lado_h / 2))
    x1, y1 = int(min(painel_img.shape[1], x0 + lado_w)), int(min(painel_img.shape[0], y0 + lado_h))
    return cv2.resize(painel_img[y0:y1, x0:x1], (w, h), interpolation=cv2.INTER_CUBIC)


def _personagem(painel_orig, painel_img, alt):
    """Personagem recortado (BGR + alfa) com altura alt e contorno de luz."""
    m = fx_parallax.mascara(painel_orig)
    if m.shape[:2] != painel_img.shape[:2]:
        m = cv2.resize(m, (painel_img.shape[1], painel_img.shape[0]))
    a = cv2.GaussianBlur((m > 110).astype(np.float32), (0, 0), 1.2)
    ys, xs = np.nonzero(a > 0.5)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    img, a = painel_img[y0:y1, x0:x1], a[y0:y1, x0:x1]
    sc = alt / img.shape[0]
    img = cv2.resize(img, (int(img.shape[1] * sc), alt), interpolation=cv2.INTER_CUBIC)
    a = cv2.resize(a, (img.shape[1], alt))
    brilho = np.clip(cv2.GaussianBlur(cv2.dilate(a, np.ones((9, 9), np.uint8)), (0, 0), 3) - a, 0, 1)
    img = (img * a[..., None] + 255 * brilho[..., None] * (1 - a[..., None])).astype(np.uint8)
    return img, np.clip(a + brilho, 0, 1)


def _titulo_capitulo(capa_img, n, obra, idioma=None):
    """Quadro de abertura do capítulo (2,5 s): capa borrada + CAPÍTULO N."""
    fr = cv2.resize(_fundo(capa_img), (W, H))
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(im)
    f1, f2 = fx_acabamento._fonte("LuckiestGuy-Regular.ttf", 150), fx_acabamento._fonte("Montserrat-ExtraBold.ttf", 54)
    import idiomas
    t1, t2 = f"{idiomas.texto(idioma, 'capitulo').upper()} {n}", obra.upper()
    if idioma:  # alfabeto do idioma (hindi/tailandês) precisa da fonte dele
        f1 = fx_acabamento._fonte(idiomas.IDIOMAS[idioma].get("fonte_png") or "Montserrat-ExtraBold.ttf", 130)
    d.text(((W - d.textlength(t1, font=f1)) / 2, H * 0.36), t1, font=f1, fill=(255, 212, 0),
           stroke_width=9, stroke_fill=(0, 0, 0))
    d.text(((W - d.textlength(t2, font=f2)) / 2, H * 0.36 + 175), t2, font=f2, fill=(255, 255, 255),
           stroke_width=5, stroke_fill=(0, 0, 0))
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def _enc():
    if fx_parallax._qsv():
        return ["-c:v", "h264_qsv", "-global_quality", "22", "-preset", "medium", "-pix_fmt", "nv12"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p"]


def renderizar_capitulo(obra, n, pasta, skip_ini, skip_fim, titulo_obra, out_mp4, idioma=None):
    t_ini = time.time()
    tmp = SAIDA / obra / f"_tmp_cap{n:02d}{'_' + idioma if idioma else ''}"
    tmp.mkdir(parents=True, exist_ok=True)
    paineis, capa_orig, recap_pt, recap = _dados_capitulo(pasta, skip_ini, skip_fim, idioma)
    imagens, scores = _censurar(paineis, recap_pt, tmp)
    momentos = _momentos(paineis, imagens, scores, recap, tmp, idioma, recap_pt)
    import idiomas
    fonte_leg = (idiomas.IDIOMAS.get(idioma, {}).get("fonte_png") if idioma else None) or "Montserrat-ExtraBold.ttf"
    lay = {}
    for m in momentos:
        lay[m["layout"]] = lay.get(m["layout"], 0) + 1
    log(f"  cap {n}: {len(momentos)} momentos {lay}, {sum(i != p for i, p in zip(imagens, paineis))} censurados")

    # voz: cada momento com sua duração (fala + respiro), na ordem
    T_ABRE = 2.5
    partes = [tmp / "_abre.wav"]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t",
                    f"{T_ABRE}", str(partes[0])], check=True)
    for k, m in enumerate(momentos):
        pw = tmp / f"_m{k:03d}.wav"
        src = ["-i", str(m["wav"])] if m["wav"] else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono"]
        subprocess.run(["ffmpeg", "-y", "-v", "error", *src, "-af", f"aresample=48000,apad,atrim=0:{m['dur']:.3f}",
                        "-ac", "1", "-ar", "48000", "-t", f"{m['dur']:.3f}", str(pw)], check=True)
        partes.append(pw)
    lista = tmp / "_voz.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
    voz = tmp / "_voz.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-c", "copy", str(voz)], check=True)

    # vídeo: quadros em OpenCV -> Quick Sync
    bruto = tmp / "_bruto.mp4"
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", str(voz), *_enc(), "-c:a", "aac", "-b:a", "192k",
                             "-shortest", str(bruto)], stdin=subprocess.PIPE)
    try:
        abre = _titulo_capitulo(cv2.imread(str(capa_orig)), n, titulo_obra, idioma)
        for f in range(int(T_ABRE * FPS)):
            k = min(1.0, f / 12)
            proc.stdin.write(cv2.addWeighted(abre, k, np.zeros_like(abre), 1 - k, 0).tobytes())
        ultimo = abre
        imgs = [cv2.imread(str(m["img"])) for m in momentos]
        cartoes = [_com_borda(_cartao(im)) for im in imgs]
        apagados = [cv2.convertScaleAbs(c[:CH + 12], alpha=0.45) for c in cartoes]  # vizinhos da tira
        fundos = [cv2.resize(_fundo(im), (W, H)) for im in imgs]
        branco = np.full((H, W, 3), 255, np.uint8)
        for k, m in enumerate(momentos):
            leg = _legendas(m["texto"], m["dur"], fonte_leg)
            lay, trans = m["layout"], m.get("trans", "desliza")
            extra = None
            if lay == "close":
                extra = _com_borda(_rosto_zoom(imgs[k], m["painel"], int(0.44 * W), int(0.80 * H)), 8)
            elif lay == "recorte":
                extra = _personagem(m["painel"], imgs[k], int(0.98 * H))
            elif lay == "cheio":  # painel na largura toda; a câmera desce por ele (ou fica no meio, se baixo)
                extra = cv2.resize(imgs[k], (W, int(imgs[k].shape[0] * W / imgs[k].shape[1])),
                                   interpolation=cv2.INTER_CUBIC)
            lado = lay in ("close", "recorte", "duo")
            n_fr = max(1, int(round(m["dur"] * FPS)))
            for f in range(n_fr):
                t = f / FPS
                e = min(1.0, t / T_TROCA)
                e = 1 - (1 - e) ** 3
                desl = (1 - e) * PASSO if trans == "desliza" else 0.0
                desl_y = (1 - e) * 0.7 * H if trans == "sobe" else 0.0
                if lay == "cheio":
                    if extra.shape[0] > H:
                        p_ = min(1.0, t / m["dur"])
                        y0 = int((extra.shape[0] - H) * (p_ * p_ * (3 - 2 * p_)))
                        fr = extra[y0:y0 + H].copy()
                    else:
                        fr = fundos[k].copy()
                        _colar(fr, extra, W / 2 + desl, H / 2 + desl_y)
                else:
                    fr = fundos[k].copy() if e >= 1 or k == 0 else cv2.addWeighted(fundos[k], e, fundos[k - 1], 1 - e, 0)
                    cx_ativo = (0.70 * W if lay == "duo" else 0.27 * W) if lado else W / 2
                    if lay == "tira":  # vizinhos apagados dos lados
                        for j, dx in ((k - 1, -PASSO), (k + 1, PASSO)):
                            if 0 <= j < len(momentos):
                                _colar(fr, apagados[j], W / 2 + dx + desl, H / 2 + desl_y * 0.3)
                    elif lay == "duo" and k > 0:  # o painel anterior fica à esquerda, apagado
                        _colar(fr, apagados[k - 1], 0.27 * W, H / 2)
                    atual = _janela(cartoes[k], t, m["dur"])
                    deriva = 18 * (t / m["dur"] - 0.5)  # deslize lento (barato; zoom por quadro custava caro)
                    _colar(fr, atual, cx_ativo + desl + deriva, H / 2 + desl_y)
                    if lay == "close":
                        zz = 1.0 + 0.06 * (t / m["dur"])
                        ex = cv2.resize(extra, (int(extra.shape[1] * zz), int(extra.shape[0] * zz)))
                        _colar(fr, ex, 0.73 * W + (1 - e) * 0.5 * W, H / 2)
                    elif lay == "recorte":
                        img_p, a_p = extra
                        sobe = (1 - e) * 0.25 * H
                        _colar(fr, img_p, 0.72 * W, H - img_p.shape[0] / 2 + sobe + 0.02 * H, a_p)
                if trans == "funde" and e < 1:
                    fr = cv2.addWeighted(fr, e, ultimo, 1 - e, 0)
                elif trans == "corte" and f < 4:
                    fr = cv2.addWeighted(fr, f / 4, branco, 1 - f / 4, 0)
                for t0, t1, lim, la in leg:
                    if t0 <= t < t1:
                        _colar(fr, lim, W / 2, H - 70 - lim.shape[0] / 2, la)
                proc.stdin.write(fr.tobytes())
            ultimo = fr
    finally:
        proc.stdin.close()
        proc.wait(timeout=1800)
    if proc.returncode != 0 or not bruto.exists():
        raise RuntimeError("encode do capítulo falhou")

    total = fx_acabamento.duracao(bruto)
    musica = fx_music.compose_dynamic_music(total, recap_pt.get("locucoes", []), fx_acabamento.TRILHAS_DIR, tmp)
    fx_acabamento.masterizar_audio(bruto, out_mp4, musica, [], tmp)
    info = {"cap": n, "duracao": fx_acabamento.duracao(out_mp4), "momentos": len(momentos), "layouts": lay,
            "trilhas": fx_music.ULTIMAS_FAIXAS, "censurados": sum(i != p for i, p in zip(imagens, paineis))}
    Path(out_mp4).with_suffix(".json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in tmp.iterdir():
        f.unlink(missing_ok=True)
    tmp.rmdir()
    log(f"  [OK] cap {n} longo: {Path(out_mp4).name} ({info['duracao'] / 60:.1f} min, {time.time() - t_ini:.0f} s)")
    return info


# ─── compilação ──────────────────────────────────────────────────────────────
def _tempo(s):
    s = int(s)
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def _capa_compilacao(fontes, titulo_obra, out_jpg):
    """Capa 16:9 da compilação no estilo sensual (fx_acabamento), com painéis de todos os capítulos."""
    paineis, info = [], {}
    for _n, (pasta, ini, fim) in sorted(fontes.items()):
        try:
            ps, _c, recap, _r = _dados_capitulo(pasta, ini, fim)
        except FileNotFoundError:
            continue
        locs, descs = recap.get("locucoes", []), recap.get("descriptions", [])
        for k, p in enumerate(ps):
            loc = locs[k] if k < len(locs) else {}
            info[str(p)] = {"desc": descs[k] if k < len(descs) else "", "fala": loc.get("text", ""),
                            "persona": loc.get("persona"), "genero": loc.get("gender")}
        paineis += ps
    return fx_acabamento.gerar_capa(paineis, titulo_obra, None, out_jpg, info=info) if paineis else None


def compilar(obra, caps, titulo_obra, fontes=None, idioma=None):
    """Junta capNN.mp4 (já renderizados, mesmo formato) num vídeo só + lista de capítulos com minuto.
    fontes = {n: (pasta, skip_ini, skip_fim)} pra capa."""
    pasta = SAIDA / obra / (idioma or "")
    arqs = [(n, pasta / f"cap{n:02d}.mp4") for n in caps if (pasta / f"cap{n:02d}.mp4").exists()]
    if not arqs:
        return None
    a, b = arqs[0][0], arqs[-1][0]
    out = pasta / f"{obra}_caps{a:02d}-{b:02d}.mp4"
    lista = pasta / "_lista.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for _n, p in arqs), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                    "-movflags", "+faststart", str(out)], check=True)
    lista.unlink(missing_ok=True)
    capitulos, t = [], 0.0
    for n, p in arqs:
        capitulos.append(f"{_tempo(t)} Capítulo {n}")
        t += fx_acabamento.duracao(p)
    meta = {"obra": obra, "titulo": f"{titulo_obra} — Capítulos {a} a {b} (Recap completo)",
            "caps": [n for n, _ in arqs], "duracao": t, "capitulos_descricao": "\n".join(capitulos)}
    if fontes:
        try:
            meta["capa"] = str(_capa_compilacao({n: fontes[n] for n, _ in arqs if n in fontes}, titulo_obra,
                                                out.with_suffix(".capa.jpg")) or "")
        except Exception as e:  # noqa: BLE001
            log(f"  [!] capa da compilação falhou: {str(e)[:120]}")
    out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    # só a compilação mais nova fica (as outras são prefixo dela; 41 caps somariam ~100 GB). A que já foi
    # postada ("postado" no .json) fica: o backup pro Drive usa o caminho dela.
    for velho in pasta.glob(f"{obra}_caps*.mp4"):
        if velho != out and "postado" not in fx_music._ler_json(velho.with_suffix(".json"), {}):
            for f in (velho, velho.with_suffix(".json"), velho.with_suffix(".capa.jpg")):
                f.unlink(missing_ok=True)
    log(f"  [OK] compilação: {out.name} ({t / 60:.1f} min, {len(arqs)} caps)")
    return out


def main():
    ap = argparse.ArgumentParser(description="vídeo longo 16:9 da obra (reaproveita o cache do vertical)")
    ap.add_argument("--obra", required=True, help="slug da obra (config/fila.json)")
    ap.add_argument("--caps", required=True, help="ex.: 1-10")
    ap.add_argument("--compilar", action="store_true", help="junta os capítulos prontos num vídeo só")
    ap.add_argument("--refazer", action="store_true", help="renderiza de novo mesmo se o capNN.mp4 existir")
    ap.add_argument("--idioma", help="versão em outra língua (usa a tradução e as vozes do vertical)")
    a = ap.parse_args()
    import fila
    c = fila.cfg()
    obra = next((o for o in c["obras"] if o["slug"] == a.obra), {"slug": a.obra, "titulo": a.obra})
    est = fila.ler_estado()
    a0, a1 = (int(x) for x in a.caps.split("-")) if "-" in a.caps else (int(a.caps), int(a.caps))
    caps = list(range(a0, a1 + 1))
    dest = SAIDA / a.obra / (a.idioma or "")
    dest.mkdir(parents=True, exist_ok=True)
    pastas = {n_: (k, p) for k, o, n_, p in fila.capitulos() if o["slug"] == a.obra}
    fontes = {n: (p, int(est.get(k, {}).get("skip", {}).get("inicio", 0)),
                  int(est.get(k, {}).get("skip", {}).get("fim", 0))) for n, (k, p) in pastas.items()}
    for n in caps:
        out = dest / f"cap{n:02d}.mp4"
        if (out.exists() and not a.refazer) or n not in pastas:
            continue
        chave, pasta = pastas[n]
        sk = est.get(chave, {}).get("skip", {})
        try:
            renderizar_capitulo(a.obra, n, pasta, int(sk.get("inicio", 0)), int(sk.get("fim", 0)), obra["titulo"], out,
                                a.idioma)
        except FileNotFoundError as e:
            log(f"  cap {n}: {e}")
    if a.compilar:
        compilar(a.obra, caps, obra["titulo"], fontes, a.idioma)


if __name__ == "__main__":
    main()
