import re

with open("D:/recapd-ambientes/producao/bin/anime_auto.py", "r", encoding="utf-8") as f:
    codigo = f.read()

novo_codigo = codigo.replace(
    "if fazer_short(c, target_lines=10, dry_run=args.dry_run):",
    "# Duração original baseada em tempo para os shorts\n            if fazer_short(c, target_lines=None, dry_run=args.dry_run):"
)

# Precisamos corrigir também dentro da func fazer_short
def_fazer_short = """def fazer_short(cand, target_lines, dry_run):
    \"\"\"Fluxo para formato curto (9:16).\"\"\"
    # Marca como tentado para evitar loop infinito em caso de crash (OOM do Whisper)
    _marca_feito(cand["id"], "short_attempted")

    work, video, txt = _prepara_candidato(cand)
    if not work:
        if work and work.exists(): shutil.rmtree(work) # Falhou baixar/transcrever, apaga lixo temporal
        return False

    # Vamos calcular o target_lines sendo dinâmico ao Short original de forma natural
    from anime_probe import video_duration
    orig_dur = video_duration(str(video))
    # Em média, uma linha do script gera 3-4 segundos de fala do Gemini.
    target_lines = max(5, int(orig_dur / 4)) if orig_dur else 12 
    logging.info(f"[auto|short] Duração do original: {orig_dur:.1f}s -> Alvo setado: {target_lines} linhas dinâmicas.")

    roteiro = work / "roteiro.txt"
    # Target lines bem menor pra caber em 1 min
    n = anime_script.rewrite_to_file(txt, roteiro, target_lines=target_lines)
    if n == 0:
        if work.exists(): shutil.rmtree(work) # Falhou roteirizacao (lixo real/IA recusou), limpa o diretorio
        return False
    logging.info(f"[auto|short] roteiro curto: {n} frases")
"""

codigo = re.sub(r'def fazer_short\(cand, target_lines, dry_run\):.*?logging\.info\(f"\[auto\|short\] roteiro curto: \{n\} frases"\)', def_fazer_short, novo_codigo, flags=re.DOTALL)

with open("D:/recapd-ambientes/producao/bin/anime_auto.py", "w", encoding="utf-8") as f:
    f.write(codigo)
