#!/usr/bin/env python3
"""split-shorts.py — Corta um vídeo longo em múltiplos Shorts (~55-60s) com CTA no final.

Corta em silêncios naturais (nunca no meio de uma fala), adiciona tela de CTA
no final de cada parte com áudio padrão e imagem do último frame.

Uso:
    python bin/split-shorts.py --video workspace/videos/capitulo-2/VIDEO.mp4 \
        --obra "The Meek Cat" --capitulo 2 [--plan workspace/meta/cap2_shorts_plan.json]

Se --plan não for passado, detecta silêncios automaticamente.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))

W, H, FPS = 1080, 1920, 30
IDIOMA = None  # --idioma (versão em outra língua): textos da tela final e dos metadados
CTA_DURATION = 3.5  # Duração do CTA final (segundos)
# Duração DINÂMICA (dono, 16/10): "os shorts devem ser dinâmicos, tem um tempo variável, pra acabar
# em partes que deixem a pessoa com vontade de ver a próxima e começos que façam sentido".
# O teto de 58 s era de quando o Short tinha que caber em 1 min; hoje o YouTube aceita até 3 min, e
# um capítulo virava 6 a 11 partes — mais do que a cota diária do canal aguenta postar.
TARGET_PART_DUR = 80  # alvo, não regra: o corte vai pro melhor gancho da janela
MIN_PART_DUR = 35
MAX_PART_DUR = 165  # Shorts aceitam até 180 s; sobra folga pro CTA
CARIMBO_S = 5.0     # por quantos segundos o "CAP. N | PARTE i" fica na tela, no começo da parte


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def detect_silences(video_path, noise_db=-35, min_dur=0.3):
    """Detecta pontos de silêncio no vídeo (transições naturais entre falas)."""
    r = subprocess.run([
        "ffmpeg", "-i", str(video_path), "-af",
        f"silencedetect=noise={noise_db}dB:d={min_dur}",
        "-f", "null", "-"
    ], capture_output=True, text=True, timeout=300)

    silences = []
    for line in r.stderr.split('\n'):
        m = re.search(r'silence_end: ([\d.]+)', line)
        if m:
            silences.append(float(m.group(1)))
    return silences


def tempos_de_impacto(meta):
    """Segundo em que termina cada fala que o editorial marcou como IMPACTO.

    O editorial escolhe 7-8 momentos fortes por capítulo ("flagra", "porta", "chorando") e grava o
    índice da fala no .meta.json. Acabar a parte logo DEPOIS de um desses é o fim que deixa vontade
    de ver a próxima."""
    acab = (meta or {}).get("acabamento") or {}
    fr, du = acab.get("fronteiras") or [], acab.get("duracoes") or []
    fins = []
    for imp in ((acab.get("editorial") or {}).get("impactos") or []):
        k = imp.get("fala")
        if isinstance(k, int) and 0 <= k < len(fr):
            fins.append(fr[k] + (du[k] if k < len(du) else 0.0))
    return sorted(fins)


def plan_cuts(total_dur, pontos, impactos=(), silencios=(), duracoes=()):
    """Escolhe cada corte pelo melhor GANCHO dentro da janela de duração.

    Antes cortava sempre no ponto mais perto de 55 s: a parte acabava onde calhava e a seguinte
    começava no meio de uma cena. Agora cada candidato (fronteira de painel) ganha nota:
      + acabou logo depois de um momento de impacto -> fim com gancho;
      + cai num silêncio medido no áudio            -> não corta no meio da fala;
      - distância do alvo de duração                -> só desempata.
    A duração passa a ser consequência: parte curta se o gancho veio cedo, longa se veio tarde."""
    pontos = sorted(p for p in pontos if 0 < p < total_dur)
    impactos, silencios = sorted(impactos or []), sorted(silencios or [])

    # duração do clip que COMEÇA em cada ponto: clip curto (até ~2,2 s) é painel sem narração, e a
    # parte seguinte abriria num quadro mudo. No teste do cap 1, 2 das 5 partes começavam assim.
    dur_apos = {round(p, 3): (duracoes[i] if i < len(duracoes) else 0.0)
                for i, p in enumerate(pontos)} if duracoes else {}

    def nota(p, ini):
        n = 0.0
        if any(ini < t <= p and p - t <= 10.0 for t in impactos):
            n += 3.0          # acabou logo depois de um impacto: fim com gancho
        if any(abs(p - s) <= 0.45 for s in silencios):
            n += 2.0          # pausa real no áudio: não corta no meio da palavra
        d = dur_apos.get(round(p, 3))
        if d is not None:
            n += 1.5 if d >= 2.2 else -1.5   # a próxima parte abre falando, não num painel mudo
        return n - abs(p - (ini + TARGET_PART_DUR)) / 60.0

    cuts = [0.0]
    while total_dur - cuts[-1] > MAX_PART_DUR:
        ini = cuts[-1]
        janela = [p for p in pontos if ini + MIN_PART_DUR <= p <= ini + MAX_PART_DUR]
        if janela:
            cuts.append(max(janela, key=lambda p: nota(p, ini)))
        else:  # sem ponto natural na janela: o próximo que existir (Shorts aceitam até 3 min)
            depois = [p for p in pontos if p > ini + MAX_PART_DUR]
            cuts.append(depois[0] if depois else ini + TARGET_PART_DUR)
    if len(cuts) > 1 and total_dur - cuts[-1] < MIN_PART_DUR:
        cuts.pop()  # sobra curta demais entra na parte anterior
    cuts.append(total_dur)
    return cuts


def get_duration(path):
    """Retorna duração de um arquivo de mídia."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10
    )
    return float(r.stdout.strip())


