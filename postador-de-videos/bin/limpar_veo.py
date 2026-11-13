#!/usr/bin/env python3
"""limpar_veo.py - versao LIMPA dos Shorts do Veo (sem a marca @InovareStories e sem o cartao final "Siga ...").

Os 'brutos' (veo_videos_iniciais, copia no Drive em videos-backup/veo/brutos_veo_videos_iniciais) vem em 2 formatos
(conferido em quadros reais em 15/10):
  - 720x1280 de ~8 s ('cru'): o clipe do Veo puro, ja limpo -> so sobe para 1080x1920;
  - 1080x1920 de ~15,4 s: o clipe num quadro 720x1280 no meio (ou 720x960 com faixas cinzas), marca @InovareStories em
    cima, legenda embutida, de ~7,5 a ~13,4 s o SLIDE DE PROPAGANDA (produto + WhatsApp) e no fim o cartao "Siga
    @InovareStories" -> recorta o quadro (com a legenda inteira) e corta antes do slide (fundo desfocado quando e 3:4).
  Outro formato: nao limpa (json com 'revisar'). Os COMPLETO (pos_final) tem a propaganda: nunca usar como limpo.
Transcreve a fala (base do titulo). Saida: D:\\hipercool-materiais\\veo\\limpos\\<nome>.mp4 + .json; so os de formato
conhecido sao aprovados (politica.marcar_aprovacao); os outros ficam para 'manhwareact.py rede --aprovar'.
Os limpos entram na rede do manhwa-react (mr/rede.py, fonte 'veo') so nos canais de config 'canais_veo_limpo'.

Uso (venv do manhwa-react): python bin/limpar_veo.py [--max N] [--drive] [arquivo.mp4 ...]
"""
import argparse
import json
import re
import shutil
import subprocess

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
import sys
import tempfile
from datetime import datetime
from pathlib import Path

if sys.stdout:
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
RCLONE = r"D:\tools\rclone.exe"
BRUTOS = Path(r"D:\hipercool-materiais\veo\veo_videos_iniciais")
# Saida do gerador religado em 16/10 (cron_gerar_video_llm.py, ja passou pelo porteiro validar_video + conferir_fala):
# 720x1280 de 8 s, o Veo puro. Ninguem levava esses para os limpos, entao o Veo novo nunca chegava na rede. Os teste_*
# sao sobras de teste.
NOVOS = Path(r"D:\veo\beta\videos\cron_shorts")
DRIVE_BRUTOS = "manhwa-drive:videos-backup/veo/brutos_veo_videos_iniciais"
SAIDA = Path(r"D:\hipercool-materiais\veo\limpos")
QUADRO = (720, 1280, 180, 320)  # w, h, x, y do video do Veo dentro do bruto
# Parte dos brutos de ~8 s e montagem de 2 cenas e algumas vieram do TikTok (marca d'agua/logo do TikTok): nao vao pro
# YouTube. Logo recortada de um deles (robos_desastrad_20260729_123452) e limiar calibrado em 15/10 (marca 0,65-0,70;
# limpos <= 0,52 em amostra de 14). Montagens de correlacao de cor baixa conferidas nos quadros em 16/10: sem logo
# (nota 0,42-0,46), entao nao ha regra extra por correlacao (VERIFICACAO_CORRELACAO.md). Zona cinzenta 0,50-0,57
# (ex.: robos_desastrad_20260729_102749, 0,524, logo vista no quadro): rejeitar na mao.
MARCA_TIKTOK = Path(r"D:\postador-de-videos\config\marca_tiktok.png")
LIMIAR_TIKTOK = 0.57


def duracao(p):
    return float(subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, creationflags=_SEM_JANELA).stdout.strip())


