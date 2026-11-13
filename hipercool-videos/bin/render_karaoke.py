#!/usr/bin/env python3
"""render_karaoke.py — Renderiza karaokê palavra-a-palavra via HTML+GSAP+Playwright.

Alternativa HyperFrames: em vez de gerar 1 PNG por palavra (que sobrecarrega o ffmpeg),
gera um vídeo WebM transparente (canal alpha) com animação "per-word kinetic typography"
do GSAP, seguindo os padrões do hyperframes-animation/techniques.md.

Uso:
    python bin/render_karaoke.py --text "Olá mundo" --width 1080 --height 1920 \\
        --out /tmp/karaoke.webm --fps 30 --duration 4.0

    # Teste rápido
    python bin/render_karaoke.py --text "Teste de legenda animada palavra por palavra" --duration 3.0
"""
import argparse
import base64
import os
import json
import sys
import tempfile
import time
from pathlib import Path

# Caminho pro Playwright (já instalado no venv)
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Template HTML com GSAP inline + animação word-by-word
# Usa CDN pra carregar GSAP (não precisa de instalação local)
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    width: {WIDTH}px; height: {HEIGHT}px;
    background: transparent;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    font-family: Arial Black, Impact, Helvetica Neue, sans-serif;
    overflow: hidden;
}}
.legend-box {{
    position: relative;
    width: 92%;
    margin-bottom: {MARGIN_BOTTOM}px;
    text-align: center;
}}
.word {{
    display: inline-block;
    font-size: {FONT_SIZE}px;
    font-weight: 900;
    color: white;
    text-shadow:
        -{STROKE}px -{STROKE}px 0 #000,
         {STROKE}px -{STROKE}px 0 #000,
        -{STROKE}px  {STROKE}px 0 #000,
         {STROKE}px  {STROKE}px 0 #000,
        0 0 8px rgba(0,0,0,0.5);
    opacity: 0;
    margin: 0 {SPACING}px;
    line-height: 1.3;
    position: relative;
}}
.highlight {{
    color: #FFD63C;
    text-shadow:
        -{STROKE}px -{STROKE}px 0 #000,
         {STROKE}px -{STROKE}px 0 #000,
        -{STROKE}px  {STROKE}px 0 #000,
         {STROKE}px  {STROKE}px 0 #000,
        0 0 12px rgba(255,214,60,0.4);
}}
</style>
</head>
<body>
<div class="legend-box">
    {WORDS_HTML}
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script>
(function() {{
    var tl = gsap.timeline({{ paused: true }});

    // Timings for each word [start, end] in seconds, from Python
    var timings = {TIMINGS_JSON};

    document.querySelectorAll('.word').forEach(function(word, i) {{
        var t = timings[i];
        if (!t) return;
        var start = t[0];
        var end = t[1];
        var dur = end - start;

        // Fade up + slight slide in
        tl.from(word, {{
            y: 18,
            opacity: 0,
            duration: Math.min(dur * 0.7, 0.25),
            ease: 'power2.out'
        }}, start);

        // Highlight transition: palavra destaca aos 60% da duração
        // (se não for a última, senão destaca até o fim)
        if (i < timings.length - 1) {{
            var highlight_dur = Math.max(0.05, (timings[i+1][0] - start) * 0.3);
            tl.to(word, {{
                color: '#FFD63C',
                textShadow: '-{STROKE}px -{STROKE}px 0 #000, {STROKE}px -{STROKE}px 0 #000, -{STROKE}px {STROKE}px 0 #000, {STROKE}px {STROKE}px 0 #000, 0 0 12px rgba(255,214,60,0.4)',
                duration: 0.1,
                ease: 'power1.in'
            }}, start + dur * 0.6);
        }}

        // Fade out (sutil) no final da palavra
        tl.to(word, {{
            opacity: 0.85,
            duration: 0.08,
            ease: 'none'
        }}, end - 0.08);
    }});

    // Exponential ramp play
    var totalDur = {DURATION};
    var proxy = {{ time: 0 }};
    tl.to(proxy, {{
        time: totalDur,
        duration: totalDur,
        ease: 'none'
    }}, 0);

    // Signal ready
    document.title = 'READY';

    // Render loop: seek timeline to current time
    var fps = {FPS};
    var frameInterval = 1000 / fps;
    var lastTime = 0;

    function tick() {{
        var now = performance.now() / 1000;
        if (now - lastTime >= frameInterval / 1000) {{
            lastTime = now;
            tl.progress(Math.min(now / totalDur, 1));
        }}
        if (now < totalDur + 0.1) {{
            requestAnimationFrame(tick);
        }}
    }}
    tick();
}})();
</script>
</body>
</html>"""


def frase_para_timings(text, duration=3.0):
    """Divide texto em palavras e estima timing para cada uma.

    Retorna lista de [start, end] para cada palavra.
    A duração total é dividida uniformemente.
    """
    palavras = text.strip().split()
    n = len(palavras)
    if n == 0:
        return []
    per_palavra = duration / n
    timings = []
    for i in range(n):
        start = i * per_palavra
        end = start + per_palavra
        timings.append([round(start, 3), round(end, 3)])
    return timings


def gerar_html(text, timings, width=1080, height=1920, font_size=65,
               stroke=8, margin_bottom=220, spacing=6):
    """Gera o HTML completo com GSAP para uma fala."""
    palavras = text.strip().split()
    words_html_parts = []
    for i, palavra in enumerate(palavras):
        words_html_parts.append(
            f'<span class="word w-{i}" id="w-{i}">{palavra}</span>'
        )
    words_html = "\n    ".join(words_html_parts)

    # Remove acentos/css inválidos do JSON
    timings_json = json.dumps(timings)

    total_duration = max(timings[-1][1], 0.5) if timings else 0.5

    html = HTML_TEMPLATE.format(
        WIDTH=width,
        HEIGHT=height,
        FONT_SIZE=font_size,
        STROKE=stroke,
        MARGIN_BOTTOM=margin_bottom,
        SPACING=spacing,
        WORDS_HTML=words_html,
        TIMINGS_JSON=timings_json,
        DURATION=total_duration,
        FPS=30,
    )
    return html


def render_karaoke(text, out_path, duration=3.0, width=1080, height=1920,
                   font_size=65, stroke=8, fps=30):
    """Renderiza karaokê palavra-a-palavra como WebM transparente.

    Args:
        text: Texto a renderizar
        out_path: Caminho do .webm de saída
        duration: Duração total em segundos
        width: Largura do vídeo
        height: Altura do vídeo
        font_size: Tamanho da fonte
        stroke: Grossura do contorno
        fps: Frames por segundo

    Returns:
        str: Caminho do .webm, ou None se falhar
    """
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    timings = frase_para_timings(text, duration)
    html = gerar_html(text, timings, width=width, height=height,
                      font_size=font_size, stroke=stroke)

    # Escrever HTML temporário
    tmp_html = out_path.with_suffix(".html")
    tmp_html.write_text(html)

    try:
        with sync_playwright() as p:
            # WebKit é mais leve e tem bom suporte WebGL/Canvas
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )

            # Navegar pro HTML
            page.goto(f"file://{tmp_html.resolve()}")

            # Esperar o GSAP carregar e a timeline montar
            time.sleep(0.5)

            # Renderizar frames (screenshot sequencial -> ffmpeg)
            # Em vez de screenshot frame a frame (muito lento), vamos usar
            # a API de screencast do Playwright (video recording)
            # https://playwright.dev/python/docs/api/class-browsercontext#browser-context-record-video

            # Abordagem: gravar vídeo do browser com Playwright
            video_path = str(out_path.with_name(out_path.stem + "_raw.webm"))

            # Playwright grava vídeo no close do context
            context = browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=str(out_path.parent),
                record_video_size={"width": width, "height": height},
            )
            context_page = context.new_page()

            # Navegar no context que grava
            context_page.goto(f"file://{tmp_html.resolve()}")

            # Esperar carregar
            context_page.wait_for_function(
                "document.title === 'READY'",
                timeout=10000
            )

            # Aguardar duração total + margem
            wait_time = duration + 1.0
            time.sleep(wait_time)

            # Fechar context (finaliza gravação)
            context.close()
            browser.close()

        # Playwright salva o vídeo em path com hash. Precisamos encontrar
        # o arquivo .webm mais recente no diretório pai
        import glob
        webms = sorted(Path(out_path.parent).glob("*.webm"), key=os.path.getmtime)
        if webms:
            recorded = webms[-1]
            # Mover pro path solicitado
            recorded.rename(out_path)
            print(f"  [OK] Karaokê renderizado: {out_path.name} ({out_path.stat().st_size / 1024:.0f} KB)")
            try:
                tmp_html.unlink()
            except Exception:
                pass
            return str(out_path)

        return None

    except Exception as e:
        print(f"  [X] Erro render_karaoke: {e}", file=sys.stderr)
        return None


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renderiza karaokê word-by-word via GSAP")
    parser.add_argument("--text", required=True, help="Texto a animar")
    parser.add_argument("--out", default=None, help="Saída .webm")
    parser.add_argument("--duration", type=float, default=3.0, help="Duração em segundos")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--font-size", type=int, default=65)
    parser.add_argument("--stroke", type=int, default=8)
    args = parser.parse_args()

    out = args.out or str(Path(PROJECT_DIR) / "workspace" / "tmp" / "karaoke_test.webm")

    print(f"Renderizando karaokê: {args.text[:50]}... ({args.duration}s)")
    result = render_karaoke(args.text, out, duration=args.duration,
                            width=args.width, height=args.height,
                            font_size=args.font_size, stroke=args.stroke)
    if result:
        print(f"[OK] Pronto: {result}")
    else:
        print("[X] Falhou")
        sys.exit(1)
