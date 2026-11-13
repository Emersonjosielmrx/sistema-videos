import json
from datetime import datetime
from pathlib import Path

METRICS_FILE = Path(__file__).resolve().parent.parent / "workspace" / "pipeline_metrics.jsonl"

def record_job(vid, titulo, modo, status, reason="", orig_dur=0.0, lines=0, final_v=0.0, final_a=0.0, ar=0.0):
    """Grava estado do processamento de modo estruturado para análise futura."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Delta (descompasso de sincronia)
    sync_delta = round(abs(float(final_v or 0) - float(final_a or 0)), 2)
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "video_id": vid,
        "titulo": titulo,
        "modo": modo,
        "status": status,  # SUCESSO ou FALHA
        "reason_fail": reason,
        "orig_dur_s": round(float(orig_dur), 1) if orig_dur else 0.0,
        "script_lines": int(lines) if lines else 0,
        "final_v_dur_s": round(float(final_v), 1) if final_v else 0.0,
        "final_a_dur_s": round(float(final_a), 1) if final_a else 0.0,
        "sync_delta_s": sync_delta,
        "aspect_ratio": round(float(ar), 3) if ar else 0.0
    }
    
    with open(METRICS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

