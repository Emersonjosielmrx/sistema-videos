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
FOLGA = 0.45                            # s de respiro depois de cada fala (longo é pra contar mais história)
LEITURA_CPS = 15                        # letras/s de leitura dos balões (o painel não sai antes de dar pra ler)
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
    # mesmo reforço do vertical (16/10): visão em painel de score baixo + painéis forçados pela análise do vídeo
    scores, _subiram = censura_visual.reforcar_scores(paineis, scores)
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
# frases EXTRAS do narrador por capítulo (o deitado conta mais história que o vertical). pt = voz Gemini (cota
# dividida com a produção): com moderação; outra língua = edge-tts (grátis): à vontade. HIPER_LONGO_EXTRAS=0 desliga.
EXTRAS_PT, EXTRAS_LINGUA = 12, 30


def _extras(recap, descs, narr_file, idioma=None):
    """{painel: frase extra do narrador} (cache por capítulo/língua ao lado do roteiro). {} se o LLM falhar."""
    if os.environ.get("HIPER_LONGO_EXTRAS", "1") == "0":
        return {}
    destino = Path(narr_file).with_name(Path(narr_file).stem + f"_longo_extra{'_' + idioma if idioma else ''}.json")
    if destino.exists():
        return {int(k): v for k, v in _ler_json_tolerante(destino).items()}
    import gemini_llm
    import idiomas
    locs = recap.get("locucoes", [])
    n_max = EXTRAS_LINGUA if idioma else EXTRAS_PT
    linhas = "\n".join(f"{k}: [{l.get('persona')}] {l.get('text', '')} | cena: {descs[k] if k < len(descs) else ''}"
                       for k, l in enumerate(locs))
    lingua = f"em {idiomas.IDIOMAS[idioma]['nome']}" if idioma else "em português do Brasil"
    pedido = (f"Roteiro de um capítulo de manhwa (uma fala por painel) com a cena de cada painel:\n{linhas[:14000]}\n\n"
              f"Esta versão do vídeo é mais lenta e conta MAIS da história. Escolha até {n_max} painéis onde uma frase "
              "EXTRA do narrador ajuda quem nunca leu: o que a cena mostra e a fala não disse, a fala de balão (está "
              "entre aspas na cena) que não foi dita, quem é quem, o que acabou de acontecer. Use SÓ o que está no "
              "roteiro e nas cenas: NÃO invente fato, motivo, passado nem segredo; nada de metáfora ou frase de "
              "efeito; não fale de câmera/enquadramento. Tom de narrador de recap conversando (como o resto do "
              "roteiro): a ação + o que ela quer dizer na cena. Frase curta (8-20 palavras), presente, sem repetir a "
              "fala do painel.\n❌ \"Yeseul retira o calçado em um plano de detalhe.\" (descreve a câmera)\n"
              "❌ \"Ela veio cobrar uma dívida de sangue.\" (inventa)\n"
              "✅ \"Nisso, ela já vai tirando o sapato, como se a casa fosse dela.\"\n"
              f"Escreva {lingua}. Responda SÓ JSON {{\"<número do painel>\": \"frase\"}}.")
    try:
        txt = gemini_llm.generate_text(pedido, max_tokens=3000, temperature=0.7, max_attempts=3)
        d = json.loads(re.search(r"\{.*\}", txt or "", re.S).group(0))
        ext = {int(k): str(v).strip() for k, v in d.items() if str(k).isdigit() and 0 <= int(k) < len(locs)
               and len(str(v).split()) >= 4}
        ext = dict(sorted(ext.items())[:n_max])
    except Exception as e:  # noqa: BLE001
        log(f"  [!] frases extras do longo: LLM falhou ({str(e)[:80]})")
        return {}
    destino.write_text(json.dumps(ext, ensure_ascii=False, indent=1), encoding="utf-8")
    return ext


def _falar_extra(texto, wav, idioma=None, obra_elenco=None):
    """Voz do narrador pra frase extra. pt: a narradora do elenco da obra (a mesma do vertical); se o motor do pt
    for o Gemini, libera o Gemini SÓ pra ela (o resto do longo é cache-only)."""
    if idioma:
        import idiomas
        return idiomas.falar(texto, wav, "Narrador", None, idioma)
    os.environ["TTS_CACHE_ONLY"] = "0"
    try:
        import elenco
        return elenco.falar(obra_elenco, texto, wav, "Narrador", None)
    finally:
        os.environ["TTS_CACHE_ONLY"] = "1"