def stats(p, filtro, ini=None):
    """[(t, {YAVG, YLOW, YHIGH})] do signalstats depois do filtro."""
    cmd = [FFMPEG, "-hide_banner"] + (["-ss", str(ini)] if ini is not None else []) + ["-i", str(p), "-vf",
           f"{filtro},signalstats,metadata=print", "-an", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          creationflags=_SEM_JANELA).stderr
    res, t = [], None
    for ln in out.splitlines():
        m = re.search(r"pts_time:([\d.]+)", ln)
        if m:
            t = float(m.group(1)) + (ini or 0)
            res.append((t, {}))
        m = re.search(r"lavfi\.signalstats\.(YAVG|YLOW|YHIGH)=([\d.]+)", ln)
        if m and res:
            res[-1][1][m.group(1)] = float(m.group(2))
    return res


def layout(p):
    """'34' quando o Veo veio 3:4 (faixa cinza lisa em cima do quadro), senao 'cheio'."""
    w, h, x, y = QUADRO
    s = stats(p, f"trim=1:3,fps=2,crop={w}:110:{x}:{y + 20}")
    lisas = [d for _, d in s if d.get("YHIGH", 99) - d.get("YLOW", 0) < 6]
    return "34" if s and len(lisas) >= len(s) * 0.8 else "cheio"


def corte_final(p, dur, lay):
    """Fim do clipe do Veo. Depois dele vem o slide de PROPAGANDA (produto + WhatsApp, imagem parada ate ~dur-2 s)
    e o cartao "Siga @InovareStories". Acha onde o brilho para de mudar ate o cartao e corta 0,5 s antes
    (a transicao para o slide). Reserva: 7,5 s (clipe de 8 s do Veo com 0,5 s de transicao).
    Devolve (corte, detectado): detectado=False = estrutura fora do padrao -> o video NAO e aprovado (revisar)."""
    w, h, x, y = QUADRO
    cw, ch, cy = (720, 960, 480) if lay == "34" else (w, h, y)
    s = [(t, d["YAVG"]) for t, d in stats(p, f"fps=4,crop={cw}:{ch}:{x}:{cy}") if "YAVG" in d]
    slide = [(t, v) for t, v in s if t <= dur - 2.3]
    inicio = None
    for i, (t, v) in enumerate(slide):
        if len(slide) - i >= 6 and all(abs(v2 - v) <= 2.0 for _, v2 in slide[i:]):
            inicio = t
            break
    if inicio is not None and 5.5 <= inicio - 0.5 <= 9.0:
        return round(inicio - 0.5, 2), True
    return 7.5, False


def resolucao(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of",
                        "csv=p=0", str(p)], capture_output=True, text=True, creationflags=_SEM_JANELA).stdout.strip().split(",")
    return int(r[0]), int(r[1])


def limpar(src, destino):
    """Devolve (dur, layout, corte, confiavel). 'cru' = 720x1280 de ~8 s: o clipe do Veo puro (sem marca, legenda,
    propaganda nem cartao - conferido em 15/10), so sobe para 1080x1920. Outro formato: ValueError (fica p/ revisar)."""
    dur = duracao(src)
    res = resolucao(src)
    if res == (720, 1280) and dur <= 9.0:
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(src), "-vf", "scale=1080:1920:flags=lanczos,setsar=1",
                        "-c:v", "libx264", "-threads", "3", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(destino)], check=True,
                       creationflags=_SEM_JANELA)
        return dur, "cru", round(dur, 2), True
    if res != (1080, 1920):
        raise ValueError(f"formato {res[0]}x{res[1]} de {dur:.1f} s fora do padrao")
    lay = layout(src)
    fim, detectado = corte_final(src, dur, lay)
    w, h, x, y = QUADRO
    if lay == "34":
        vf = (f"[0:v]crop=720:960:{x}:480,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,"
              "crop=1080:1920,boxblur=30:2,eq=brightness=-0.08[bg];[b]scale=1080:-2[fg];"
              "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]")
    else:
        # a legenda embutida passa um pouco do quadro 720x1280 (dos lados e embaixo): pega 900x1600 em volta dele
        # (borda preta fina, legenda inteira); a marca @InovareStories fica acima de y=80 e sai do mesmo jeito
        vf = "[0:v]crop=900:1600:90:160,scale=1080:1920,setsar=1[v]"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(src), "-t", str(fim), "-filter_complex", vf, "-map", "[v]",
                    "-map", "0:a?", "-c:v", "libx264", "-threads", "3", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(destino)], check=True,
                   creationflags=_SEM_JANELA)
    return dur, lay, fim, detectado and 14.0 <= dur <= 17.0