def build_cta_overlay(part_num, total_parts, obra):
    """Gera PNG transparente com o texto do CTA para sobrepor no vídeo."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    import idiomas
    font_candidates = [
        idiomas.IDIOMAS.get(IDIOMA, {}).get("fonte_png", ""),
        r"D:\hipercool-materiais\assets\fonts\LuckiestGuy-Regular.ttf" if IDIOMA in (None, "pt", "it", "id", "fr", "en") else "",
        r"C:\Windows\Fonts\impact.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_path = next((f for f in font_candidates if f and Path(f).exists()), None)

    font_big = ImageFont.truetype(font_path, 80) if font_path else ImageFont.load_default()
    font_med = ImageFont.truetype(font_path, 52) if font_path else ImageFont.load_default()
    font_sm = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()

    # Textos: última parte = FIM, outras = CONTINUA
    line1 = idiomas.texto(IDIOMA, "parte", x=part_num, y=total_parts)
    if part_num < total_parts:
        line2 = idiomas.texto(IDIOMA, "continua").replace(" ➡️", "")
    else:
        line2 = idiomas.texto(IDIOMA, "fim").replace("✅ ", "FIM DO ")
    line3 = idiomas.texto(IDIOMA, "inscreva").replace(" 🔔", "")

    for text, font, y_pos, color in [
        (line1, font_big, H * 0.38, (255, 255, 255)),
        (line2, font_med, H * 0.50, (255, 214, 60)),
        (line3, font_sm, H * 0.62, (255, 70, 70)),
    ]:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=6)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2 - bbox[0]
        draw.text((x, int(y_pos)), text, font=font, fill=color,
                  stroke_width=6, stroke_fill=(0, 0, 0, 200))

    return img


def _em_censura(t, censura_meta):
    return any(x <= t <= y for x, y in ((censura_meta or {}).get("janelas") or []))


def _keyframe_em_ou_apos(video_path, t, janela=6.0):
    """Primeiro keyframe em t ou logo depois, ou None.

    Só um keyframe pode abrir um pedaço copiado. Sem isto o corte volta pro keyframe anterior e o
    Short abre no quadro que escolher_frame_limpo tinha acabado de rejeitar."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags",
         "-of", "csv=p=0", "-read_intervals", f"{max(0.0, t - 0.05):.3f}%+{janela:.0f}", str(video_path)],
        capture_output=True, text=True, timeout=60)
    for linha in r.stdout.splitlines():
        campos = linha.split(",")
        if len(campos) >= 2 and campos[1].startswith("K"):
            try:
                k = float(campos[0])
            except ValueError:
                continue
            if k >= t - 0.05:
                return k
    return None


