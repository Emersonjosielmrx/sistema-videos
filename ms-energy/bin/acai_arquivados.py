# -*- coding: utf-8 -*-
r"""acai_arquivados.py — repostagem dos STORIES ARQUIVADOS do Açaí O Precioso como Reels (dona 05/11 12h50: "use o
conteúdo deles que está em arquivado pra adicionar legenda MIX, cards, trilha e repostar, pois são os que não dependem
de Veo 3"). Vídeos em D:\ms-energy\assets\acai\arquivados (baixados da captura do arquivo às 08:40).

Cada vídeo: 720x1280 -> 1080x1920 (lanczos + nitidez leve), LEGENDA MIX palavra a palavra pela fala (faster-whisper
com tempo por palavra), selo @, trilha baixa com ducking pela voz, cartão final 3 s (Zap + endereço).
Saída: D:\ms-energy\videos\acai\fila_para_postar\arquivado_<id>\reel.mp4 + legenda.txt. NÃO posta.
Rodar com o Python do sistema (tem o faster-whisper):
    D:eoenvScriptspython.exe acai_arquivados.py [ids...]      # sem ids = todos (pula repetidos e os já feitos)
"""
import json
import random
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import acai  # noqa: E402
import legenda_mix  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ORIG = Path(r"D:\ms-energy\assets\acai\arquivados")
FILA = acai.SAIDA / "fila_para_postar"
FONTES = Path(r"D:\recapd-ambientes\producao\workspace\assets\fonts")
TRILHAS = Path(r"D:\hipercool-materiais\assets\trilhas")
_MODELO = []


def _whisper():
    if not _MODELO:
        from faster_whisper import WhisperModel
        _MODELO.append(WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4))
    return _MODELO[0]


def palavras(video):
    segs, _ = _whisper().transcribe(str(video), language="pt", word_timestamps=True, vad_filter=True)
    out = []
    for s in segs:
        for w in s.words or []:
            t = re.sub(r"[^\wÀ-ú?!]", "", w.word.strip())
            if t:
                out.append((round(w.start, 2), round(w.end, 2), t.upper()))
    return out


def cartoes(ps, dur):
    """Grupos de até 3 palavras; sem fala = frases fixas da marca."""
    if len(ps) < 3:
        fr = ["AÇAÍ PURO", "O VERDADEIRO SABOR", "DO AÇAÍ NATIVO", "PEÇA O SEU"]
        passo = max(1.2, (dur - 0.6) / len(fr))
        return [[(0.4 + i * passo + k * 0.3, w) for k, w in enumerate(f.split())] + [0.4 + (i + 1) * passo - 0.05]
                for i, f in enumerate(fr)]
    out, grupo = [], []
    for i, (t0, t1, w) in enumerate(ps):
        grupo.append((t0, w))
        fim_frase = len(grupo) >= 3 or i + 1 == len(ps) or ps[i + 1][0] - t1 > 0.45
        if fim_frase:
            out.append(grupo + [min(dur, t1 + 0.25)])
            grupo = []
    return out


def _dur(v):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(v)], capture_output=True, text=True).stdout.strip() or 0)


def _tem_audio(v):
    return "audio" in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                      "stream=codec_type", "-of", "csv=p=0", str(v)], capture_output=True, text=True).stdout


def montar(video, pasta):
    dur = _dur(video)
    ps = palavras(video) if _tem_audio(video) else []
    estilos, linhas = legenda_mix.gerar(cartoes(ps, dur), 1080, 1920)
    (pasta / "mix.ass").write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
        "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding\n" + "\n".join(estilos) + "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, "
        "MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(linhas) + "\n", encoding="utf-8")
    # 05/11 13h dona ("deixe o máximo organizado pra fazer todas assim que ele decidir a cor"): ETAPA 1 (pesada, não
    # depende da cor) = 1080x1920 + legenda MIX pela fala -> base.mp4 com o áudio original. A ETAPA 2 (finalizar) põe
    # selo, cartão final e trilha na cor escolhida, em segundos.
    fontes = FONTES.as_posix().replace(":", "\\:")
    filtro = ("scale=1080:1920:flags=lanczos:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"unsharp=5:5:0.5,setsar=1,fps=30,subtitles=mix.ass:fontsdir='{fontes}',format=yuv420p")
    out = pasta / "base.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", filtro, "-c:v", "h264_qsv", "-global_quality", "20",
           "-c:a", "aac", "-b:a", "160k", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(pasta))
    if r.returncode != 0:
        cmd[cmd.index("h264_qsv"):cmd.index("h264_qsv") + 3] = ["libx264", "-crf", "19"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(pasta))
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-400:])
    texto = " ".join(w for _, _, w in ps).capitalize()
    corpo = texto[:180] + ("…" if len(texto) > 180 else "") if texto else "O verdadeiro sabor do açaí nativo 💜"
    leg = f"{corpo}\n\n📲 Pedidos e encomendas: {acai.ZAP}\n📍 {acai.ENDERECO} — {acai.CIDADE}\n\n{acai.HASHTAGS}"
    (pasta / "legenda.txt").write_text(leg, "utf-8")
    (pasta / "info.json").write_text(json.dumps({"origem": str(video), "dur": dur, "palavras": len(ps),
                                                 "audio": _tem_audio(video)}, ensure_ascii=False), "utf-8")
    return out


