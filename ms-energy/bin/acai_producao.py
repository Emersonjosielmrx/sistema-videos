# -*- coding: utf-8 -*-
r"""acai_producao.py — conteúdo do Açaí O Precioso em LOTE para a pasta (dona 05/11/2026 12h: "comece as do açaí e vá
deixando em uma pasta até restabelecermos o login"). Nada é postado aqui.

Estilo: referências @pontodoacai_pgmcentral + preferidas da dona (Ver-o-Açaí, Point do Açaí, Açaíze, Açaí da Hora,
Amazônia na Cuia, Belém Açaiteria). Reels = Veo a partir das fotos reais do perfil + LEGENDA MIX (cada palavra com
desenho/efeito diferente, legenda_mix.py dos Shorts) + cartão final (Zap + endereço), como as solares.
Informativos = carrosséis creme + roxo uva (acai.ref_*).
Saída: D:\ms-energy\videos\acai\fila_para_postar\<data>_<tipo>_<id>\ (mp4/jpg + legenda.txt).
    D:\veo\venv\Scripts\python.exe acai_producao.py [reels|carrosseis|tudo]
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageFilter

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import acai  # noqa: E402
import legenda_mix  # noqa: E402

FILA = acai.SAIDA / "fila_para_postar"
FONTES = Path(r"D:\recapd-ambientes\producao\workspace\assets\fonts")
NAO_SORVETE = acai.NAO_SORVETE

REELS_MIX = [
    {"id": "litro_gelo", "foto": "DKzTAP5sBBY_5.jpg",
     "frases": ["AÇAÍ PURO", "GROSSO DE VERDADE", "NO LITRO OU 500 ML", "PEÇA O SEU"],
     "prompt": "Vertical 9:16 product commercial. Slow cinematic orbit around these exact acai packages on ice, cold "
               "mist, condensation, no people, keep packages and labels exactly as in the photo, no new text." + NAO_SORVETE,
     "legenda": "Açaí puro e grosso, no litro ou no 500 ml 💜 Leve pra casa!"},
    {"id": "tigela_frito", "foto": "DKQJ1LVPKMx_4.jpg",
     "frases": ["ALMOÇO HOJE?", "AÇAÍ NA TIGELA", "COM PEIXE FRITO", "SÓ NO PRECIOSO"],
     "prompt": "Vertical 9:16 food commercial. Slow top-down drift over this exact table: bowl of thick pure dark purple "
               "acai, crispy fried fish, shrimp, dried beef, warm light, no people, no text, keep the food exactly as "
               "in the photo." + NAO_SORVETE,
     "legenda": "Almoço hoje? Açaí puro na tigela com peixe frito 😋 Vem pro Precioso!"},
    {"id": "nativo", "foto": "DMxdQ_qMC-Q_0.jpg",
     "frases": ["O VERDADEIRO", "AÇAÍ NATIVO", "DE PARAGOMINAS", "BATIDO NA HORA"],
     "prompt": "Vertical 9:16 product commercial. Gentle slow push-in on these exact acai packages, cold and fresh, "
               "subtle mist, premium look, no people, keep packages and labels exactly as in the photo." + NAO_SORVETE,
     "legenda": "O verdadeiro açaí nativo de Paragominas 💜 Puro, grosso e batido na hora."},
    {"id": "fachada", "foto": "DKQJ1LVPKMx_1.jpg",
     "frases": ["JÁ CONHECE", "O AÇAÍ PRECIOSO?", "PROMISSÃO I", "TE ESPERAMOS"],
     "prompt": "Vertical 9:16 cinematic shot. Slow push-in towards this exact acai shop front at dusk, warm purple lights, "
               "inviting, no people added, keep the facade and sign exactly as in the photo, no new text.",
     "legenda": f"Vem conhecer o Açaí O Precioso 💜 📍 {acai.ENDERECO}."},
]

CARROSSEIS_REF = [
    {"id": "beneficios", "tipo": "lista", "titulo": "5 BENEFÍCIOS DO AÇAÍ",
     "itens": ["Fonte de energia", "Ação antioxidante", "Rico em fibras", "Ajuda na imunidade", "Gorduras boas"],
     "legenda": "Além de gostoso, faz bem 💜 Qual benefício você não conhecia?"},
    {"id": "como_pedir", "tipo": "lista", "titulo": "COMO PEDIR SEU AÇAÍ",
     "itens": ["Chama no Zap", "Escolha litro ou tigela", "Retire ou receba"],
     "legenda": "Pedir é fácil 💜 Chama no WhatsApp e garanta o seu!"},
    {"id": "litro_tigela", "tipo": "fotos", "slides": [("DKzTAP5sBBY_5.jpg", "AÇAÍ PURO NO LITRO", "Grosso, batido na hora."),
                                                       ("DKQJ1LVPKMx_4.jpg", "TIGELA NA HORA", "Com peixe frito, camarão ou charque.")],
     "legenda": "Litro pra levar ou tigela na hora: como você prefere seu açaí? 💜"},
    {"id": "onde_estamos", "tipo": "onde", "legenda": f"Vem pro Precioso 💜 📍 {acai.ENDERECO}."},
]


def _cartoes(frases, dur):
    """Uma frase por 'cartão', palavras espaçadas dentro da janela de cada frase."""
    ini, fim = 0.4, max(1.5, dur - 0.3)
    janela = (fim - ini) / len(frases)
    out = []
    for i, fr in enumerate(frases):
        t0 = ini + i * janela
        ps = fr.split()
        passo = min(0.35, (janela * 0.6) / max(1, len(ps)))
        out.append([(round(t0 + k * passo, 2), w) for k, w in enumerate(ps)] + [round(t0 + janela - 0.05, 2)])
    return out


def montar_mix(clip, r, pasta):
    """Vertical 1080x1920 (sem faixa preta: fundo desfocado) + legenda MIX + selo @ + cartão final 3 s."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(clip)], capture_output=True, text=True).stdout.strip() or 8)
    estilos, linhas = legenda_mix.gerar(_cartoes(r["frases"], dur), 1080, 1920)
    ass = pasta / "mix.ass"
    ass.write_text("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n"
                   "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
                   "SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
                   "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                   + "\n".join(estilos) + "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
                   "MarginV, Effect, Text\n" + "\n".join(linhas) + "\n", encoding="utf-8")
    cartao, selo = pasta / "cartao.jpg", pasta / "selo.png"
    acai._cartao_final().save(cartao, quality=93)
    from PIL import ImageDraw
    sel = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))  # só o @ embaixo (a legenda MIX fica livre no meio)
    d = ImageDraw.Draw(sel)
    f = acai._f(acai.MONT_B, 44)
    d.rounded_rectangle([1080 // 2 - 230, 1920 - 300, 1080 // 2 + 230, 1920 - 220], 40, fill=acai.UVA + (235,))
    d.text(((1080 - d.textlength(acai.ARROBA, font=f)) / 2, 1920 - 290), acai.ARROBA, font=f, fill="white")
    sel.save(selo)
    cd = subprocess.run(["ffmpeg", "-hide_banner", "-ss", "1", "-i", str(clip), "-vf", "cropdetect=24:2:0", "-frames:v",
                         "12", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    m = re.findall(r"crop=(\d+:\d+:\d+:\d+)", cd)
    corte = f"crop={m[-1]}," if m else ""
    fontes = FONTES.as_posix().replace(":", "\\:")
    filtro = (f"[0:v]{corte}split[a][b];"
              "[b]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.08[bg];"
              "[a]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
              "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30,"
              f"subtitles=mix.ass:fontsdir='{fontes}'[v];"
              "[v][1:v]overlay=0:0:shortest=1,format=yuv420p[vg];"
              "[2:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[c];"
              "[vg][c]concat=n=2:v=1:a=0[outv];[0:a]apad=pad_dur=3[outa]")
    out = pasta / f"reel_{r['id']}.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-loop", "1", "-i", str(selo), "-loop", "1", "-t", "3",
           "-i", str(cartao), "-filter_complex", filtro, "-map", "[outv]", "-map", "[outa]", "-c:v", "h264_qsv",
           "-global_quality", "21", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)]
    if subprocess.run(cmd, capture_output=True, cwd=str(pasta)).returncode != 0:
        cmd[cmd.index("h264_qsv"):cmd.index("h264_qsv") + 3] = ["libx264", "-crf", "20"]
        subprocess.run(cmd, check=True, capture_output=True, cwd=str(pasta))
    return out


def _foto9(foto, destino):
    base = Image.open(acai.FOTOS / foto).convert("RGB")
    fundo = acai._cobrir(acai.FOTOS / foto, 1080, 1920).filter(ImageFilter.GaussianBlur(40))
    base.thumbnail((1080, 1920))
    fundo.paste(base, ((1080 - base.width) // 2, (1920 - base.height) // 2))
    fundo.save(destino, quality=94)
    return destino


def _leg(txt):
    return f"{txt}\n\n📲 Pedidos e encomendas: {acai.ZAP}\n📍 {acai.ENDERECO} — {acai.CIDADE}\n\n{acai.HASHTAGS}"


def reels():
    for r in REELS_MIX:
        if list(FILA.glob(f"*_reel_{r['id']}/reel_{r['id']}.mp4")):
            continue
        pasta = FILA / f"{datetime.now():%Y%m%d_%H%M}_reel_{r['id']}"
        pasta.mkdir(parents=True, exist_ok=True)
        clip = acai._veo(r["prompt"], _foto9(r["foto"], pasta / "foto_9x16.jpg"), pasta / "veo.mp4")
        if not clip:
            acai.log(f"[lote] reel {r['id']}: sem clipe do Veo")
            continue
        out = montar_mix(clip, r, pasta)
        (pasta / "legenda.txt").write_text(_leg(r["legenda"]), "utf-8")
        acai.log(f"[lote] reel pronto (não postado): {out}")


def carrosseis():
    for c in CARROSSEIS_REF:
        pasta = FILA / f"{datetime.now():%Y%m%d_%H%M}_carrossel_{c['id']}"
        if list(FILA.glob(f"*_carrossel_{c['id']}")):
            continue
        pasta.mkdir(parents=True, exist_ok=True)
        if c["tipo"] == "lista":
            imgs = [acai.ref_lista(c["titulo"], c["itens"])]
        elif c["tipo"] == "fotos":
            imgs = [acai.ref_foto_titulo(f, t, s) for f, t, s in c["slides"]]
        else:
            imgs = [acai.ref_onde_estamos()]
        imgs.append(acai.slide_cta())
        for i, im in enumerate(imgs, 1):
            im.save(pasta / f"{i}.jpg", quality=93)
        (pasta / "legenda.txt").write_text(_leg(c["legenda"]), "utf-8")
        acai.log(f"[lote] carrossel pronto (não postado): {pasta}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    o = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if o in ("carrosseis", "tudo"):
        carrosseis()
    if o in ("reels", "tudo"):
        reels()