def frame_limpo_para_cartao(t_fim, t_inicio, censura_meta):
    """Instante que o cartão final vai congelar: o último quadro limpo do trecho.

    O cartão congela um quadro por 3,5 s. Se o trecho acabar dentro de uma janela de censura, o
    Short termina com esse quadro na tela — foi o que a auditoria achou (shorts-10: última parte
    terminando num topless borrado). Recua até 6 s procurando quadro fora de qualquer janela; se
    não houver nenhum, devolve o começo do trecho, que a abertura já garantiu limpo."""
    janelas = (censura_meta or {}).get("janelas", []) or []

    def sujo(t):
        return any(x <= t <= y for x, y in janelas)

    t = t_fim
    while sujo(t) and t > t_fim - 6.0 and t > t_inicio:
        t -= 0.5
    return t if not sujo(t) else t_inicio


def escolher_frame_limpo(video_path, t_inicial, video_dur, censura_meta):
    """Escolhe frame limpo perto de t_inicial que não esteja censurado.

    Deriva do mapa: fronteiras gravadas nos clips originais, mas fx_clips._igualar_audio encurtava
    clips curtos (vídeo 1.5 s, fala 0.8-1.1 s) no fim da fala -> até 3.5 s de erro acumulado no
    fim do vídeo (16/10 cap 1). Corrigido, mas vídeos antigos ainda têm a deriva. O t_inicial
    do Short já vem das fronteiras, então carrega o erro; usar a janela de censura direto daria
    falso positivo. Solução: procura VISUALMENTE (ffmpeg scene cut) frame limpo nos primeiros 4 s."""
    import subprocess
    janelas = censura_meta.get("janelas", []) if censura_meta else []

    def censura_em(t):
        return any(x <= t <= y for x, y in janelas)

    # Candidatos: t_inicial e cortes de cena nos primeiros 4 s
    fim_busca = min(t_inicial + 4.0, video_dur)
    r = subprocess.run([
        "ffmpeg", "-hide_banner", "-v", "info",
        "-ss", f"{t_inicial:.3f}", "-i", str(video_path), "-t", f"{fim_busca - t_inicial:.3f}",
        "-vf", "select='isnan(prev_selected_t)+gte(scene,0.25)',showinfo",
        "-fps_mode", "vfr", "-f", "null", "-"
    ], capture_output=True, text=True, timeout=30)

    candidatos = [t_inicial]
    for line in r.stderr.split('\n'):
        m = re.search(r'pts_time:([\d.]+)', line)
        if m:
            t_abs = t_inicial + float(m.group(1))
            if t_abs < fim_busca:
                candidatos.append(t_abs)

    # Primeiro não-censurado; se todos censurados, o próprio t_inicial
    for t in candidatos:
        if not censura_em(t):
            return t
    return t_inicial