def nota_tiktok(mp4):
    """Maior semelhanca (0-1) com a logo do TikTok, 1 quadro por segundo, varias escalas, em cores (opencv)."""
    import cv2
    import numpy as np
    tpl = cv2.imread(str(MARCA_TIKTOK))
    w, h = 540, 960
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(mp4), "-vf", f"fps=1,scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], capture_output=True, creationflags=_SEM_JANELA).stdout
    melhor = 0.0
    for i in range(len(raw) // (w * h * 3)):
        quadro = np.frombuffer(raw[i * w * h * 3:(i + 1) * w * h * 3], np.uint8).reshape(h, w, 3)
        for esc in (0.25, 0.3, 0.35, 0.45, 0.55, 0.7):
            t = cv2.resize(tpl, None, fx=esc, fy=esc)
            melhor = max(melhor, float(cv2.minMaxLoc(cv2.matchTemplate(quadro, t, cv2.TM_CCOEFF_NORMED))[1]))
    return round(melhor, 3)


# erros do ffmpeg quando o arquivo abre mas o conteudo nao decodifica (copiado de D:\veo\beta\validar_video.py, 16/10):
# o ffprobe le o cabecalho e diz que esta tudo bem; so decodificando de verdade aparece. 27 dos 240 limpos eram assim.
_RX_DECODE = re.compile(r"Invalid NAL unit size|Error splitting the input into NAL units|missing picture in access unit|"
                        r"error while decoding|Invalid data found when processing input|could not find codec parameters",
                        re.I)


def decodifica(mp4):
    """None se o video toca do comeco ao fim; senao o motivo."""
    try:
        r = subprocess.run([FFMPEG, "-v", "error", "-i", str(mp4), "-f", "null", "-"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180, creationflags=_SEM_JANELA)
    except subprocess.TimeoutExpired:
        return "ffmpeg passou de 180 s decodificando"
    achado = _RX_DECODE.search(r.stderr or "")
    if r.returncode or achado:
        return f"arquivo quebrado, nao decodifica ({achado.group(0) if achado else f'ffmpeg saiu {r.returncode}'})"
    return None


GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")  # mesmo gateway do veo (antigravity/gemini-3-flash, com visao)
_PERG_MARCA = ("Esta imagem e o canto inferior direito de um video. Existe nela uma MARCA D'AGUA de texto ou logo de "
               "ferramenta de IA, como 'Grok', 'Veo', 'Sora', 'TikTok' ou outra? Responda SO com JSON: "
               '{"marca": "<nome da marca ou nenhuma>"}')
MOLDURA = ("moldura preta + legenda queimada (bruto montado de 15 s, 16/10): so o Veo puro (layout cru, tela cheia) "
           "vai ao ar")


def marca_ia(mp4):
    """Nome da marca d'agua de IA no canto inferior direito ("Grok", "Veo"...) ou None. 16/10: a foto de entrada feita
    no Grok leva o "Grok" para o video, e o Veo poe o "Veo" dele; o detector por molde (opencv) errava, a visao acerta.
    Olha 2 quadros, so o canto ampliado (1 pedido por quadro). Falha do gateway levanta: quem chama nao aprova."""
    import base64
    import urllib.request
    gw = json.loads(GATEWAY.read_text(encoding="utf-8"))
    url = gw.get("gateway_url", "http://157.173.207.22:20128").rstrip("/") + "/v1/chat/completions"
    dur = duracao(mp4) or 8
    for t in (min(2.0, dur / 4), dur * 0.75):
        img = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf",
                              "crop=iw*0.45:ih*0.12:iw*0.55:ih*0.88,scale=-1:240", "-f", "image2", "-vcodec", "mjpeg",
                              "-"], capture_output=True, creationflags=_SEM_JANELA).stdout
        corpo = {"model": "antigravity/gemini-3-flash", "max_tokens": 40, "messages": [{"role": "user", "content": [
            {"type": "text", "text": _PERG_MARCA},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(img).decode()}}]}]}
        req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={
            "Authorization": "Bearer " + gw["gateway_key"], "Content-Type": "application/json"})
        txt = json.loads(urllib.request.urlopen(req, timeout=60).read())["choices"][0]["message"]["content"]
        achou = re.search(r'"marca"\s*:\s*"([^"]*)"', txt)
        nome = (achou.group(1) if achou else txt).strip()
        if nome and not re.fullmatch(r"(?i)nenhuma|none|nao|não|-", nome):
            return nome
    return None