# 05/11 dona: "o vídeo ficou bom, só ficou com poucos cards" -> gancho no começo + card informativo a cada ~9 s
# (estilo dos reels da solar), em HTML na paleta C. Trilha só de biblioteca livre (Mixkit / YouTube Audio Library):
# o reel 7d96fd2d saiu com trilha de Dragon Ball = risco de direito autoral na conta do cliente.
TRILHAS_LIVRES = ["calm_chill.mp3", "funny_lighthearted.mp3", "Bella Bella Beat - Nana Kwabena.mp3",
                  "Caballero - Ofshane.mp3", "Days Are Long  - Silent Partner.mp3", "Auckland - VYEN.mp3",
                  "Better - Anno Domini Beats.mp3"]
GANCHOS = ["Açaí <em>puro</em> do<br>jeito paraense", "Batido <em>na hora</em><br>pra você", "No litro<br>ou na <em>tigela</em>",
           "Já pediu seu<br><em>açaí</em> hoje?", "Açaí de <em>verdade</em><br>em Paragominas", "Grosso, roxo<br>e <em>fresquinho</em>"]
CARDS_INFO = [("🥣", "Litro · 500 ml · Tigela"), ("📲", "(91) 99366-8986<br>(91) 9270-8006"),
              ("📍", "2 unidades em Paragominas"), ("💜", "100% natural, batido na hora"),
              ("🎉", "Aceitamos encomendas"), ("🐟", "Com peixe frito, charque ou camarão")]
_CSS_CARD = ("@import url('https://fonts.googleapis.com/css2?family=Anton&family=Poppins:wght@600;800&"
             "family=Playfair+Display:ital,wght@1,700&display=swap');"
             "html,body{margin:0;background:transparent}body{width:1080px;height:420px;display:flex;align-items:center;"
             "justify-content:center;font-family:'Poppins',sans-serif}"
             ".g{background:linear-gradient(135deg,#3d0f3b,#6b2a68);border:5px solid #E8C76A;border-radius:44px;"
             "padding:30px 56px 36px;text-align:center;box-shadow:0 18px 40px rgba(0,0,0,.45);max-width:900px}"
             ".g .t{display:inline-block;background:#E8C76A;color:#3d0f3b;font-weight:800;font-size:30px;letter-spacing:3px;"
             "padding:6px 26px;border-radius:30px;text-transform:uppercase}"
             ".g .h{font-family:'Anton';font-size:104px;line-height:1.02;color:#fff;text-transform:uppercase;margin-top:14px}"
             ".g .h em{font-family:'Playfair Display';font-style:italic;text-transform:none;color:#E8C76A;font-size:.85em}"
             ".i{display:flex;align-items:center;gap:26px;background:#F7F2EA;border-radius:70px;padding:18px 48px 18px 18px;"
             "box-shadow:0 16px 36px rgba(0,0,0,.45);border:4px solid #E8C76A;max-width:900px;box-sizing:border-box}"
             ".i .c{flex:none}"
             ".i .c{width:104px;height:104px;border-radius:52px;background:#3d0f3b;display:flex;align-items:center;"
             "justify-content:center;font-size:56px}"
             ".i p{margin:0;font-weight:800;font-size:46px;color:#3d0f3b;line-height:1.1}")


def _cards(pasta, n_info):
    """Renderiza gancho + n_info cards (PNG transparente 1080x420) -> lista de caminhos."""
    from playwright.sync_api import sync_playwright
    sem = sum(map(ord, pasta.name))
    gancho = GANCHOS[sem % len(GANCHOS)]
    infos = [CARDS_INFO[(sem + k) % len(CARDS_INFO)] for k in range(n_info)]
    htmls = [f"<div class='g'><span class='t'>Açaí O Precioso</span><div class='h'>{gancho}</div></div>"]
    htmls += [f"<div class='i'><div class='c'>{e}</div><p>{t}</p></div>" for e, t in infos]
    arqs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 420})
        for k, corpo in enumerate(htmls):
            pg.set_content(f"<html><head><meta charset='utf-8'><style>{_CSS_CARD}</style></head><body>{corpo}</body></html>",
                           wait_until="networkidle")
            pg.wait_for_timeout(400)
            a = pasta / f"card{k}.png"
            pg.screenshot(path=str(a), omit_background=True)
            arqs.append(a)
        b.close()
    return arqs


