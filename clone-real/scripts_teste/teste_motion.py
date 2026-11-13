# Teste real do Motion Sync (01/11): imagem fictícia (Nano Banana) + vídeo de dança -> flow_gerar.motion
import json
import sys
import traceback

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador  # noqa: E402

D = r"D:\tmp_motion\teste"
VID = r"D:\veo\beta\videos\cron_shorts\danca_e_musica__20261101_161853.mp4"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    with FlowGerador("fabiovideoseducativos") as fg:
        print("creditos antes", fg.f.creditos(), flush=True)
        r = fg.imagem("Photorealistic vertical portrait of a young woman with long curly red hair, green sweater, "
                      "standing in a cozy bright kitchen, waist-up, looking at the camera, natural light.",
                      D + r"\aparencia.png")
        print("imagem ok", r["arquivos"], flush=True)
        r = fg.motion(D + r"\aparencia.png", VID, D + r"\motion_resultado.mp4")
        print("MOTION OK", r["arquivos"], r.get("texto", "")[:300], flush=True)
        print("creditos depois", fg.f.creditos(), flush=True)
except Exception as e:
    traceback.print_exc()
    print("FALHOU", type(e).__name__, str(e)[:800], flush=True)