def conferir_marcas_ia():
    """Limpos ainda nao postados: moldura (layout cheio/34) ou marca d'agua de IA -> revisar + rejeitado (a rede e o
    TikTok/Instagram nao pegam). Guarda o resultado no json ('marca_ia') para nao perguntar de novo."""
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import politica
    tirados = 0
    for jp in sorted(SAIDA.glob("*.json")):
        meta = json.loads(jp.read_text("utf-8"))
        mp4 = jp.with_suffix(".mp4")
        if not mp4.exists() or meta.get("posted_url") or meta.get("revisar") or "marca_ia" in meta:
            continue
        if meta.get("layout") != "cru":
            motivo = MOLDURA
        else:
            try:
                meta["marca_ia"] = marca_ia(mp4)
            except Exception as ex:  # noqa: BLE001  (gateway fora: confere na proxima)
                print(f"  {mp4.name}: nao deu para conferir a marca ({str(ex)[:80]})")
                continue
            motivo = f"marca d'agua {meta['marca_ia']} no canto (16/10): nao postar" if meta["marca_ia"] else None
        if motivo:
            meta["revisar"] = motivo
            politica.marcar_aprovacao(mp4, "rejeitado", motivo)
            tirados += 1
            print(f"  {mp4.name}: {motivo[:60]} -> rejeitado")
        jp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    print(f"conferidos; tirados da fila: {tirados}")


def conferir_arquivos():
    """Decodifica os limpos ja feitos (sem 'decodifica' no json): quebrado -> revisar + rejeitado (a rede nao posta)."""
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import politica
    quebrados = 0
    for jp in sorted(SAIDA.glob("*.json")):
        meta = json.loads(jp.read_text("utf-8"))
        mp4 = jp.with_suffix(".mp4")
        if "decodifica" in meta or not mp4.exists():
            continue
        motivo = decodifica(mp4)
        meta["decodifica"] = motivo is None
        if motivo:
            meta["revisar"] = motivo
            politica.marcar_aprovacao(mp4, "rejeitado", motivo)
            quebrados += 1
            print(f"  {mp4.name}: {motivo} -> rejeitado")
        jp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    print(f"conferidos; quebrados: {quebrados}")


def conferir_marcas():
    """Passa o detector do TikTok nos limpos ja feitos (sem 'nota_tiktok' no json): com marca -> revisar + rejeitado."""
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import politica
    marcados = 0
    for jp in sorted(SAIDA.glob("*.json")):
        meta = json.loads(jp.read_text("utf-8"))
        mp4 = jp.with_suffix(".mp4")
        if "nota_tiktok" in meta or not mp4.exists():
            continue
        meta["nota_tiktok"] = nota_tiktok(mp4)
        if meta["nota_tiktok"] >= LIMIAR_TIKTOK:
            meta["revisar"] = f"marca/logo do TikTok no video (nota {meta['nota_tiktok']}): nao postar no YouTube"
            politica.marcar_aprovacao(mp4, "rejeitado", meta["revisar"])
            marcados += 1
            print(f"  {mp4.name}: MARCA DO TIKTOK ({meta['nota_tiktok']}) -> rejeitado")
        jp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    print(f"conferidos; com marca do TikTok: {marcados}")