def finalizar(pasta, cor_selo=(93, 32, 92), cartao=None):
    """ETAPA 2: base.mp4 + selo @ (cor da paleta) + trilha baixa com ducking + cartão final 3 s -> reel.mp4."""
    pasta = Path(pasta)
    info = json.loads((pasta / "info.json").read_text("utf-8"))
    dur = info["dur"]
    sel = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(sel)
    f = acai._f(acai.MONT_B, 42)
    d.rounded_rectangle([540 - 225, 95, 540 + 225, 170], 38, fill=tuple(cor_selo) + (230,))  # topo: embaixo os stories já têm texto
    d.text(((1080 - d.textlength(acai.ARROBA, font=f)) / 2, 105), acai.ARROBA, font=f, fill="white")
    sel.save(pasta / "selo.png")
    (cartao or acai._cartao_final()).convert("RGB").resize((1080, 1920)).save(pasta / "cartao.jpg", quality=93)
    trilha = TRILHAS / random.choice([t for t in TRILHAS_LIVRES if (TRILHAS / t).exists()])
    # cards: gancho 0,2–3,8 s; depois 1 card a cada ~9 s (3,5 s na tela), entrando da direita com fade
    tempos = [(0.2, 3.8)]
    t = 8.0
    while t + 3.5 < dur - 1:
        tempos.append((t, t + 3.5))
        t += 9.0
    cards = _cards(pasta, len(tempos) - 1)
    entradas, cadeia, ant = [], "", "vs"
    for k, ((a, b), png) in enumerate(zip(tempos, cards)):
        i = 4 + k
        entradas += ["-loop", "1", "-t", f"{dur:.2f}", "-i", png.name]
        cadeia += (f"[{i}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.3:alpha=1,fade=t=out:st={b - 0.3:.2f}:d=0.3:alpha=1[k{k}];"
                   f"[{ant}][k{k}]overlay=x='max(0,({a + 0.35:.2f}-t))*2400':y=190:enable='between(t,{a:.2f},{b:.2f})'[o{k}];")
        ant = f"o{k}"
    voz = "[0:a]aresample=48000,asplit=2[voz][sc];" if info.get("audio", True) else         "anullsrc=r=48000:cl=stereo,atrim=0:%.2f[voz];anullsrc=r=48000:cl=stereo,atrim=0:%.2f[sc];" % (dur, dur)
    filtro = ("[0:v][1:v]overlay=0:0:shortest=1[vs];" + cadeia + f"[{ant}]format=yuv420p[vg];"
              "[2:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[c];[vg][c]concat=n=2:v=1:a=0[outv];" + voz +
              f"[3:a]aloop=loop=-1:size=2e9,atrim=0:{dur + 3:.2f},loudnorm=I=-30:TP=-3,aresample=48000[mus];"
              "[mus][sc]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=300[musd];"
              "[voz]apad=pad_dur=3[vz];[vz][musd]amix=inputs=2:duration=longest:normalize=0,"
              f"atrim=0:{dur + 3:.2f},afade=t=out:st={dur + 2:.2f}:d=1[outa]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", "base.mp4", "-loop", "1", "-i", "selo.png", "-loop", "1", "-t", "3",
           "-i", "cartao.jpg", "-i", str(trilha), *entradas, "-filter_complex", filtro, "-map", "[outv]", "-map", "[outa]",
           "-c:v", "h264_qsv", "-global_quality", "21", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "reel.mp4"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(pasta))
    if r.returncode != 0:
        cmd[cmd.index("h264_qsv"):cmd.index("h264_qsv") + 3] = ["libx264", "-crf", "20"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(pasta))
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-400:])
    info["trilha"] = trilha.name
    info["cards"] = len(cards)
    (pasta / "info.json").write_text(json.dumps(info, ensure_ascii=False), "utf-8")
    return pasta / "reel.mp4"


def unicos():
    """Tira os repetidos (mesmo story em versões diferentes): mesma duração (0,1 s) = mesmo vídeo; fica o maior."""
    vs = {}
    for v in sorted(ORIG.glob("vid_*.mp4")):
        d = round(_dur(v), 1)
        if d < 4:
            continue
        if d not in vs or v.stat().st_size > vs[d].stat().st_size:
            vs[d] = v
    return sorted(vs.values())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    alvo = [ORIG / f"vid_{i}.mp4" for i in sys.argv[1:]] or unicos()
    for v in alvo:
        pasta = FILA / f"arquivado_{v.stem[4:]}"
        if (pasta / "base.mp4").exists():
            continue
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            print(montar(v, pasta), flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"falhou {v.name}: {type(e).__name__}: {str(e)[:200]}", flush=True)
