#!/usr/bin/env python3
"""_pc2_seg_test.py — testa build_segments nas 3 primeiras frases pra achar onde trava.
Roda no PC2 via task agendada (desacoplado do SSH instavel). Loga cada passo.
"""
import sys, os, time, glob, traceback
sys.path.insert(0, "C:/recapd-e-animes/bin")
os.environ["PYTHONUTF8"] = "1"
os.environ["ANIME_ORIENT"] = "landscape"

LOG = "C:/recapd-e-animes/workspace/seg_test.log"
def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)

def main():
    log("=== seg_test inicio ===")
    wds = sorted(glob.glob(os.path.expandvars(r"C:/Users/Emerson-IA/AppData/Local/Temp/anime_worker_*")),
                 key=os.path.getmtime, reverse=True)
    if not wds:
        log("sem workdir"); return
    w = wds[0]
    log("workdir=" + w)
    src = os.path.join(w, "source.mp4")
    rot = os.path.join(w, "roteiro.txt")
    lines = [l.strip() for l in open(rot, encoding="utf-8") if l.strip()][:3]
    log("lines=%d (testando 3)" % len(lines))

    # Passo a passo: primeiro so o narrate isolado (a etapa que suspeitamos travar)
    try:
        import anime_tts
        for i, ln in enumerate(lines):
            t = time.time()
            log("narrate %d start: %s" % (i, ln[:40]))
            wav = anime_tts.narrate(ln, os.path.join(w, "audio_cache", "seg_test_%d.wav" % i))
            log("narrate %d -> %s (%.1fs)" % (i, bool(wav), time.time() - t))
    except Exception as e:
        log("ERRO narrate: %s\n%s" % (e, traceback.format_exc()))
        return

    # Agora build_segments completo nas 3 frases
    try:
        import anime_segments as S
        t = time.time()
        log("build_segments start")
        clips, entries, sfx, word_times = S.build_segments(src, lines, os.path.join(w, "segtest_clips"),
                                               audio_dir=os.path.join(w, "audio_cache"), orient="landscape")
        log("build_segments DONE clips=%d (%.1fs)" % (len(clips), time.time() - t))
    except Exception as e:
        log("ERRO build_segments: %s\n%s" % (e, traceback.format_exc()))
        return
    log("=== seg_test fim OK ===")

if __name__ == "__main__":
    main()