def transcrever(mp4):
    """(fala, palavras com tempo) da transcricao do manhwa-react."""
    sys.path.insert(0, r"D:\manhwa-react")
    from mr import transcribe
    cfg = json.loads(Path(r"D:\manhwa-react\config.json").read_text("utf-8"))
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mp4), "-ac", "1", "-ar", "16000", str(wav)], check=True,
                       creationflags=_SEM_JANELA)
        res = transcribe.transcribe(cfg, wav, "pt")
    return " ".join(s["text"] for s in res["segments"]).strip(), res.get("words") or []


def loudnorm_filtro(mp4, alvo=-14, tp=-1, lra=11):
    """Filtro do 2o passo do loudnorm medido no 1o (copiado de D:\\manhwa-react\\mr\\audio.py: loudnorm_two_pass).
    Item AT-10 (16/10): o limpo ia ao ar sem nivelar (o COMPLETO medido estava em -17,2 LUFS). Sem medida: passo unico."""
    base = f"loudnorm=I={alvo}:TP={tp}:LRA={lra}"
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(mp4), "-vn", "-af", base + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                       creationflags=_SEM_JANELA)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr or "", re.S)
    if not m:
        return base
    j = json.loads(m.group(0))
    if j.get("input_i") in (None, "-inf"):  # sem audio de verdade
        return None
    return (base + f":measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
            f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")


def nivelar(mp4, af):
    """So o audio (o video vai copiado): para o limpo sem legenda."""
    with tempfile.TemporaryDirectory() as td:
        saida = Path(td) / "n.mp4"
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mp4), "-c:v", "copy", "-af", af, "-ar", "48000",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(saida)], check=True, timeout=300,
                       creationflags=_SEM_JANELA)
        shutil.move(str(saida), str(mp4))


def legendar(mp4, palavras, dur, af=None):
    """Queima a legenda palavra a palavra PELO AUDIO (mr/captions.py do react, so a legenda: sem gancho, marca, barra
    nem CTA). 16/10, item AT-03 do Veo: a legenda antiga espalhava o texto do prompt pelo tempo. Falhou -> fica sem."""
    sys.path.insert(0, r"D:\manhwa-react")
    from mr import captions
    from mr.common import ffpath
    cfg = json.loads(Path(r"D:\manhwa-react\config.json").read_text("utf-8"))
    cfg["overlays"] = dict(cfg["overlays"], hook=False, watermark=False, progress_bar=False, keywords=False, cta=False)
    # sem divisoria o build_ass poe a legenda a 62% da altura: no Veo (rosto no centro) cobria a boca (quadros de 16/10).
    # divider_out=1620 -> legenda em 1620-120 = 1500 (78%): abaixo do queixo e acima dos botoes do Shorts
    ass = captions.build_ass(cfg, palavras, dur, {"divider_out": 1620}, {})
    fontes = Path(cfg["paths"]["assets"]) / "fonts"
    with tempfile.TemporaryDirectory() as td:
        ass_p, saida = Path(td) / "l.ass", Path(td) / "l.mp4"
        ass_p.write_text(ass, "utf-8")
        audio = ["-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k"] if af else ["-c:a", "copy"]
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mp4), "-vf",
                        f"ass={ffpath(ass_p)}:fontsdir={ffpath(fontes)},format=yuv420p", "-c:v", "libx264", "-crf", "18",
                        "-preset", "veryfast", *audio, "-movflags", "+faststart", str(saida)],
                       check=True, timeout=300, creationflags=_SEM_JANELA)
        shutil.move(str(saida), str(mp4))


