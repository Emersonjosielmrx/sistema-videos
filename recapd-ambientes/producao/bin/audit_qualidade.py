import os
import json
import subprocess
from pathlib import Path

BASE = Path("D:/recapd-ambientes/producao/workspace/anime")

def get_durations(filepath):
    """Retorna (dur_video, dur_audio) usando ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,duration", "-of", "json", str(filepath)
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        data = json.loads(out)
        v_dur = 0.0
        a_dur = 0.0
        for s in data.get("streams", []):
            if s.get("codec_type") == "video" and "duration" in s:
                v_dur = float(s["duration"])
            elif s.get("codec_type") == "audio" and "duration" in s:
                a_dur = float(s["duration"])
        return v_dur, a_dur
    except:
        return 0.0, 0.0

print("🔍 Iniciando Auditoria de Qualidade em vídeos já processados...")

erros_sincronia = []
erros_roteiro = []
erros_sem_audio = []

for work_dir in BASE.iterdir():
    if not work_dir.is_dir(): continue
    
    # Verifica qualidade do Roteiro
    roteiro = work_dir / "roteiro.txt"
    if roteiro.exists():
        texto = roteiro.read_text(encoding="utf-8")
        # Procura caracteres indesejados tipo markdown, asteriscos, aspas duplas soltas, emojis (básico)
        if "*" in texto or "\"" in texto or "!"*4 in texto or "?"*4 in texto:
             erros_roteiro.append(work_dir.name)
             
    # Verifica descompassos de Video x Audio nos finais
    for v_name in ["final_anime_deitado.mp4", "final_anime_short.mp4"]:
        v_path = work_dir / v_name
        if v_path.exists():
            v_dur, a_dur = get_durations(v_path)
            
            if a_dur == 0.0:
                erros_sem_audio.append(work_dir.name + " (" + v_name + ")")
                continue
                
            # Verifica se áudio e vídeo estão descompassados demais (> 5 seg)
            # Como consta no CLAUDE.md: "se áudio >5s menor que vídeo = QUEBRADO."
            if abs(v_dur - a_dur) > 5.0:
                erros_sincronia.append(f"{work_dir.name} ({v_name}) -> V:{v_dur:.1f}s | A:{a_dur:.1f}s")


print(f"\n📑 {len(erros_roteiro)} roteiros com sujeira visual (*, aspas).")
if erros_roteiro:
    for e in erros_roteiro[:5]: print(f"   - {e}")

print(f"\n🔇 {len(erros_sem_audio)} vídeos renderizados SEM ÁUDIO.")
if erros_sem_audio:
    for e in erros_sem_audio[:5]: print(f"   - {e}")

print(f"\n⏱ {len(erros_sincronia)} vídeos com DESCOMPASSO GRAVE Áudio/Vídeo (>5s de gap).")
if erros_sincronia:
    for e in erros_sincronia[:10]: print(f"   - {e}")