def _momentos(paineis, imagens, scores, recap, tmp, idioma=None, recap_pt=None, extras=None):
    """Lista de momentos: {img, painel (original, p/ máscara/rosto), wav, dur, texto, layout, trans}.
    layout: tira | cheio (painel na largura toda, câmera desce) | duo (anterior + atual lado a lado) |
    close | recorte. Nunca a mesma transição/layout comum 3 vezes seguidas. extras: {painel: frase do narrador}
    que entra logo depois da fala do painel."""
    locs = recap.get("locucoes", [])
    obra_elenco = None
    if not idioma:  # pt: vozes do elenco fixo da obra, as MESMAS do vertical (até 16/10 o 16:9 usava as do Gemini)
        import elenco
        obra_elenco = elenco.obra_de(Path(paineis[0]).parent) if paineis else None
        locs = elenco.normalizar(obra_elenco, locs)
    descs = (recap_pt or recap).get("descriptions", [])
    # 17/10: a curva do clímax (elenco.curva_climax) também no 16:9 — sem ela o deitado saía com a voz reta
    # e, como a chave do cache inclui a velocidade, regravava as falas do clímax diferentes do vertical.
    impactos = [i["fala"] for i in ((recap_pt or recap).get("_editorial") or {}).get("impactos", [])
                if isinstance(i.get("fala"), int)]
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
                ok = elenco.falar(obra_elenco, texto, wav, persona, gen, indice=k, impactos=impactos,
                                  total=len(locs))
            if not ok:
                wav = None
        extra = (extras or {}).get(k)
        if extra:
            wav_x = tmp / f"voz_{k:03d}_x.wav"
            if _falar_extra(extra, wav_x, idioma, obra_elenco):
                if wav:  # fala do painel + 0,25 s + frase extra, num wav só
                    junto = tmp / f"voz_{k:03d}_j.wav"
                    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-i", str(wav_x), "-filter_complex",
                                    "[0:a]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur=0.25[a];"
                                    "[1:a]aresample=48000,aformat=channel_layouts=mono[b];[a][b]concat=n=2:v=0:a=1",
                                    str(junto)], check=True)
                    wav, texto = junto, f"{texto} {extra}"
                else:
                    wav, texto = wav_x, extra
        # o painel fica pelo menos o tempo de ler os balões dele (texto entre aspas na descrição do painel)
        leitura = 1.0 + sum(len(q) for q in re.findall(r'["“]([^"”]+)["”]', desc)) / LEITURA_CPS
        fala = _wav_dur(wav) if wav else 0.0
        dur = max(fala + FOLGA if wav else 2.2, leitura)
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
        out.append({"img": imagens[k], "painel": p, "wav": wav, "dur": max(dur, 1.0), "fala": fala,
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


def _legendas(texto, fala, fonte_nome="Montserrat-ExtraBold.ttf"):
    """[(t0, t1, imagem RGBA)] — fala quebrada em pedaços de até 2 linhas, tempo proporcional ao tamanho,
    dentro da duração da voz (fala, em s)."""
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
    fala = max(0.5, fala)
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


def _titulo_capitulo(capa_img, n, idioma=None):
    """Quadro de abertura do capítulo (2,5 s): capa borrada + CAPÍTULO N. Sem o nome da obra (dono, 15/10: o nome
    não pode aparecer em lugar nenhum — direitos autorais)."""
    fr = cv2.resize(_fundo(capa_img), (W, H))
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(im)
    f1 = fx_acabamento._fonte("LuckiestGuy-Regular.ttf", 150)
    import idiomas
    t1 = f"{idiomas.texto(idioma, 'capitulo').upper()} {n}"
    if idioma:  # alfabeto do idioma (hindi/tailandês) precisa da fonte dele
        f1 = fx_acabamento._fonte(idiomas.IDIOMAS[idioma].get("fonte_png") or "Montserrat-ExtraBold.ttf", 130)
    d.text(((W - d.textlength(t1, font=f1)) / 2, H * 0.40), t1, font=f1, fill=(255, 212, 0),
           stroke_width=9, stroke_fill=(0, 0, 0))
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
    narr = hp_paineis.arquivo_narracao(pasta, len(paineis), 1, skip_fim, skip_ini)
    extras = _extras(recap, recap_pt.get("descriptions", []), narr, idioma)
    if extras:
        log(f"  cap {n}: {len(extras)} frases extras do narrador (o deitado conta mais história)")
    momentos = _momentos(paineis, imagens, scores, recap, tmp, idioma, recap_pt, extras)
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
        abre = _titulo_capitulo(cv2.imread(str(capa_orig)), n, idioma)
        for f in range(int(T_ABRE * FPS)):
            k = min(1.0, f / 12)
            proc.stdin.write(cv2.addWeighted(abre, k, np.zeros_like(abre), 1 - k, 0).tobytes())
        ultimo = abre
        imgs = [cv2.imread(str(m["img"])) for m in momentos]
        cartoes = [_com_borda(_cartao(im)) for im in imgs]
        apagados = [cv2.convertScaleAbs(c[:CH + 12], alpha=0.45) for c in cartoes]  # vizinhos da tira
        fundos = [cv2.resize(_fundo(im), (W, H + 30)) for im in imgs]

        def _fundo_pan(idx, prog):
            """Fundo com pan vertical lento (0→30px)."""
            y0 = int(30 * prog)
            return fundos[idx][y0:y0 + H].copy()

        branco = np.full((H, W, 3), 255, np.uint8)
        for k, m in enumerate(momentos):
            leg = _legendas(m["texto"], m["fala"], fonte_leg)
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
                        fr = _fundo_pan(k, t / max(0.1, m["dur"]))
                        _colar(fr, extra, W / 2 + desl, H / 2 + desl_y)
                else:
                    prog_t = t / max(0.1, m["dur"])
                    if e >= 1 or k == 0:
                        fr = _fundo_pan(k, prog_t)
                    else:
                        f1, f2 = _fundo_pan(k, prog_t), _fundo_pan(k - 1, 1.0)  # o anterior parou no fim do pan
                        fr = cv2.addWeighted(f1, e, f2, 1 - e, 0)
                    cx_ativo = (0.70 * W if lay == "duo" else 0.27 * W) if lado else W / 2
                    if lay == "tira":  # vizinhos apagados dos lados
                        for j, dx in ((k - 1, -PASSO), (k + 1, PASSO)):
                            if 0 <= j < len(momentos):
                                _colar(fr, apagados[j], W / 2 + dx + desl, H / 2 + desl_y * 0.3)
                    elif lay == "duo" and k > 0:  # o painel anterior fica à esquerda, apagado
                        _colar(fr, apagados[k - 1], 0.27 * W, H / 2)
                    atual = _janela(cartoes[k], t, m["dur"])
                    prog = t / max(0.1, m["dur"])
                    deriva = 18 * (prog - 0.5)
                    zb = 1.0 + 0.04 * prog  # respiração: o quadro inteiro (com a borda) cresce devagar, sem cortar balão
                    if zb > 1.001:
                        atual = cv2.resize(atual, (round(atual.shape[1] * zb), round(atual.shape[0] * zb)),
                                           interpolation=cv2.INTER_LINEAR)
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
    # quando cada momento está na tela (painel e layout): a análise do vídeo pronto (revisao_video) diz qual
    # painel apareceu sem censura — em "tira"/"duo" os vizinhos também ficam visíveis, apagados
    tempos, t_ac = [], T_ABRE
    for m in momentos:
        d = max(1, int(round(m["dur"] * FPS))) / FPS
        tempos.append([round(t_ac, 2), round(t_ac + d, 2), Path(m["painel"]).name, m["layout"]])
        t_ac += d
    info = {"cap": n, "duracao": fx_acabamento.duracao(out_mp4), "momentos": len(momentos), "layouts": lay,
            "trilhas": fx_music.ULTIMAS_FAIXAS, "censurados": sum(i != p for i, p in zip(imagens, paineis)),
            "momentos_tempo": tempos}
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


def _capa_compilacao(fontes, titulo_obra, out_jpg, selo="", idioma=None):
    """Capa 16:9 da compilação: redesenhada (bin/capa_ia, frase de premissa + selo "COMPLETO a-b") ou, se o gateway
    não gerar, a de painel (fx_acabamento) com painéis de todos os capítulos."""
    try:
        import capa_ia
        obra = capa_ia.obra_do_painel(Path(next(iter(fontes.values()))[0]) / "x.jpg")
        frase = (capa_ia._cfg_obra(obra) or {}).get("frase_compilado") or titulo_obra
        if capa_ia.capas(obra, frase if not idioma else "", selo, out_jpg, n=3, roteiro=f"Premissa: {frase}",
                         idioma=idioma or "pt", chave=f"caps{min(fontes):02d}-{max(fontes):02d}"):
            return out_jpg
    except Exception as e:  # noqa: BLE001
        log(f"  [!] capa IA da compilação falhou ({str(e)[:120]}) -> capa de painel")
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


def _cap_do_meio(durs, minimo=240.0):
    """Índice do capítulo depois do qual entra a chamada de like do meio (voz humana, bin/intros_voz.py): a troca de
    capítulo mais perto de 1/3 do vídeo, nunca antes de 4 min. None se nenhuma troca servir."""
    total, acc, bordas = sum(durs), 0.0, []
    for k, d in enumerate(durs[:-1]):
        acc += d
        if acc >= minimo:
            bordas.append((abs(acc - total / 3), k))
    return min(bordas)[1] if bordas else None


def _juntar(arquivos, out, pasta):
    lista = pasta / "_lista.txt"
    lista.write_text("".join(f"file '{Path(p).as_posix()}'\n" for p in arquivos), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                    "-movflags", "+faststart", str(out)], check=True)
    lista.unlink(missing_ok=True)


def _cta_compilado(arqs, fontes, titulo_obra, capa_jpg, pasta):
    """Pedido de like falado no FIM do compilado, uma vez só: a fala que o vertical do último capítulo ganhou depois
    do último painel (narration.gerar_cta_fim -> _cta_fim no cache da narração), sobre a capa do compilado.
    {mp4, dur, id, texto} ou None. Mesmo formato dos capNN.mp4 (emenda sem re-encode), senão fica de fora."""
    import elenco
    import intros_voz
    import narration
    n = arqs[-1][0]
    if n not in (fontes or {}):
        return None
    pasta_c, skip_ini, skip_fim = fontes[n]
    paineis, _capa, recap_pt, _r = _dados_capitulo(pasta_c, skip_ini, skip_fim)
    tinha = bool((recap_pt.get("_cta_fim") or {}).get("texto"))
    cta = narration.gerar_cta_fim(recap_pt, titulo_obra)
    if not cta:
        return None
    if not tinha:  # capítulo de antes de 18/10: a fala fica no cache e o próximo compilado usa a mesma
        narr = hp_paineis.arquivo_narracao(pasta_c, len(paineis), 1, skip_fim, skip_ini)
        Path(narr).write_text(json.dumps(recap_pt, ensure_ascii=False, indent=2), encoding="utf-8")
    wav = pasta / "_abertura_fim_cta.wav"
    if not _falar_extra(cta["texto"], wav, None, elenco.obra_de(Path(paineis[0]).parent) if paineis else None):
        return None
    s0, s1 = fx_acabamento._limites_fala(str(wav))
    pal = [(w["w"], round(w["s"], 2), round(w["e"], 2))
           for w in fx_acabamento._proporcional(cta["texto"].split(), s0, s1, 0)]
    fundo = Path(capa_jpg) if capa_jpg and Path(capa_jpg).is_file() else pasta / "_abertura_fim_fundo.jpg"
    if not fundo.is_file():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-sseof", "-6", "-i", str(arqs[-1][1]), "-frames:v", "1",
                        str(fundo)], check=True, timeout=60)
    mp4 = pasta / f"_abertura_fim_{cta['id']}.mp4"
    intros_voz.segmento({"id": f"cta_{cta['id']}", "arquivo": str(wav), "palavras": pal, "texto": cta["texto"]},
                        fundo, mp4, W, H, FPS, _enc(), semente=f"cta|{n}")
    wav.unlink(missing_ok=True)
    if intros_voz._formato(mp4) != intros_voz._formato(arqs[0][1]):
        log("  [!] CTA do fim do compilado saiu em formato diferente dos capítulos — fica de fora")
        mp4.unlink(missing_ok=True)
        return None
    return {"mp4": mp4, "dur": fx_acabamento.duracao(mp4), "id": cta["id"], "texto": cta["texto"]}


