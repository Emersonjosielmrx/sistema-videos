"""anime-pipeline.py — orquestrador do recap de anime descaracterizado.

Só amarra as peças (cada uma num módulo pequeno):
  anime_tts.py      → narração
  anime_probe.py    → duração de mídia
  anime_segments.py → corte+descaracterização dos clipes
  anime_captions.py → legenda queimada (PNG overlay)
  fx_clips.py       → concat final (reuso do motor hipercool)

IMPORTANTE — orientação por PROCESSO:
  O motor (fx_assets) decide W/H no IMPORT, lendo ANIME_ORIENT. Por isso cada
  formato roda num subprocesso próprio: o dispatcher (main) só dispara; o
  trabalho pesado roda em run_one(), que importa o motor já na orientação certa.

Uso:
  python anime-pipeline.py --video-source anime.mp4 --script roteiro.txt
  python anime-pipeline.py ... --formato deitado   # só 16:9
  python anime-pipeline.py ... --formato short     # só 9:16
"""
import sys
import os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import logging
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                    ])
_stream_handler = logging.root.handlers[0]
try:
    _stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Formato → (orientação do motor, nome do arquivo final)
_FORMATS = {
    "deitado": ("landscape", "final_anime_deitado.mp4"),
    "short":   ("vertical",  "final_anime_short.mp4"),
}


def parse_txt_script(script_path):
    """Lê o roteiro .txt (1 frase por linha) e devolve a lista de frases não-vazias.
    Cada frase vira um clipe: é narrada (TTS) e mapeada sobre uma fatia do vídeo."""
    with open(script_path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def run_one(video_path, script_path, orient, out_name, max_panels):
    """Gera UM formato. Roda num processo onde ANIME_ORIENT já está setado
    ANTES de importar o motor, então W/H nascem na orientação certa."""
    # imports pesados aqui dentro (pós-ANIME_ORIENT), não no topo do módulo.
    from anime_segments import build_segments
    from anime_captions import burn_captions
    from fx_clips import concat_with_xfade

    workspace = Path(video_path).parent
    lines = parse_txt_script(script_path)
    if max_panels > 0:
        lines = lines[:max_panels]
    if not lines:
        logging.error("Script vazio")
        return False

    # Áudio TTS COMPARTILHADO entre as orientações (gera 1x, reusa).
    audio_dir = workspace / "audio_cache"
    clip_dir = workspace / f"clipes_{orient}"

    clips, entries, sfx_durs = build_segments(video_path, lines, clip_dir,
                                    audio_dir=audio_dir, orient=orient)
    if not clips:
        logging.error(f"[{orient}] nenhum clipe gerado")
        return False

    logging.info(f"[{orient}] concatenando {len(clips)} clipes...")
    concat_out = str(workspace / f"_semlegenda_{orient}.mp4")
    concat_with_xfade(clips, concat_out, clip_sfx_dur=sfx_durs)

    # -- Integração de Música Dinâmica --
    # Independência TOTAL: usa SÓ as trilhas do próprio projeto
    # (workspace/assets/trilhas, que é junction pro hub compartilhado
    # hipercool-materiais — a única pasta externa permitida). Sem fallback pra
    # outras pastas hipercool: apagar qualquer uma delas não quebra o recap.
    _trilhas_dir = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "trilhas"
    if _trilhas_dir.exists() and (_trilhas_dir / "moods.json").exists():
        import effects_engine
        
        # Mapeamos o texto para o formato que add_dynamic_music gosta 
        # (lista de descrições para inferir o mood). 
        # No formato antigo era recap["locucoes"].
        mock_locucoes = [{"texto": e[0]} for e in entries]
        
        logging.info(f"[{orient}] queimando música dinâmica...")
        concat_music = str(workspace / f"_semlegenda_music_{orient}.mp4")
        effects_engine.add_dynamic_music(Path(concat_out), mock_locucoes, Path(concat_music),
                                         _trilhas_dir, music_volume=0.18, no_copyright=False)
                                         
        if Path(concat_music).exists():
            Path(concat_out).unlink()
            Path(concat_music).rename(concat_out)

    final_out = str(workspace / out_name)
    logging.info(f"[{orient}] queimando legendas...")
    if not burn_captions(concat_out, entries, final_out, orient=orient):
        logging.warning(f"[{orient}] legenda falhou — usando sem legenda")
        import shutil
        shutil.copy2(concat_out, final_out)

    logging.info(f"[{orient}] PRONTO: {final_out}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Recap de anime descaracterizado (narração TTS)")
    parser.add_argument("--video-source", required=True, help="Arquivo de video original mp4")
    parser.add_argument("--script", required=True, help="Arquivo txt com as frases (roteiro)")
    parser.add_argument("--titulo", default="Anime Recap", help="Título")
    parser.add_argument("--skip-notify", action="store_true", help="Pula a notificação")
    parser.add_argument("--max-panels", type=int, default=1000, help="Limite de frases (teste)")
    parser.add_argument("--formato", choices=["deitado", "short", "ambos"], default="ambos",
                        help="deitado (16:9 principal), short (9:16) ou ambos")
    parser.add_argument("--short-source-kind", choices=["native", "reframe"], default="reframe",
                        help="Se o short usa fonte vertical nativa ou vai emoldurar vídeo horizontal")
    parser.add_argument("--cover-hardsub", action="store_true",
                        help="Fonte tem legenda queimada (hard-sub): põe tarja fosca no rodapé "
                             "cobrindo a legenda velha (espelhada pelo hflip) antes da nossa PT")
    # interno: quando setado, este processo gera SÓ um formato (não redispatcha).
    parser.add_argument("--_orient", choices=["landscape", "vertical"], help=argparse.SUPPRESS)
    parser.add_argument("--_out-name", help=argparse.SUPPRESS)
    args = parser.parse_args()

    # Modo worker: um formato só, orientação já fixada pela env no import.
    if args._orient:
        ok = run_one(args.video_source, args.script, args._orient,
                     args._out_name, args.max_panels)
        sys.exit(0 if ok else 1)

    # Modo dispatcher: dispara um subprocesso por formato pedido.
    formatos = ["deitado", "short"] if args.formato == "ambos" else [args.formato]
    falhou = False
    for fmt in formatos:
        orient, out_name = _FORMATS[fmt]
        logging.info(f"===== Disparando formato: {fmt} ({orient}) =====")
        env = dict(os.environ, ANIME_ORIENT=orient, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        if fmt == "short":
            env["ANIME_SHORT_SOURCE"] = args.short_source_kind
        if args.cover_hardsub:
            env["ANIME_HARDSUB_COVER"] = "1"
        cmd = [sys.executable, os.path.abspath(__file__),
               "--video-source", args.video_source,
               "--script", args.script,
               "--max-panels", str(args.max_panels),
               "--_orient", orient, "--_out-name", out_name]
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            logging.error(f"[{fmt}] subprocesso falhou (rc={r.returncode})")
            falhou = True

    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()
