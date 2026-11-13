# Teste 7 (01/11): hipótese = o vídeo recém-enviado ainda está sendo processado quando a geração começa.
# J = vídeo base e3e7691f (enviado há ~10 min, falhou na hora) + o prompt GENÉRICO que "falhava".
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
from services.veo_flow.flow_gerar import FlowGerador  # noqa: E402

D = Path(r"D:\tmp_motion\teste")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with FlowGerador("fabiovideoseducativos") as fg:
    print("base:", fg.f.midias(["e3e7691f-3e97-4d4f-a49f-b1a23ee15e9e"]), flush=True)
    mid = fg.pedir("Use the generate_video_edit_video tool with Omni Flash, aspect ratio 9:16. Base video: "
                   "e3e7691f-3e97-4d4f-a49f-b1a23ee15e9e. Reference image: cc876648-2e4a-4283-b38a-3b547f97f54c. "
                   "Edit: the person in the video becomes the person from the reference image (same face, hair, body "
                   "and clothes), doing exactly the same movements, gestures, expressions and timing as in the video. "
                   "Use the background and lighting of the reference image.")["midias"][0]["media_id"]
    print("J pedido", mid, flush=True)
    fg.soltar_chrome()
    fim = time.time() + 900
    while time.time() < fim:
        time.sleep(20)
        falha = fg.f.falha_geracao(mid)
        if falha:
            print("J FALHOU", falha, flush=True)
            break
        try:
            arq, tipo, _ = fg.f.baixar(mid, D / "edit_J.mp4")
            if (tipo or "").startswith("video"):
                print("J OK", arq, flush=True)
                break
        except Exception:  # noqa: BLE001
            pass
    print("creditos", fg.f.creditos(), flush=True)