def compilar(obra, caps, titulo_obra, fontes=None, idioma=None):
    """Junta capNN.mp4 (já renderizados, mesmo formato) num vídeo só + lista de capítulos com minuto.
    fontes = {n: (pasta, skip_ini, skip_fim)} pra capa. Em pt o vídeo abre com uma voz humana (bin/intros_voz.py:
    cada compilado postado com uma abertura diferente, pra medir qual rende mais)."""
    pasta = SAIDA / obra / (idioma or "")
    arqs = [(n, pasta / f"cap{n:02d}.mp4") for n in caps if (pasta / f"cap{n:02d}.mp4").exists()]
    if not arqs:
        return None
    a, b = arqs[0][0], arqs[-1][0]
    out = pasta / f"{obra}_caps{a:02d}-{b:02d}.mp4"
    meta = {"obra": obra, "titulo": f"{titulo_obra} — Capítulos {a} a {b} (Recap completo)",
            "caps": [n for n, _ in arqs]}
    if fontes:
        try:
            meta["capa"] = str(_capa_compilacao({n: fontes[n] for n, _ in arqs if n in fontes}, titulo_obra,
                                                out.with_suffix(".capa.jpg"), selo=f"COMPLETO {a}-{b}",
                                                idioma=idioma) or "")
        except Exception as e:  # noqa: BLE001
            log(f"  [!] capa da compilação falhou: {str(e)[:120]}")
    durs = [fx_acabamento.duracao(p) for _n, p in arqs]
    abertura = meio = k_meio = fim = None
    if not idioma:
        try:
            import intros_voz
            abertura = intros_voz.para_compilado(obra, arqs[0][1], meta.get("capa"), pasta, _enc(), W, H, FPS)
        except Exception as e:  # noqa: BLE001
            log(f"  [!] abertura com voz humana falhou ({str(e)[:120]}) — compilação sem abertura")
        k_meio = _cap_do_meio(durs)
        if k_meio is not None:
            try:
                import intros_voz
                meio = intros_voz.para_compilado(obra, arqs[0][1], meta.get("capa"), pasta, _enc(), W, H, FPS,
                                                 lugar="meio", evitar_canal=(abertura or {}).get("canal"))
            except Exception as e:  # noqa: BLE001
                log(f"  [!] chamada de like do meio falhou ({str(e)[:120]}) — compilação sem ela")
        if os.environ.get("HIPER_CTA_FIM", "1") != "0":
            try:
                fim = _cta_compilado(arqs, fontes, titulo_obra, meta.get("capa"), pasta)
            except Exception as e:  # noqa: BLE001
                log(f"  [!] CTA do fim do compilado falhou ({str(e)[:120]}) — compilação sem ele")

    def _ordem():
        lista = [abertura["mp4"]] if abertura else []
        for k, (_n, p) in enumerate(arqs):
            lista.append(p)
            if meio and k == k_meio:
                lista.append(meio["mp4"])
        if fim:
            lista.append(fim["mp4"])
        return lista

    _juntar(_ordem(), out, pasta)
    if abertura or meio or fim:  # confere cada emenda; a que der erro de decodificação sai e o vídeo é juntado de novo
        import intros_voz
        t_ab = abertura["dur"] if abertura else 0.0
        ok_ab = not abertura or intros_voz.emenda_ok(out, t_ab)
        ok_meio = True
        if meio:
            t0 = t_ab + sum(durs[:k_meio + 1])
            ok_meio = intros_voz.emenda_ok(out, t0) and intros_voz.emenda_ok(out, t0 + meio["dur"])
        ok_fim = not fim or intros_voz.emenda_ok(out, t_ab + sum(durs) + (meio["dur"] if meio else 0.0))
        if not ok_ab:
            log("  [!] emenda da abertura com o capítulo 1 deu erro — compilação sem abertura")
            abertura = None
        if not ok_meio:
            log("  [!] emenda da chamada do meio deu erro — compilação sem ela")
            meio = None
        if not ok_fim:
            log("  [!] emenda do CTA do fim deu erro — compilação sem ele")
            fim = None
        if not (ok_ab and ok_meio and ok_fim):
            _juntar(_ordem(), out, pasta)
        for f in pasta.glob("_abertura_*"):
            f.unlink(missing_ok=True)
    if abertura:
        meta["intro_voz"] = {k: abertura[k] for k in ("id", "canal", "texto")} | {"dur": round(abertura["dur"], 2)}
        log(f"  abertura com voz humana: {abertura['id']} ({abertura['canal']}, {abertura['dur']:.1f} s)")
    if meio:
        meta["intro_meio"] = {k: meio[k] for k in ("id", "canal", "texto")} | {
            "dur": round(meio["dur"], 2), "depois_do_cap": arqs[k_meio][0]}
        log(f"  chamada de like no meio: {meio['id']} ({meio['canal']}) depois do cap {arqs[k_meio][0]}")
    capitulos, t = [], (abertura["dur"] if abertura else 0.0)
    for k, (n, _p) in enumerate(arqs):
        capitulos.append(f"{_tempo(0 if k == 0 else t)} Capítulo {n}")  # a abertura conta dentro do capítulo 1
        t += durs[k]
        if meio and k == k_meio:
            t += meio["dur"]  # a chamada do meio conta dentro do capítulo de antes
    if fim:
        t += fim["dur"]  # conta dentro do último capítulo
        meta["cta_fim"] = {"id": fim["id"], "texto": fim["texto"], "dur": round(fim["dur"], 2)}
        log(f"  CTA do fim: {fim['id']} ({fim['dur']:.1f} s): {fim['texto'][:90]}")
    meta.update(duracao=t, capitulos_descricao="\n".join(capitulos))
    out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    # só a compilação mais nova fica (as outras são prefixo dela; 41 caps somariam ~100 GB). A que já foi
    # postada ("postado" no .json) fica: o backup pro Drive usa o caminho dela.
    # 23/10 (ordem da dona): o 16:9 avulso do capítulo (capsNN-NN) e o compilado 1..N convivem — um não apaga o outro
    avulso = lambda p: re.fullmatch(rf"{re.escape(obra)}_caps(\d+)-\1", p.stem) is not None  # noqa: E731
    for velho in pasta.glob(f"{obra}_caps*.mp4"):
        if avulso(out) or avulso(velho):
            continue
        if velho != out and "postado" not in fx_music._ler_json(velho.with_suffix(".json"), {}):
            for f in (velho, velho.with_suffix(".json"), velho.with_suffix(".capa.jpg"),
                      *pasta.glob(f"{velho.stem}.capa_v*.jpg")):
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
    # fila de render entre projetos (D:\video-fila, 17/10): 1 render pesado por vez no PC; falhou = segue.
    # Só RENDERIZAR capítulo pesa. Compilar (--compilar sem --refazer, com os capNN.mp4 prontos) é colar os
    # laterais já feitos: não entra na fila (17/10, o dono: "os compilados não precisam renderizar tudo de novo").
    import contextlib
    _vez = contextlib.nullcontext()
    try:
        _arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None  # noqa: E731
        _a, _, _b = (_arg("--caps") or "0").partition("-")
        _pasta = SAIDA / (_arg("--obra") or "") / (_arg("--idioma") or "")
        _so_cola = "--compilar" in sys.argv and "--refazer" not in sys.argv and all(
            (_pasta / f"cap{n:02d}.mp4").exists() for n in range(int(_a), int(_b or _a) + 1))
        if not _so_cola:
            sys.path.insert(0, r"D:\video-fila")
            import fila_render
            _vez = fila_render.vez("hipercool", "16:9 " + " ".join(sys.argv[1:])[:100])
    except Exception:  # noqa: BLE001
        pass
    with _vez:
        main()