def _keyframe_apos(path, t_min):
    """Primeiro keyframe em t >= t_min, ou None se não houver um útil.

    Serve pra cortar a parte em dois sem reencodar o resto: só um keyframe pode abrir um pedaço
    copiado. Medido no cap 1 em 16/10: as partes têm keyframe a cada 1,5 a 3 s, então sempre
    aparece um logo depois do carimbo."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags",
         "-of", "csv=p=0", "-read_intervals", f"%+{t_min + 20:.0f}", str(path)],
        capture_output=True, text=True, timeout=60)
    melhor = None
    for linha in r.stdout.splitlines():
        campos = linha.split(",")
        if len(campos) >= 2 and campos[1].startswith("K"):
            try:
                t = float(campos[0])
            except ValueError:
                continue
            if t >= t_min - 0.001:
                melhor = t
                break
    dur = get_duration(path)
    # só compensa se sobrar resto de verdade pra copiar
    return melhor if melhor and melhor < dur - 2.0 else None


def _carimbar_trecho(origem, png, quando, saida, ate=None):
    """Grava o carimbo em `origem` (inteira, ou só até `ate` segundos) na GPU, com o x264 de reserva."""
    base = ["ffmpeg", "-y", "-i", str(origem), "-i", str(png)]
    limite = ["-t", f"{ate:.3f}"] if ate else []
    tentativas = [] if os.environ.get("HIPER_QSV") == "0" else [
        base + ["-filter_complex", f"[0:v][1:v]{quando},format=nv12",
                "-c:v", "h264_qsv", "-global_quality", "23"] + limite + ["-c:a", "aac", "-b:a", "192k", str(saida)]]
    tentativas.append(base + ["-filter_complex", f"[0:v][1:v]{quando}",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                              "-pix_fmt", "yuv420p"] + limite + ["-c:a", "aac", "-b:a", "192k", str(saida)])
    for k, cmd in enumerate(tentativas):
        r = subprocess.run(cmd, capture_output=True, timeout=900)
        if r.returncode == 0 and Path(saida).exists() and Path(saida).stat().st_size > 10000:
            return
        if k == len(tentativas) - 1:
            raise RuntimeError(f"carimbo falhou: {(r.stderr or b'').decode('utf-8', 'replace')[-300:]}")
        log("  [!] carimbo pelo Quick Sync falhou — refazendo no x264")


def adicionar_carimbo(parte_path, part_num, capitulo, total_parts=None):
    """Carimbo "CAP. N | PARTE i" no alto, nos primeiros segundos da parte.

    Só no começo (CARIMBO_S): ele existe pra quem abriu a parte 3 saber onde está, e quem abre vê
    desde o primeiro segundo — deixar fixo o vídeo inteiro é poluição em cima da arte.
    Na parte 1 sai só "PARTE 1/N": o selo amarelo "CAP. N" do próprio vídeo aparece nos primeiros
    segundos e os dois juntos ficam repetidos (visto no teste de 16/10)."""
    from PIL import Image, ImageDraw, ImageFont
    import idiomas

    parte_path = Path(parte_path)
    cap_txt = idiomas.texto(IDIOMA, 'cap', n=capitulo)
    parte_txt = idiomas.texto(IDIOMA, 'parte', x=part_num, y=999).split(' DE ')[0].split(' DI ')[0].split(' SUR ')[0].split(' OF ')[0].split(' ИЗ ')[0].split(' จาก ')[0].split('/')[0].strip()
    if total_parts:
        parte_txt = f"{parte_txt}/{total_parts}"
    texto = parte_txt if part_num == 1 else f"{cap_txt} | {parte_txt}"

    # Gerar PNG do carimbo
    font_path = r"D:\hipercool-materiais\assets\fonts\LuckiestGuy-Regular.ttf"
    if not Path(font_path).exists():
        font_path = r"C:\Windows\Fonts\impact.ttf"

    font = ImageFont.truetype(str(font_path), 32)
    bbox = font.getbbox(texto)
    w_txt, h_txt = bbox[2] - bbox[0], bbox[3] - bbox[1]

    margin = 10
    img = Image.new("RGBA", (w_txt + margin * 2, h_txt + margin * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Borda preta
    x_base, y_base = margin, margin
    for dx in [-3, -2, -1, 0, 1, 2, 3]:
        for dy in [-3, -2, -1, 0, 1, 2, 3]:
            if dx != 0 or dy != 0:
                draw.text((x_base + dx, y_base + dy), texto, font=font, fill=(0, 0, 0, 255))
    draw.text((x_base, y_base), texto, font=font, fill=(255, 255, 255, 255))

    carimbo_png = parte_path.parent / f"_carimbo_{part_num}.png"
    img.save(str(carimbo_png))

    # Overlay
    temp_out = parte_path.with_name(parte_path.stem + "_carimbo.mp4")
    quando = f"overlay=30:30:enable='lt(t,{CARIMBO_S})'"

    # Reencodar a parte inteira pra escrever 5 s de texto é desperdício: medido em 16/10 numa parte
    # de 84 s, 104 s no Quick Sync e 302 s no x264 — cinco partes por capítulo, vezes sete línguas.
    # Como o carimbo só existe no começo, refaz só o pedaço até o primeiro keyframe depois dele e
    # cola o resto sem tocar (é o mesmo truque do CTA, que já junta base copiada + trecho novo).
    corte = _keyframe_apos(parte_path, CARIMBO_S)
    if corte:
        cabeca = parte_path.with_name(parte_path.stem + "_cab.mp4")
        resto = parte_path.with_name(parte_path.stem + "_resto.mp4")
        lista = parte_path.with_name(parte_path.stem + "_lista.txt")
        try:
            _carimbar_trecho(parte_path, carimbo_png, quando, cabeca, ate=corte)
            subprocess.run(["ffmpeg", "-y", "-ss", f"{corte:.3f}", "-i", str(parte_path),
                            "-c", "copy", str(resto)], capture_output=True, check=True, timeout=300)
            lista.write_text("file '%s'\nfile '%s'" % (cabeca.name, resto.name), encoding="utf-8")
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                            "-c", "copy", str(temp_out)], capture_output=True, check=True, timeout=300)
        except Exception:  # noqa: BLE001 — qualquer tropeço cai no caminho inteiro, que sempre funciona
            temp_out.unlink(missing_ok=True)
            corte = None
        finally:
            for f in (cabeca, resto, lista):
                try:
                    f.unlink(missing_ok=True)
                except OSError:
                    pass
    if not corte:
        _carimbar_trecho(parte_path, carimbo_png, quando, temp_out)
    import time
    time.sleep(1)  # ffmpeg pode manter handle aberto no Windows

    # Limpar PNG
    for _ in range(3):
        try:
            carimbo_png.unlink(missing_ok=True)
            break
        except PermissionError:
            time.sleep(0.5)

    # Replace com retry
    for tentativa in range(5):
        try:
            temp_out.replace(parte_path)
            break
        except PermissionError:
            if tentativa < 4:
                time.sleep(1)
            else:
                raise


def split_video(video_path, cuts, out_dir, obra, capitulo):
    """Corta o vídeo nas partes, adiciona carimbo e CTA (overlay com a música do vídeo)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    segmentos = cuts if cuts and isinstance(cuts[0], (list, tuple)) else list(zip(cuts, cuts[1:]))
    total_parts = len(segmentos)
    results = []

    video_dur = get_duration(video_path)
    meta_v = Path(video_path).with_suffix(".meta.json")
    censura_meta = (json.loads(meta_v.read_text(encoding="utf-8")).get("censura") or {}) if meta_v.exists() else {}

    for i, (start, end) in enumerate(segmentos):
        part_num = i + 1

        # Frame limpo pra abertura (deriva do mapa: shorts-10)
        start_limpo = escolher_frame_limpo(video_path, start, video_dur, censura_meta)
        # ...e o corte tem de cair EM CIMA de um keyframe. Com "-c copy" o ffmpeg não consegue
        # começar fora de keyframe: ele volta pro anterior e devolve os quadros extras, o que
        # desfazia a escolha acima — medido no cap 1 (GOP de 2 s), pedindo 95,000 o arquivo abria
        # em 94,100, e 10 das 45 partes dos 11 capítulos reabriam dentro de janela censurada.
        kf = _keyframe_em_ou_apos(video_path, start_limpo)
        if kf is not None and not _em_censura(kf, censura_meta):
            start_limpo = kf
        dur = end - start_limpo

        log(f"Parte {part_num}/{total_parts}: {start_limpo:.1f}s -> {end:.1f}s ({dur:.1f}s)")

        # 1. Gerar overlay CTA (PNG transparente)
        cta_overlay = out_dir / f"_cta_overlay_{part_num:02d}.png"
        img_overlay = build_cta_overlay(part_num, total_parts, obra)
        img_overlay.save(str(cta_overlay))

        # 2. Cortar a parte do vídeo principal (rápido: copy)
        slug = re.sub(r'[^a-z0-9]+', '-', obra.lower()).strip('-')
        final_name = f"{slug}_cap{capitulo}_parte{part_num:02d}.mp4"
        parte_base = out_dir / f"_parte{part_num:02d}_base.mp4"

        cmd_corte = [
            "ffmpeg", "-y",
            "-ss", f"{start_limpo:.3f}", "-i", str(video_path),
            "-t", f"{dur:.3f}",
            "-c", "copy",
            str(parte_base)
        ]
        subprocess.run(cmd_corte, check=True, capture_output=True, timeout=300)

        # 3. Criar segmento CTA: último frame LIMPO + overlay + escurecer + fade.
        # A conta vai em tempo do VÍDEO (as janelas de censura são do vídeo inteiro) e volta pra
        # tempo do trecho, que é o que o comando do CTA soma a start_limpo.
        ultimo_frame_t = frame_limpo_para_cartao(
            start_limpo + dur - 0.1, start_limpo, censura_meta) - start_limpo
        cta_seek = min(start_limpo + ultimo_frame_t, video_dur - 0.5)
        cta_segmento = out_dir / f"_parte{part_num:02d}_cta.mp4"

        fade_cta = "fade=t=in:st=0:d=0.3:alpha=1"
        escurecer = "eq=brightness=-0.25"

        cmd_cta = [
            "ffmpeg", "-y",
            "-ss", f"{cta_seek:.3f}", "-i", str(video_path),
            "-loop", "1", "-t", f"{CTA_DURATION:.2f}", "-i", str(cta_overlay),
            "-filter_complex",
            f"[0:v]loop=loop={int(CTA_DURATION * FPS)}:size=1:start=0,{escurecer}[bg];"
            f"[1:v]{fade_cta}[ovr];"
            f"[bg][ovr]overlay=0:0,format=yuv420p[vout];"
            # O áudio sai do mesmo ponto do vídeo, mas o quadro é congelado por CTA_DURATION e o som
            # não: na ÚLTIMA parte o ponto fica a 0,1 s do fim do arquivo e sobra 0,1 s de som para
            # 3,5 s de imagem — o Short terminava com ~3,2 s mudos, logo no cartão "FIM DO...".
            # apad completa com silêncio até o fim; nas outras partes não muda nada, porque lá o
            # áudio do vídeo já dura mais que o cartão.
            f"[0:a]apad=whole_dur={CTA_DURATION:.2f}[aout]",
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-t", f"{CTA_DURATION:.2f}",
            str(cta_segmento)
        ]
        subprocess.run(cmd_cta, check=True, capture_output=True, timeout=300)

        # 4. Concatenar parte base + CTA
        lista_concat = out_dir / f"_concat{part_num:02d}.txt"
        lista_concat.write_text(f"file '{parte_base.name}'\nfile '{cta_segmento.name}'", encoding="utf-8")

        final_path = out_dir / final_name
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(lista_concat),
            "-c", "copy",
            str(final_path)
        ]
        subprocess.run(cmd_concat, check=True, capture_output=True, timeout=120)

        # Limpar temporários
        cta_overlay.unlink(missing_ok=True)
        parte_base.unlink(missing_ok=True)
        cta_segmento.unlink(missing_ok=True)
        lista_concat.unlink(missing_ok=True)

        # 3. Carimbo "CAP. N | PARTE i/N" nos primeiros segundos. Estava desligado por lentidão
        # (302 s por parte no x264); com Quick Sync e só no começo voltou a caber no orçamento.
        # HIPER_CARIMBO=0 desliga se precisar cortar Shorts com pressa.
        if os.environ.get("HIPER_CARIMBO", "1") != "0":
            try:
                adicionar_carimbo(final_path, part_num, capitulo, total_parts)
            except Exception as e:  # noqa: BLE001 — carimbo é enfeite: não derruba o Short
                log(f"  [!] carimbo não entrou em {final_name}: {str(e)[:120]}")

        # Info
        final_dur = get_duration(final_path)
        size_mb = final_path.stat().st_size / (1024 * 1024)
        log(f"  [OK] {final_name} ({final_dur:.1f}s, {size_mb:.1f}MB)")

        results.append({
            "part": part_num,
            "inicio": round(start, 3),
            "fim": round(end, 3),
            "file": str(final_path),
            "filename": final_name,
            "duration": round(final_dur, 1),
            "size_mb": round(size_mb, 1),
            "start": round(start, 1),
            "end": round(end, 1),
        })

    return results


