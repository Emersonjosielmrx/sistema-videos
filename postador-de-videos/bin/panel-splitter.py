#!/usr/bin/env python3
"""panel-splitter.py — Corta strips verticais de mangá em painéis individuais.

O COMPONENTE MAIS IMPORTANTE do projeto. Foco em modo teste/preview pra
validar cortes visuais antes de rodar a pipeline cara (IA + TTS + vídeo).

Uso:
    # MODO TESTE — corta e gera preview HTML
    python bin/panel-splitter.py --test --input workspace/cache/slug/

    # TUNING — ajustar parâmetros
    python bin/panel-splitter.py --test --input X --thresh 240 --min-h 400 --max-h 2400 --gap-min 30

    # MODO ESCURO (manhwas com fundo preto entre painéis)
    python bin/panel-splitter.py --test --input X --dark-mode

    # DRY-RUN — só mostra onde cortaria, sem salvar
    python bin/panel-splitter.py --dry-run --input X

    # PRODUÇÃO — salva painéis prontos
    python bin/panel-splitter.py --split --input X --out workspace/panels/slug/
"""
import argparse
import sys
import webbrowser
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

PROJECT_DIR = Path(__file__).resolve().parent.parent


def trim_borders(img, dark_thresh=20, light_thresh=245, min_trim=5):
    """Remove bordas pretas/brancas do topo e fundo de um painel.

    Elimina linhas que são quase totalmente escuras (< dark_thresh)
    ou quase totalmente claras (> light_thresh).
    MAS preserva bordas que contêm conteúdo (texto/balões).
    """
    w, h = img.size
    if h < 50:
        return img

    pixels = img.load()
    sample_cols = [int(w * (i + 0.5) / 10) for i in range(10)]
    sample_cols = [c for c in sample_cols if 0 <= c < w]

    # Colunas densas pra detectar conteúdo (balões)
    content_cols = [int(w * (i + 0.5) / 30) for i in range(30)]
    content_cols = [c for c in content_cols if 0 <= c < w]

    def row_has_content(y_start, y_end):
        """Verifica se uma faixa tem conteúdo (pixels escuros em fundo claro ou vice-versa)."""
        dark_px = 0
        light_px = 0
        total = 0
        step = max(1, (y_end - y_start) // 5)
        for y in range(y_start, y_end, step):
            if y >= h:
                break
            for cx in content_cols:
                r, g, b = pixels[cx, y][:3]
                avg = (r + g + b) / 3
                total += 1
                if avg < 150:
                    dark_px += 1
                if avg > 200:
                    light_px += 1
        if total == 0:
            return False
        # Se a borda é clara (branca) e tem pixels escuros > 2% = balão/texto
        # Se a borda é escura (preta) e tem pixels claros > 2% = balão/texto
        dark_ratio = dark_px / total
        light_ratio = light_px / total
        # Fundo misto: se tem tanto escuros quanto claros, provavelmente há conteúdo
        if dark_ratio > 0.02 and light_ratio > 0.02:
            return True
        return False

    # Trim do topo
    top = 0
    for y in range(min(h // 3, 200)):  # No máximo 1/3 ou 200px
        brightness = sum(sum(pixels[cx, y][:3]) / 3 for cx in sample_cols) / len(sample_cols)
        if brightness < dark_thresh or brightness > light_thresh:
            top = y + 1
        else:
            break

    # Se o topo tem conteúdo, não cortar
    if top > 0 and row_has_content(0, top):
        top = 0

    # Trim do fundo
    bot = h
    for y in range(h - 1, max(h * 2 // 3, h - 200), -1):
        brightness = sum(sum(pixels[cx, y][:3]) / 3 for cx in sample_cols) / len(sample_cols)
        if brightness < dark_thresh or brightness > light_thresh:
            bot = y
        else:
            break

    # Se o fundo tem conteúdo, não cortar
    if bot < h and row_has_content(bot, h):
        bot = h

    # Só cortar se removeu pelo menos min_trim px
    if top >= min_trim or (h - bot) >= min_trim:
        if bot - top > 50:  # Garantir que sobra conteúdo
            return img.crop((0, top, w, bot))

    return img


def detect_gaps(img, blank_thresh=240, gap_min_px=30, dark_mode=False, sample_cols=100):
    """Detecta gaps horizontais (regiões brancas ou escuras) numa imagem vertical.

    Retorna lista de tuplas (y_start, y_end) representando as regiões de gap.
    """
    w, h = img.size
    # Amostrar N colunas uniformemente, ignorando 5% das bordas laterais
    margin = int(w * 0.05)
    cols = [int(margin + (w - 2 * margin) * (i + 0.5) / sample_cols) for i in range(sample_cols)]
    cols = [c for c in cols if 0 <= c < w]

    pixels = img.load()
    gaps = []
    in_gap = False
    gap_start = 0

    # Limiar para considerar que um pixel desvia do fundo
    dev_threshold = 255 - blank_thresh + 15 if dark_mode else blank_thresh - 15

    for y in range(h):
        deviants = 0
        for cx in cols:
            r, g, b = pixels[cx, y][:3]
            avg = (r + g + b) / 3.0

            if dark_mode:
                # No modo escuro, fundo é preto. Desvio é pixel claro
                if avg >= dev_threshold:
                    deviants += 1
            else:
                # No modo claro, fundo é branco. Desvio é pixel escuro
                if avg <= dev_threshold:
                    deviants += 1

        # Consideramos linha de gap se menos de 3% dos pixels amostrados desviarem
        is_gap_row = (deviants / len(cols)) < 0.03

        if is_gap_row:
            if not in_gap:
                gap_start = y
                in_gap = True
        else:
            if in_gap:
                if y - gap_start >= gap_min_px:
                    gaps.append((gap_start, y))
                in_gap = False

    # Gap no final
    if in_gap and h - gap_start >= gap_min_px:
        gaps.append((gap_start, h))

    return gaps


def region_has_content(img, y0, y1, dark_mode=False, threshold=240, sample_cols=50):
    """Verifica se há algum conteúdo (desvio do fundo) no intervalo vertical [y0, y1].

    Usa amostragem mais densa para não perder balões pequenos ou textos finos.
    Ignora 5% das bordas laterais para desconsiderar a margem vertical da página.
    """
    w, h = img.size
    y0 = max(0, y0)
    y1 = min(h, y1)
    if y1 <= y0:
        return False

    margin = int(w * 0.05)
    cols = [int(margin + (w - 2 * margin) * (i + 0.5) / sample_cols) for i in range(sample_cols)]
    cols = [c for c in cols if 0 <= c < w]

    pixels = img.load()
    deviant_count = 0
    total_count = 0

    for y in range(y0, y1):
        for cx in cols:
            r, g, b = pixels[cx, y][:3]
            avg = (r + g + b) / 3.0

            if dark_mode:
                if avg >= (255 - threshold + 15):
                    deviant_count += 1
            else:
                if avg <= (threshold - 15):
                    deviant_count += 1
            total_count += 1

    if total_count == 0:
        return False

    ratio = deviant_count / total_count
    return ratio > 0.008


def filter_gaps(gaps, min_dist=300):
    """Agrupa gaps que estão muito próximos uns dos outros (distância < min_dist)
    e mantém apenas o maior gap de cada grupo. Isso evita fatiar balões de fala
    ou arte flutuando no meio de um gutter.
    """
    if not gaps:
        return []

    clusters = []
    current_cluster = [gaps[0]]

    for g in gaps[1:]:
        prev_gap_end = current_cluster[-1][1]
        curr_gap_start = g[0]
        if curr_gap_start - prev_gap_end < min_dist:
            current_cluster.append(g)
        else:
            clusters.append(current_cluster)
            current_cluster = [g]
    clusters.append(current_cluster)

    filtered_gaps = []
    for cluster in clusters:
        # Encontra o gap com a maior altura/tamanho no cluster
        best_gap = max(cluster, key=lambda g: g[1] - g[0])
        filtered_gaps.append(best_gap)

    return filtered_gaps


def find_best_cut_row(img, y_target, search_window=250, dark_mode=False, blank_thresh=240, sample_cols=100):
    """Encontra a linha com menor densidade de conteúdo ao redor de y_target.
    
    Procura no intervalo [y_target - search_window, y_target + search_window].
    Retorna a coordenada y ideal localmente para o corte.
    """
    w, h = img.size
    margin = int(w * 0.05)
    cols = [int(margin + (w - 2 * margin) * (i + 0.5) / sample_cols) for i in range(sample_cols)]
    cols = [c for c in cols if 0 <= c < w]
    
    pixels = img.load()
    best_y = y_target
    min_score = float('inf')
    
    y_min = max(0, y_target - search_window)
    y_max = min(h - 1, y_target + search_window)
    
    # Limiar para desvio do fundo
    dev_threshold = 255 - blank_thresh + 15 if dark_mode else blank_thresh - 15
    
    for y in range(y_min, y_max + 1):
        deviants = 0
        for cx in cols:
            r, g, b = pixels[cx, y][:3]
            avg = (r + g + b) / 3.0
            if dark_mode:
                if avg >= dev_threshold:
                    deviants += 1
            else:
                if avg <= dev_threshold:
                    deviants += 1
        
        # Penalidade leve por distância para preferir cortes mais próximos do y_target ideal
        dist_penalty = abs(y - y_target) / (search_window * 10.0)
        score = (deviants / len(cols)) + dist_penalty
        
        if score < min_score:
            min_score = score
            best_y = y
            
    return best_y


def split_strip(img_path, min_h=400, max_h=2000, blank_thresh=240,
                gap_min_px=30, dark_mode=False):
    """Corta uma imagem vertical em painéis baseado em gaps detectados.

    Retorna lista de dicts: [{img: PIL.Image, y_start, y_end, height}, ...]
    """
    img = Image.open(img_path).convert("RGB")
    w, h = img.size

    # Detecção automática de modo escuro/claro por strip
    if not dark_mode:
        sample_rows = min(100, h)
        step = max(1, h // sample_rows)
        white_votes = 0
        black_votes = 0

        sample_cols = 20
        cols = [int(w * (i + 0.5) / sample_cols) for i in range(sample_cols)]
        cols = [c for c in cols if 0 <= c < w]

        pixels = img.load()
        for y in range(0, h, step):
            if y >= h:
                break
            brightness = sum(sum(pixels[cx, y][:3]) / 3 for cx in cols) / len(cols)
            if brightness > 240:
                white_votes += 1
            elif brightness < 15:
                black_votes += 1

        if black_votes > white_votes:
            dark_mode = True

    gaps = detect_gaps(img, blank_thresh, gap_min_px, dark_mode)
    # Agrupar e filtrar gaps que estão muito próximos (balões/artes flutuantes no gutter)
    gaps = filter_gaps(gaps, min_dist=max(150, min_h - 100))

    # Construir painéis brutos com suporte a overlap inteligente se houver conteúdo nos gaps
    num_panels = len(gaps) + 1
    raw = []
    for i in range(num_panels):
        if i == 0:
            y_start = 0
        else:
            prev_gap_start, prev_gap_end = gaps[i - 1]
            y_start = (prev_gap_start + prev_gap_end) // 2

        if i == num_panels - 1:
            y_end = h
        else:
            next_gap_start, next_gap_end = gaps[i]
            y_end = (next_gap_start + next_gap_end) // 2

        raw.append({"y_start": y_start, "y_end": y_end, "height": y_end - y_start})

    # Ajustar limites de y_start e y_end se houver conteúdo nos gaps
    for i in range(num_panels):
        # 1. Ajustar o início do painel i baseado no gap anterior
        if i > 0:
            prev_gap_start, prev_gap_end = gaps[i - 1]
            mid_prev = (prev_gap_start + prev_gap_end) // 2
            if region_has_content(img, mid_prev, prev_gap_end, dark_mode, blank_thresh):
                raw[i]["y_start"] = prev_gap_start
                raw[i]["height"] = raw[i]["y_end"] - raw[i]["y_start"]

        # 2. Ajustar o fim do painel i baseado no gap seguinte
        if i < num_panels - 1:
            next_gap_start, next_gap_end = gaps[i]
            mid_next = (next_gap_start + next_gap_end) // 2
            if region_has_content(img, next_gap_start, mid_next, dark_mode, blank_thresh):
                raw[i]["y_end"] = next_gap_end
                raw[i]["height"] = raw[i]["y_end"] - raw[i]["y_start"]

    # MESCLAR painéis pequenos (balões flutuantes, fragmentos) com o vizinho.
    # Um painel < min_h provavelmente é um balão solto no vazio — junta ele
    # com o painel seguinte (ou anterior se for o último).
    merged = []
    for p in raw:
        if p["height"] < min_h and merged:
            # junta com o painel anterior
            merged[-1]["y_end"] = p["y_end"]
            merged[-1]["height"] = merged[-1]["y_end"] - merged[-1]["y_start"]
        else:
            merged.append(p)
    # Se o primeiro painel ficou pequeno e há um segundo, junta-os
    while len(merged) >= 2 and merged[0]["height"] < min_h:
        merged[1]["y_start"] = merged[0]["y_start"]
        merged[1]["height"] = merged[1]["y_end"] - merged[1]["y_start"]
        merged.pop(0)

    # Materializar imagens
    panels = []
    for p in merged:
        panels.append({
            "img": img.crop((0, p["y_start"], w, p["y_end"])),
            "y_start": p["y_start"],
            "y_end": p["y_end"],
            "height": p["height"],
        })

    # Fallback: se não encontrou gaps, corta em pedaços fixos de 1800px
    if not panels:
        chunk_h = 1800
        for y in range(0, h, chunk_h):
            end = min(y + chunk_h, h)
            if end - y >= min_h:
                panels.append({
                    "img": img.crop((0, y, w, end)),
                    "y_start": y,
                    "y_end": end,
                    "height": end - y,
                })

    # Subdivide painéis maiores que max_h — MAS de forma inteligente
    # Em vez de cortar no meio (que pode cortar balões/cabeças),
    # procura gaps secundários dentro do painel grande.
    # Se não encontrar gap, mantém o painel inteiro (o effects_engine faz pan vertical).
    final = []
    for p in panels:
        if p["height"] > max_h:
            sub_img = p["img"]
            sub_h = p["height"]
            # Tentar encontrar gaps internos com threshold mais baixo
            sub_gaps = detect_gaps(sub_img, blank_thresh - 20, gap_min_px=20, dark_mode=dark_mode)
            if sub_gaps:
                # Cortar nos gaps internos
                prev = 0
                for gs, ge in sub_gaps:
                    if gs - prev >= min_h:
                        final.append({
                            "img": sub_img.crop((0, prev, sub_img.width, gs)),
                            "y_start": p["y_start"] + prev,
                            "y_end": p["y_start"] + gs,
                            "height": gs - prev,
                        })
                    prev = ge
                # Último pedaço
                if sub_h - prev >= min_h:
                    final.append({
                        "img": sub_img.crop((0, prev, sub_img.width, sub_h)),
                        "y_start": p["y_start"] + prev,
                        "y_end": p["y_start"] + sub_h,
                        "height": sub_h - prev,
                    })
                elif final:
                    # Se o pedaço final é muito pequeno, junta com o anterior
                    pass
            else:
                # Sem gaps internos — dividir usando busca inteligente de linha com menor densidade de conteúdo
                num_parts = max(2, (sub_h + 1800 - 1) // 1800)
                part_h = sub_h // num_parts
                cuts = [0]
                for i in range(1, num_parts):
                    ideal_y = i * part_h
                    best_cut = find_best_cut_row(sub_img, ideal_y, search_window=250, dark_mode=dark_mode, blank_thresh=blank_thresh)
                    cuts.append(best_cut)
                cuts.append(sub_h)
                
                overlap = 30
                for i in range(num_parts):
                    y0 = max(0, cuts[i] - overlap) if i > 0 else 0
                    y1 = min(sub_h, cuts[i+1] + overlap) if i < num_parts - 1 else sub_h
                    final.append({
                        "img": sub_img.crop((0, y0, sub_img.width, y1)),
                        "y_start": p["y_start"] + y0,
                        "y_end": p["y_start"] + y1,
                        "height": y1 - y0,
                    })
        else:
            final.append(p)

    # Pós-processamento: NÃO trim borders (preserva balões nas bordas)
    # O trim cortava balões que ficam em áreas brancas/pretas nas bordas
    trimmed = final

    # FORÇAR subdivisão de qualquer painel que ainda esteja > max_h
    # Isso garante que NENHUM painel vai pro vídeo com altura absurda
    really_final = []
    for p in final:
        if p["height"] > max_h:
            sub_img = p["img"]
            sub_h = p["height"]
            num_parts = max(2, (sub_h + 1800 - 1) // 1800)
            part_h = sub_h // num_parts
            cuts = [0]
            for i in range(1, num_parts):
                ideal_y = i * part_h
                best_cut = find_best_cut_row(sub_img, ideal_y, search_window=250, dark_mode=dark_mode, blank_thresh=blank_thresh)
                cuts.append(best_cut)
            cuts.append(sub_h)
            
            overlap = 30
            for i in range(num_parts):
                y0 = max(0, cuts[i] - overlap) if i > 0 else 0
                y1 = min(sub_h, cuts[i+1] + overlap) if i < num_parts - 1 else sub_h
                really_final.append({
                    "img": sub_img.crop((0, y0, sub_img.width, y1)),
                    "y_start": p["y_start"] + y0,
                    "y_end": p["y_start"] + y1,
                    "height": y1 - y0,
                })
        else:
            really_final.append(p)

    return really_final, gaps, img


def process_directory(input_dir, **kwargs):
    """Processa todos os strips num diretório. Retorna resultados por arquivo."""
    input_dir = Path(input_dir)
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    images = sorted(f for f in input_dir.iterdir()
                    if f.suffix.lower() in exts and not f.name.startswith("_"))

    if not images:
        print(f"Nenhuma imagem encontrada em {input_dir}", file=sys.stderr)
        return []

    all_panels = []
    for img_path in images:
        panels, gaps, original = split_strip(img_path, **kwargs)
        all_panels.append({
            "source": img_path,
            "panels": panels,
            "gaps": gaps,
            "original": original,
        })

    return all_panels


def save_panels(all_results, out_dir):
    """Salva painéis cortados como JPG numerados."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    idx = 0
    for result in all_results:
        for p in result["panels"]:
            fname = f"panel_{idx:03d}.jpg"
            p["img"].save(out_dir / fname, "JPEG", quality=90)
            idx += 1
    return idx


def generate_preview_html(all_results, preview_dir, params):
    """Gera HTML interativo pra validar cortes visuais.

    Mostra o strip original com linhas vermelhas nos cortes, e cada painel
    cortado numerado com dimensões.
    """
    preview_dir = Path(preview_dir)
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Salvar painéis como JPG pro preview
    panel_idx = 0
    panel_files = []
    for result in all_results:
        for p in result["panels"]:
            fname = f"panel_{panel_idx:03d}.jpg"
            p["img"].save(preview_dir / fname, "JPEG", quality=85)
            panel_files.append({"file": fname, "height": p["height"],
                                "y_start": p["y_start"], "y_end": p["y_end"]})
            panel_idx += 1

    # Salvar originals reduzidos pra preview
    orig_files = []
    for i, result in enumerate(all_results):
        orig = result["original"]
        # Reduz largura pra 400px pra ficar leve no browser
        ratio = 400 / orig.width
        small = orig.resize((400, int(orig.height * ratio)), Image.LANCZOS)
        fname = f"_orig_{i:02d}.jpg"
        small.save(preview_dir / fname, "JPEG", quality=75)
        orig_files.append({
            "file": fname,
            "width": orig.width,
            "height": orig.height,
            "gaps": result["gaps"],
            "ratio": ratio,
            "source": result["source"].name,
        })

    # Gerar HTML
    html_parts = [f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Panel Splitter Preview</title>
<style>
body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
h1 {{ color: #e94560; }}
h2 {{ color: #0f3460; background: #e94560; padding: 8px 16px; border-radius: 4px; display: inline-block; }}
.params {{ background: #16213e; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-family: monospace; }}
.container {{ display: flex; gap: 30px; flex-wrap: wrap; }}
.originals {{ flex: 0 0 420px; }}
.panels-grid {{ flex: 1; display: flex; flex-wrap: wrap; gap: 10px; align-content: start; }}
.panel-card {{ background: #16213e; border-radius: 8px; padding: 8px; text-align: center; }}
.panel-card img {{ max-width: 200px; max-height: 300px; border-radius: 4px; }}
.panel-card .info {{ font-size: 12px; color: #aaa; margin-top: 4px; }}
.orig-container {{ position: relative; margin-bottom: 20px; }}
.orig-container img {{ width: 400px; display: block; }}
.cut-line {{ position: absolute; left: 0; width: 100%; height: 2px; background: red; opacity: 0.8; }}
.gap-region {{ position: absolute; left: 0; width: 100%; background: rgba(255,255,0,0.15); border-top: 1px dashed yellow; border-bottom: 1px dashed yellow; }}
.summary {{ background: #0f3460; padding: 16px; border-radius: 8px; margin-bottom: 20px; }}
</style></head><body>
<h1>🔪 Panel Splitter — Preview</h1>
<div class="params">
Parâmetros: thresh={params['thresh']} | min_h={params['min_h']} | max_h={params['max_h']} | gap_min={params['gap_min']} | dark_mode={params['dark_mode']}
</div>
<div class="summary">
<b>Total:</b> {panel_idx} painéis cortados de {len(all_results)} strip(s)<br>
<b>Alturas:</b> {', '.join(f"{p['height']}px" for p in panel_files[:20])}{'...' if len(panel_files) > 20 else ''}
</div>
<div class="container">
<div class="originals">
<h2>Originals + Cortes</h2>
"""]

    for orig in orig_files:
        html_parts.append(f"""
<p style="color:#aaa;font-size:12px">{orig['source']} ({orig['width']}x{orig['height']})</p>
<div class="orig-container">
<img src="{orig['file']}">
""")
        # Linhas de corte (gaps)
        for gap_start, gap_end in orig["gaps"]:
            top_s = gap_start * orig["ratio"]
            top_e = gap_end * orig["ratio"]
            h = top_e - top_s
            html_parts.append(f'<div class="gap-region" style="top:{top_s:.0f}px;height:{h:.0f}px"></div>')
            html_parts.append(f'<div class="cut-line" style="top:{top_s:.0f}px"></div>')
            html_parts.append(f'<div class="cut-line" style="top:{top_e:.0f}px"></div>')
        html_parts.append("</div>")

    html_parts.append("""
</div>
<div class="panels-grid">
<h2>Painéis Cortados</h2>
<div style="display:flex;flex-wrap:wrap;gap:10px;">
""")

    for i, pf in enumerate(panel_files):
        html_parts.append(f"""
<div class="panel-card">
<img src="{pf['file']}" loading="lazy">
<div class="info">#{i} — {pf['height']}px<br>y:{pf['y_start']}→{pf['y_end']}</div>
</div>
""")

    html_parts.append("""
</div></div></div>
</body></html>""")

    html_path = preview_dir / "preview.html"
    html_path.write_text("".join(html_parts), encoding="utf-8")
    return html_path


def main():
    parser = argparse.ArgumentParser(
        description="Corta strips verticais de mangá em painéis individuais."
    )
    parser.add_argument("--input", "-i", required=True,
                        help="Diretório com strips (imagens) baixados")
    parser.add_argument("--out", "-o",
                        help="Diretório de saída pra painéis (modo --split)")

    # Modos
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test", action="store_true",
                      help="Modo teste: corta e gera preview HTML")
    mode.add_argument("--split", action="store_true",
                      help="Modo produção: salva painéis prontos")
    mode.add_argument("--dry-run", action="store_true",
                      help="Só mostra onde cortaria, sem salvar")

    # Parâmetros de tuning
    parser.add_argument("--thresh", type=int, default=240,
                        help="Limiar de brilho pra gap (default: 240)")
    parser.add_argument("--min-h", type=int, default=400,
                        help="Altura mínima de painel (default: 400px)")
    parser.add_argument("--max-h", type=int, default=2400,
                        help="Altura máxima antes de subdividir (default: 2400px)")
    parser.add_argument("--gap-min", type=int, default=30,
                        help="Largura mínima de gap em px (default: 30)")
    parser.add_argument("--dark-mode", action="store_true",
                        help="Detecta gaps escuros em vez de claros")
    parser.add_argument("--no-open", action="store_true",
                        help="Não abre o browser automaticamente (modo --test)")

    args = parser.parse_args()
    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"ERRO: {input_dir} não é um diretório", file=sys.stderr)
        sys.exit(1)

    kwargs = {
        "min_h": args.min_h,
        "max_h": args.max_h,
        "blank_thresh": args.thresh,
        "gap_min_px": args.gap_min,
        "dark_mode": args.dark_mode,
    }

    results = process_directory(input_dir, **kwargs)
    if not results:
        sys.exit(1)

    total_panels = sum(len(r["panels"]) for r in results)
    print(f"✂ {total_panels} painéis encontrados em {len(results)} strip(s)")

    if args.dry_run:
        for r in results:
            print(f"\n  {r['source'].name}:")
            print(f"    Gaps detectados: {len(r['gaps'])}")
            for i, p in enumerate(r["panels"]):
                print(f"    painel {i}: y={p['y_start']}→{p['y_end']} ({p['height']}px)")
        return

    if args.test:
        slug = input_dir.name
        preview_dir = PROJECT_DIR / "workspace" / "panels-preview" / slug
        params = {
            "thresh": args.thresh, "min_h": args.min_h,
            "max_h": args.max_h, "gap_min": args.gap_min,
            "dark_mode": args.dark_mode,
        }
        html_path = generate_preview_html(results, preview_dir, params)
        # Também salva painéis individuais na mesma pasta
        save_panels(results, preview_dir)
        print(f"✓ Preview salvo em: {preview_dir}/")
        print(f"  HTML: {html_path}")
        if not args.no_open:
            webbrowser.open(f"file://{html_path}")
        return

    if args.split:
        if not args.out:
            print("ERRO: --out é obrigatório no modo --split", file=sys.stderr)
            sys.exit(1)
        out_dir = Path(args.out)
        n = save_panels(results, out_dir)
        print(f"✓ {n} painéis salvos em: {out_dir}/")
        return


if __name__ == "__main__":
    main()
