import re

with open("D:/recapd-ambientes/producao/bin/anime_auto.py", "r", encoding="utf-8") as f:
    codigo = f.read()

# Importar o metrics
codigo = codigo.replace("import anime_probe\n", "import anime_probe\nimport anime_metrics\n")

## Patch em Fazer Deitado
def_deitado = """def fazer_deitado(cand, target_lines, dry_run):
    \"\"\"Fluxo para recap longo (deitado 16:9).\"\"\"
    _marca_feito(cand["id"], "deitado_attempted")

    work, video, txt = _prepara_candidato(cand)
    if not work:
        if work and work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", "Baixar ou Transcrição falhou")
        return False

    orig_dur = anime_probe.video_duration(str(video))

    roteiro = work / "roteiro.txt"
    n = anime_script.rewrite_to_file(txt, roteiro, target_lines=target_lines)
    if n == 0:
        if work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", "Roteirização falhou/Recusa IA", orig_dur=orig_dur)
        return False
    logging.info(f"[auto|deitado] roteiro longo: {n} frases")

    if dry_run:
        logging.info("[auto] DRY-RUN — parou antes de renderizar")
        return True

    cmd = [sys.executable, str(PIPELINE),
           "--video-source", str(video), "--script", str(roteiro),
           "--titulo", cand["title"], "--formato", "deitado"]
    r = subprocess.run(cmd, env=dict(os.environ, PYTHONUTF8="1"))
    if r.returncode != 0:
        logging.error(f"[auto|deitado] pipeline falhou (rc={r.returncode})")
        anime_metrics.record_job(cand["id"], cand["title"], "deitado", "FALHA", f"Pipeline rc={r.returncode}", orig_dur=orig_dur, lines=n)
        return False

    _marca_feito(cand["id"], "deitado")
    
    # Coleta metricas finais de SUCESSO antes de limpar
    vf = work / "final_anime_deitado.mp4"
    af_dur, vf_dur = 0.0, 0.0
    if vf.exists():
        vf_dur = anime_probe.video_duration(str(vf))
        try:
           import json
           out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(vf)], capture_output=True, text=True).stdout
           d = json.loads(out)
           for s in d.get("streams",[]):
               if s.get("codec_type") == "audio": af_dur = float(s.get("duration", 0))
        except: pass
    
    _cleanup_workspace(work)
    logging.info(f"[auto|deitado] PRONTO: {work}")
    anime_metrics.record_job(cand["id"], cand["title"], "deitado", "SUCESSO", orig_dur=orig_dur, lines=n, final_v=vf_dur, final_a=af_dur)
    return True
"""
codigo = re.sub(r'def fazer_deitado\(cand, target_lines, dry_run\):.*?return True', def_deitado, codigo, flags=re.DOTALL)


## Patch em Fazer Short
def_short = """def fazer_short(cand, target_lines, dry_run):
    \"\"\"Fluxo para formato curto (9:16).\"\"\"
    _marca_feito(cand["id"], "short_attempted")

    work, video, txt = _prepara_candidato(cand)
    if not work:
        if work and work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", "Baixar ou Transcrição falhou")
        return False

    orig_dur = anime_probe.video_duration(str(video))
    target_lines = max(5, int(orig_dur / 4)) if orig_dur else 12 
    logging.info(f"[auto|short] Duração do original: {orig_dur:.1f}s -> Alvo setado: {target_lines} linhas dinâmicas.")

    roteiro = work / "roteiro.txt"
    n = anime_script.rewrite_to_file(txt, roteiro, target_lines=target_lines)
    if n == 0:
        if work.exists(): shutil.rmtree(work)
        anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", "Roteirização falhou/Recusa IA", orig_dur=orig_dur)
        return False
    logging.info(f"[auto|short] roteiro curto: {n} frases")

    short_kind = "native"
    ar = 0.0
    if not anime_probe.is_vertical(str(video)):
        w, h = anime_probe.video_dimensions(str(video))
        logging.warning(f"[auto|short] fonte NÃO é vertical ({w}x{h}). Usando SOURCE=reframe (fallback).")
        short_kind = "reframe"
        ar = w/float(h) if h else 0.0
    else:
        logging.info("[auto|short] fonte confirmada VERTICAL. Usando SOURCE=native.")
        short_kind = "native"
        w, h = anime_probe.video_dimensions(str(video))
        ar = w/float(h) if h else 0.0

    if dry_run:
        logging.info("[auto] DRY-RUN — parou antes de renderizar")
        return True

    cmd = [sys.executable, str(PIPELINE),
           "--video-source", str(video), "--script", str(roteiro),
           "--titulo", cand["title"], "--formato", "short",
           "--short-source-kind", short_kind]
    r = subprocess.run(cmd, env=dict(os.environ, PYTHONUTF8="1"))
    if r.returncode != 0:
        logging.error(f"[auto|short] pipeline falhou (rc={r.returncode})")
        anime_metrics.record_job(cand["id"], cand["title"], "short", "FALHA", f"Pipeline rc={r.returncode}", orig_dur=orig_dur, lines=n, ar=ar)
        return False

    _marca_feito(cand["id"], "short")
    
    # Coleta metricas finais de SUCESSO antes de limpar
    vf = work / "final_anime_short.mp4"
    af_dur, vf_dur = 0.0, 0.0
    if vf.exists():
        vf_dur = anime_probe.video_duration(str(vf))
        try:
           import json
           out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(vf)], capture_output=True, text=True).stdout
           d = json.loads(out)
           for s in d.get("streams",[]):
               if s.get("codec_type") == "audio": af_dur = float(s.get("duration", 0))
        except: pass

    _cleanup_workspace(work)
    logging.info(f"[auto|short] PRONTO: {work}")
    anime_metrics.record_job(cand["id"], cand["title"], "short", "SUCESSO", orig_dur=orig_dur, lines=n, final_v=vf_dur, final_a=af_dur, ar=ar)
    return True
"""
codigo = re.sub(r'def fazer_short\(cand, target_lines, dry_run\):.*?return True', def_short, codigo, flags=re.DOTALL)

with open("D:/recapd-ambientes/producao/bin/anime_auto.py", "w", encoding="utf-8") as f:
    f.write(codigo)