def generate_metadata(results, obra, capitulo):
    """Gera metadados para cada Short (título, desc, tags)."""
    meta_all = {}
    total = len(results)
    hashtag_obra = "#" + re.sub(r"\W+", "", obra.title())

    import idiomas
    for r in results:
        part = r["part"]
        if IDIOMA:
            cap_txt, parte_txt = idiomas.texto(IDIOMA, "cap", n=capitulo), idiomas.texto(IDIOMA, "parte", x=part, y=total)
            title = f"{obra} {cap_txt} | {parte_txt} 🔥 #manhwa #recap"[:100]
            desc = (f"📖 {obra} — {cap_txt}, {parte_txt}\n"
                    f"{idiomas.texto(IDIOMA, 'continua_parte', n=part + 1) if part < total else idiomas.texto(IDIOMA, 'fim')}\n\n"
                    f"{hashtag_obra} #Manhwa #Recap #Webtoon #Shorts\n\n{idiomas.texto(IDIOMA, 'assine')}")
        else:
            title = f"{obra} Cap. {capitulo} | Parte {part}/{total} 🔥 #manhwa #recap"
            if len(title) > 100:
                title = f"{obra} Cap.{capitulo} Pt.{part}/{total} 🔥 #manhwa"
            desc = (
                f"📖 {obra} — Capítulo {capitulo}, Parte {part} de {total}\n"
                f"{'🔥 CONTINUA NA PARTE ' + str(part + 1) + '!' if part < total else '✅ FIM DO CAPÍTULO!'}\n\n"
                f"Recap dramática e envolvente deste manhwa coreano de romance/drama.\n\n"
                f"{hashtag_obra} #Manhwa #Recap #Webtoon #Romance #Drama #Shorts\n\n"
                f"📌 INSCREVA-SE e ative o 🔔 para não perder nenhuma parte!"
            )

        tags = [
            obra, f"{obra} cap {capitulo}", "manhwa", "recap manhwa",
            "webtoon", "romance coreano", "drama", "shorts",
            f"parte {part}", "manhwa romance", "recap", obra.lower()
        ]

        meta_all[f"part_{part:02d}"] = {
            "pt": {"title": title, "description": desc, "tags": tags},
            "inicio": r["inicio"], "fim": r["fim"], "arquivo": r["filename"],
        }

    return meta_all


