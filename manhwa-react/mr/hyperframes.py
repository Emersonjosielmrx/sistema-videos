"""HyperFrames caseiro: composicoes HTML/CSS animadas renderizadas quadro a quadro pelo Chromium (Playwright) em MOV rgba.

Vantagem sobre os MOVs fixos do acervo: texto e cor dinamicos (nome da obra, pergunta do comentario, numero falado, cor do canal).
O tempo e controlado via Web Animations API (currentTime), entao a captura e deterministica e offline (sem CDN).
"""
import hashlib
import json
import tempfile
from pathlib import Path
from .common import log, ffmpeg

FONT_CSS = """
@font-face {{ font-family: 'MB'; src: url('file:///{fonts}/Montserrat-Black.ttf'); }}
@font-face {{ font-family: 'ME'; src: url('file:///{fonts}/Montserrat-ExtraBold.ttf'); }}
@font-face {{ font-family: 'LG'; src: url('file:///{fonts}/LuckiestGuy-Regular.ttf'); }}
@font-face {{ font-family: 'BG'; src: url('file:///{fonts}/Bangers-Regular.ttf'); }}
html, body {{ margin: 0; padding: 0; background: transparent; width: {w}px; height: {h}px; overflow: hidden; }}
* {{ box-sizing: border-box; }}
"""

TEMPLATES = {
    # cartao de pergunta para comentar (fim do video)
    "cta_question": """
<div id="card" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:{w_card}px; padding:34px 44px; border-radius:38px;
  background: linear-gradient(135deg, {color} 0%, {color2} 100%); box-shadow: 0 18px 60px rgba(0,0,0,.55); text-align:center; color:#fff; font-family:'ME';">
  <div style="font:900 40px/1 'MB'; letter-spacing:2px; opacity:.95;">COMENTA 👇</div>
  <div style="font:800 54px/1.15 'ME'; margin-top:16px; text-shadow:0 3px 0 rgba(0,0,0,.35);">{text}</div>
</div>
<style>
#card {{ animation: pop {dur_ms}ms cubic-bezier(.2,1.4,.4,1) both; }}
@keyframes pop {{ 0% {{ transform:translate(-50%,-50%) scale(0); opacity:0; }} 12% {{ transform:translate(-50%,-50%) scale(1.06); opacity:1; }}
  18% {{ transform:translate(-50%,-50%) scale(1); }} 88% {{ transform:translate(-50%,-50%) scale(1); opacity:1; }} 100% {{ transform:translate(-50%,-50%) scale(.92); opacity:0; }} }}
</style>""",
    # numero grande com contagem (ex.: 20 MIL, R$ 300)
    "big_number": """
<div id="num" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); text-align:center; font-family:'BG'; color:{color};
  text-shadow: 0 0 24px rgba(0,0,0,.6), 6px 6px 0 #000, -4px 4px 0 #000, 4px -4px 0 #000, -4px -4px 0 #000; white-space:nowrap;">
  <div style="font:400 {size}px/1 'BG'; letter-spacing:4px;">{text}</div>
  <div style="font:800 44px/1 'ME'; color:#fff; margin-top:6px; letter-spacing:3px;">{sub}</div>
</div>
<style>
#num {{ animation: slam {dur_ms}ms cubic-bezier(.1,1.3,.3,1) both; }}
@keyframes slam {{ 0% {{ transform:translate(-50%,-50%) scale(2.6) rotate(-6deg); opacity:0; }} 14% {{ transform:translate(-50%,-50%) scale(1) rotate(2deg); opacity:1; }}
  22% {{ transform:translate(-50%,-50%) scale(1.04) rotate(0deg); }} 85% {{ transform:translate(-50%,-50%) scale(1.04); opacity:1; }} 100% {{ transform:translate(-50%,-50%) scale(1.2); opacity:0; }} }}
</style>""",
    # selo "PARTE X / NO PERFIL" na cor do canal
    "part_badge": """
<div id="b" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); padding:26px 54px; border-radius:60px; background:{color};
  box-shadow:0 0 0 10px rgba(255,255,255,.18), 0 16px 50px rgba(0,0,0,.5); text-align:center; color:#fff; font-family:'MB'; white-space:nowrap;">
  <div style="font:900 64px/1 'MB'; letter-spacing:3px; text-shadow:0 3px 0 rgba(0,0,0,.3);">{text}</div>
  <div style="font:800 34px/1 'ME'; margin-top:10px; opacity:.95; letter-spacing:2px;">{sub}</div>
</div>
<style>
#b {{ animation: bounce {dur_ms}ms cubic-bezier(.2,1.5,.4,1) both; }}
@keyframes bounce {{ 0% {{ transform:translate(-50%,-50%) translateY(140px) scale(.6); opacity:0; }} 15% {{ transform:translate(-50%,-50%) translateY(0) scale(1.05); opacity:1; }}
  22% {{ transform:translate(-50%,-50%) scale(1); }} 88% {{ opacity:1; }} 100% {{ transform:translate(-50%,-50%) translateY(-60px); opacity:0; }} }}
</style>""",
    # "assiste ate o fim" na cor do canal
    "watch_to_end": """
<div id="w" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); padding:18px 40px; border-radius:50px; background:#111;
  border:5px solid {color}; color:#fff; font:900 40px/1 'MB'; letter-spacing:2px; white-space:nowrap; box-shadow:0 10px 40px rgba(0,0,0,.5);">{text}</div>
<style>
#w {{ animation: slide {dur_ms}ms ease-out both; }}
@keyframes slide {{ 0% {{ transform:translate(-50%,-50%) translateX(-900px); opacity:0; }} 18% {{ transform:translate(-50%,-50%) translateX(0); opacity:1; }}
  82% {{ transform:translate(-50%,-50%) translateX(0); opacity:1; }} 100% {{ transform:translate(-50%,-50%) translateX(900px); opacity:0; }} }}
</style>""",
    # faixa inferior com a obra/fonte (lower third)
    "lower_third": """
<div id="lt" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); display:flex; align-items:center; gap:18px; padding:14px 30px 14px 18px;
  border-radius:16px; background:rgba(8,8,12,.86); border-left:14px solid {color}; color:#fff; font-family:'ME'; white-space:nowrap; box-shadow:0 10px 30px rgba(0,0,0,.5);">
  <div style="font:800 40px/1 'ME'; letter-spacing:1px;">{text}</div>
  <div style="font:700 26px/1 'ME'; color:{color}; opacity:.95;">{sub}</div>
</div>
<style>
#lt {{ animation: wipe {dur_ms}ms ease-out both; }}
@keyframes wipe {{ 0% {{ clip-path: inset(0 100% 0 0); opacity:0; }} 15% {{ clip-path: inset(0 0 0 0); opacity:1; }} 85% {{ opacity:1; }} 100% {{ opacity:0; }} }}
</style>""",
}


