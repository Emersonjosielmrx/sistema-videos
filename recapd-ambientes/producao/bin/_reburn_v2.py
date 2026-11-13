"""_reburn_v2.py — re-queima legendas no vídeo v2 que saiu SEM legenda.

O pipeline v2 gerou _semlegenda_landscape.mp4 (40min, com música) mas o
burn_subtitles estourou o timeout no batch 01 -> fallback sem legenda.
Aqui reconstruímos as `entries` (texto, duração) a partir dos WAVs/clipes em
cache (sem re-rodar TTS) e re-queimamos com o fx_subtitles já corrigido.
"""
import os, sys, logging
from pathlib import Path

os.environ["ANIME_ORIENT"] = "landscape"
os.environ["PYTHONUTF8"] = "1"
os.environ["ANIME_SUB_ENGINE"] = "ass"  # libass: 1 passada só (não 54 do PNG overlay)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

WS = Path(r"D:\recapd-ambientes\producao\workspace\anime\YfDVrAfh4dU_Nasceu_Sem_Talento_Magico")
ROTEIRO = WS / "roteiro_v2.txt"
AUDIO = WS / "audio_cache"
CLIPS = WS / "clipes_landscape"
SEMLEG = WS / "_semlegenda_landscape.mp4"
FINAL = WS / "final_anime_deitado.mp4"

sys.path.insert(0, str(Path(__file__).parent))
from anime_captions import burn_captions
from anime_segments import audio_duration

with open(ROTEIRO, encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip()]

# Reconstrói entries EXATAMENTE como build_segments faz: só as frases cujo
# clipe E áudio existem em cache entram, na ordem do índice.
entries = []
for i, line in enumerate(lines):
    wav = AUDIO / f"audio_{i}.wav"
    clip = CLIPS / f"clip_{i}.mp4"
    if not (wav.exists() and clip.exists()):
        continue
    dur = audio_duration(str(wav))
    if dur <= 0:
        continue
    entries.append((line, dur))

logging.info(f"entries reconstruídas: {len(entries)} (esperado ~636)")
if not entries:
    sys.exit("ERRO: nenhuma entry reconstruída")

logging.info("re-queimando legendas com fx_subtitles corrigido...")
ok = burn_captions(str(SEMLEG), entries, str(FINAL), orient="landscape")
if not ok:
    sys.exit("ERRO: burn_captions falhou de novo")
logging.info(f"PRONTO com legenda: {FINAL}")