def main():
    ap = argparse.ArgumentParser(description="Corta vídeo em Shorts com CTA")
    ap.add_argument("--video", required=True, help="Vídeo fonte")
    ap.add_argument("--obra", required=True, help="Nome da obra")
    ap.add_argument("--capitulo", type=int, required=True, help="Número do capítulo")
    ap.add_argument("--plan", help="JSON com cortes pré-calculados (opcional)")
    ap.add_argument("--out-dir", help="Diretório de saída (default: workspace/shorts/<slug>)")
    ap.add_argument("--idioma", help="versão em outra língua (hi/id/it/ru/th): textos da tela final e metadados")
    args = ap.parse_args()
    global IDIOMA
    IDIOMA = args.idioma

    video = Path(args.video)
    if not video.exists():
        print(f"ERRO: vídeo não encontrado: {video}", file=sys.stderr)
        sys.exit(1)

    total_dur = get_duration(video)
    log(f"Vídeo: {video.name} ({total_dur:.1f}s)")

    # Planejar cortes
    if args.plan and Path(args.plan).exists():
        plan = json.loads(Path(args.plan).read_text())
        cuts = plan["cuts"]
        log(f"Usando plano pré-calculado: {len(cuts) - 1} partes")
    else:
        # Fronteiras entre painéis (gravadas pelo pipeline no .meta.json) nunca cortam fala;
        # silêncio só pra vídeo sem meta (com trilha de fundo quase não há silêncio).
        meta_v = video.with_suffix(".meta.json")
        meta_j = json.loads(meta_v.read_text(encoding="utf-8")) if meta_v.exists() else {}
        fronteiras = (meta_j.get("acabamento") or {}).get("fronteiras") or []
        if fronteiras:
            # Sem detect_silences aqui: a trilha toca o vídeo inteiro e mascara as pausas — medido no
            # cap 1 em 16/10, -35 dB e -28 dB acham ZERO pausa em 7 min de vídeo. Varrer o arquivo
            # atrás de silêncio custava minutos e não dizia nada. Quem evita cortar no meio da fala é
            # a fronteira de painel (o pipeline só abre painel novo quando a fala anterior acabou).
            impactos = tempos_de_impacto(meta_j)
            duracoes = (meta_j.get("acabamento") or {}).get("duracoes") or []
            log(f"Cortes por gancho: {len(fronteiras)} fronteiras, {len(impactos)} impactos marcados")
            cuts = plan_cuts(total_dur, fronteiras, impactos, (), duracoes)
        else:
            log("Detectando silêncios para pontos de corte...")
            cuts = plan_cuts(total_dur, detect_silences(video))
        duracoes = [f"{b - a:.0f}s" for a, b in zip(cuts, cuts[1:])]
        log(f"Planejados {len(cuts) - 1} cortes: {', '.join(duracoes)}")

    # Trecho com mais da metade do tempo censurado não vira Short (não engaja e chama bloqueio).
    # Descarta ANTES de cortar, pra numeração "Parte X de Y" (título e tela final) ficar contínua.
    segmentos = list(zip(cuts, cuts[1:]))
    meta_v = video.with_suffix(".meta.json")
    janelas = (json.loads(meta_v.read_text(encoding="utf-8")).get("censura") or {}).get("janelas", []) \
        if meta_v.exists() else []
    if janelas:
        def frac(a, b):
            return sum(max(0.0, min(b, y) - max(a, x)) for x, y in janelas) / max(0.01, b - a)
        pulados = [(a, b) for a, b in segmentos if frac(a, b) > 0.5]
        segmentos = [s for s in segmentos if s not in pulados]
        for a, b in pulados:
            log(f"Trecho {a:.0f}-{b:.0f}s pulado: {frac(a, b):.0%} censurado")

    # Output dir
    slug = re.sub(r'[^a-z0-9]+', '-', args.obra.lower()).strip('-')
    out_dir = Path(args.out_dir) if args.out_dir else (
        PROJECT / "workspace" / "shorts" / f"{slug}-cap{args.capitulo}")

    # Cortar
    log(f"Cortando em {len(segmentos)} Shorts...")
    results = split_video(video, segmentos, out_dir, args.obra, args.capitulo)

    # Metadados
    meta = generate_metadata(results, args.obra, args.capitulo)
    meta_path = out_dir / "meta_shorts.json"
    meta["_fonte"] = video.name
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Sumário
    log(f"\n{'='*60}")
    log(f"{len(results)} Shorts gerados em: {out_dir}")
    log(f"   Metadados: {meta_path}")
    total_size = sum(r["size_mb"] for r in results)
    log(f"   Tamanho total: {total_size:.0f} MB")
    for r in results:
        log(f"   Parte {r['part']:2d}: {r['duration']:.0f}s ({r['size_mb']:.1f}MB)")


if __name__ == "__main__":
    main()