def processar(src, origem):
    destino = SAIDA / src.name
    meta_p = destino.with_suffix(".json")
    if meta_p.exists():
        return None
    SAIDA.mkdir(parents=True, exist_ok=True)
    tema = re.split(r"_20\d{6}", src.stem)[0]
    try:
        dur, lay, fim, ok = limpar(src, destino)
    except (ValueError, subprocess.CalledProcessError) as ex:
        # nao para o lote: grava o motivo (sem mp4, a rede ignora) e segue
        destino.unlink(missing_ok=True)
        meta_p.write_text(json.dumps({"arquivo": None, "tema": tema, "origem": origem, "revisar": f"nao limpou: {ex}",
                                      "criado": datetime.now().isoformat(timespec="seconds")},
                                     ensure_ascii=False, indent=1), "utf-8")
        print(f"  {src.name}: NAO LIMPOU ({str(ex)[:120]})")
        return None
    try:
        fala, palavras = transcrever(destino)
    except Exception as ex:  # noqa: BLE001
        fala, palavras = "", []
        print(f"  transcricao falhou: {ex}")
    tk = nota_tiktok(destino)
    quebrado = decodifica(destino)
    marca = None
    if not quebrado and lay == "cru":
        try:
            marca = marca_ia(destino)
        except Exception as ex:  # noqa: BLE001
            marca = f"(nao conferida: {str(ex)[:60]})"
    # aprovado pra rede so o Veo puro (cru, tela cheia; desde 16/10 o bruto montado de 15 s fica de fora: moldura preta e
    # legenda queimada), sem marca d'agua (TikTok, Grok, Veo) e que decodifica do comeco ao fim
    estrutura_ok = ok
    if quebrado:
        ok, revisar = False, quebrado
    elif lay != "cru":
        ok, revisar = False, MOLDURA
    elif marca:
        ok, revisar = False, f"marca d'agua {marca} no canto (16/10): nao postar"
    elif not ok:
        revisar = (f"estrutura fora do padrao (bruto {dur:.1f} s, corte {fim} s): conferir se sobrou propaganda e aprovar "
                   "na mao (manhwareact.py rede --aprovar)")
    elif tk >= LIMIAR_TIKTOK:
        ok, revisar = False, f"marca/logo do TikTok no video (nota {tk}): nao postar no YouTube"
    else:
        revisar = None
    repete = None
    if not quebrado:  # dedupe de VIDEO (AB-08, D:\veo\beta\dedupe_video.py): quase o mesmo clipe de um limpo ja feito
        try:
            sys.path.insert(0, r"D:\veo\beta")
            import dedupe_video
            ind = dedupe_video.carregar()
            hs = dedupe_video.hashes(destino)
            repete = dedupe_video.repetido(destino, ignorar=destino.stem, ind=ind, hs=hs)
            ind[destino.stem] = hs
            dedupe_video.guardar(ind)
        except Exception as ex:  # noqa: BLE001
            print(f"  dedupe de video falhou: {ex}")
        if repete and ok:
            ok, revisar = False, f"clipe repetido de {repete[0]} ({repete[1]:.0%} dos quadros, dedupe de video 16/10)"
    antisynthid_ok = None
    if ok:  # antes da legenda (23/10): o ruido/blur dele nao borra a legenda e o volume e medido no audio final
        try:
            sys.path.insert(0, r"D:\postador-de-videos\bin")
            import antisynthid
            with tempfile.TemporaryDirectory(prefix="antisynthid_") as atd:
                tmp_as = Path(atd) / destino.name
                if antisynthid.processar(destino, tmp_as):
                    shutil.move(str(tmp_as), str(destino))
                    antisynthid_ok = True
                else:
                    antisynthid_ok = False
                    print(f"  {src.name}: antisynthid falhou (manteve o original)")
        except Exception as ex:  # noqa: BLE001
            antisynthid_ok = f"erro: {str(ex)[:80]}"
            print(f"  {src.name}: antisynthid erro: {ex}")
    legenda = nivel = None
    if ok:  # depois dos detectores: a legenda nao pode confundir o de marca
        try:
            af = loudnorm_filtro(destino)
        except Exception as ex:  # noqa: BLE001
            af = None
            print(f"  medida de volume falhou: {ex}")
        try:
            if palavras:
                legendar(destino, palavras, fim, af)  # legenda + volume na mesma recodificacao
                legenda = "audio"
            elif af:
                nivelar(destino, af)
            nivel = "-14 LUFS" if af else None
        except Exception as ex:  # noqa: BLE001
            legenda = f"falhou: {str(ex)[:80]}" if palavras else None
            print(f"  legenda/volume falhou: {ex}")
    meta = {"arquivo": destino.name, "tema": tema, "fala": fala, "legenda": legenda, "volume": nivel, "duracao": fim,
            "duracao_bruto": dur, "layout": lay, "corte_detectado": estrutura_ok, "nota_tiktok": tk, "origem": origem,
            "decodifica": quebrado is None, "marca_ia": marca, "antisynthid": antisynthid_ok,
            "revisar": revisar, "criado": datetime.now().isoformat(timespec="seconds")}
    if ok:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import politica
        politica.marcar_aprovacao(destino, "aprovado", "Veo limpo (bin/limpar_veo.py): pedido do dono 15/10, "
                                                       "InventoReact/ManhwaReact")
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    print(f"  {src.name}: {lay}, corte {fim}s de {dur}s{'' if ok else ' [REVISAR]'} | {fala[:90]}")
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivos", nargs="*")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--drive", action="store_true", help="tambem os brutos que so estao no Drive (baixa um por vez)")
    ap.add_argument("--conferir", action="store_true", help="so passa o detector de marca do TikTok nos limpos ja feitos")
    ap.add_argument("--conferir-arquivos", action="store_true",
                    help="so decodifica os limpos ja feitos: quebrado vira revisar + rejeitado")
    ap.add_argument("--conferir-marcas-ia", action="store_true",
                    help="so confere moldura e marca d'agua de IA (Grok/Veo) nos limpos ainda nao postados")
    a = ap.parse_args()
    if a.conferir:
        conferir_marcas()
        return
    if a.conferir_marcas_ia:
        conferir_marcas_ia()
        return
    if a.conferir_arquivos:
        conferir_arquivos()
        return
    feitos = 0
    fontes = [Path(f) for f in a.arquivos] or (
        sorted(p for p in NOVOS.glob("*.mp4") if not p.name.startswith("teste")) + sorted(BRUTOS.glob("*.mp4")))
    pendentes = [src for src in fontes if not (SAIDA / src.name).with_suffix(".json").exists()]
    if not pendentes and not a.drive:
        print("limpos: 0")
        return
    # um render do veo por vez (BX-03): ocupado -> sai; a tarefa de hora em hora tenta de novo e a rede nao espera
    sys.path.insert(0, r"D:\veo\beta")
    from trava_render import TravaOcupada, trava_render
    try:
        with trava_render("limpar_veo"):
            _limpar_lote(a, pendentes)
    except TravaOcupada as ex:
        print(f"limpar_veo: {ex} - fica para a proxima rodada")


def _limpar_lote(a, pendentes):
    feitos = 0
    for src in pendentes:
        if a.max and feitos >= a.max:
            return
        if processar(src, str(src)):
            feitos += 1
    if a.drive and not a.arquivos:
        nomes = subprocess.run([RCLONE, "lsf", DRIVE_BRUTOS, "--include", "*.mp4"], capture_output=True, text=True,
                               encoding="utf-8", creationflags=_SEM_JANELA).stdout.split()
        for nome in sorted(set(nomes)):
            if (a.max and feitos >= a.max) or (SAIDA / nome).with_suffix(".json").exists():
                continue
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td) / nome
                subprocess.run([RCLONE, "copyto", f"{DRIVE_BRUTOS}/{nome}", str(tmp), "--retries", "3"], check=False,
                               creationflags=_SEM_JANELA)
                if tmp.exists() and processar(tmp, f"{DRIVE_BRUTOS}/{nome}"):
                    feitos += 1
    print(f"limpos: {feitos}")


if __name__ == "__main__":
    main()