def _lighter(hex_rgb, f=0.35):
    h = hex_rgb.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (int(c + (255 - c) * f) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def render(cfg, template, text, color="#00D1FF", sub="", dur=2.0, w=1080, h=400, fps=30, size=150):
    """Renderiza a composicao em MOV rgba (cache em assets/hyperframes). Retorna (caminho, duracao)."""
    key = hashlib.md5(json.dumps([template, text, color, sub, dur, w, h, fps, size]).encode()).hexdigest()[:12]
    out = Path(cfg["paths"]["assets"]) / "hyperframes" / f"{template}_{key}.mov"
    if out.exists():
        return out, dur
    out.parent.mkdir(parents=True, exist_ok=True)
    fonts = str(Path(cfg["paths"]["assets"]) / "fonts").replace("\\", "/")
    html = "<html><head><meta charset='utf-8'><style>" + FONT_CSS.format(fonts=fonts, w=w, h=h) + "</style></head><body>"
    html += TEMPLATES[template].format(text=text, sub=sub, color=color, color2=_lighter(color), dur_ms=int(dur * 1000), w_card=int(w * 0.82), size=size)
    html += "</body></html>"
    frames_dir = Path(tempfile.mkdtemp(prefix="mr_hf_"))
    n = int(dur * fps)
    html_path = out.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")   # file:// para as fontes locais carregarem
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg.goto(html_path.resolve().as_uri())
            pg.wait_for_timeout(250)  # fontes
            pg.evaluate("document.fonts && document.fonts.ready")
            pg.evaluate("document.getAnimations().forEach(a => a.pause())")
            for i in range(n):
                t_ms = i * 1000.0 / fps
                pg.evaluate(f"document.getAnimations().forEach(a => {{ a.currentTime = {t_ms}; }})")
                pg.screenshot(path=str(frames_dir / f"f{i:04d}.png"), omit_background=True)
            b.close()
        ffmpeg(cfg, ["-framerate", str(fps), "-i", str(frames_dir / "f%04d.png"), "-c:v", "png", "-pix_fmt", "rgba", str(out)])
        log(f"hyperframes: {template} '{text[:30]}' -> {out.name}")
    finally:
        html_path.unlink(missing_ok=True)
        for f in frames_dir.glob("*.png"):
            f.unlink()
        try:
            frames_dir.rmdir()
        except OSError:
            pass
    return out, dur
