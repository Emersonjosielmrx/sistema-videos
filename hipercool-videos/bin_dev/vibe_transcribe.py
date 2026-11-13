#!/usr/bin/env python
"""vibe_transcribe.py - Transcreve um arquivo de audio via Gemini (ditado de voz).

Uso:  python vibe_transcribe.py <arquivo.wav>
Saida: a transcricao em portugues no stdout (so o texto, nada mais).
Reusa bin/gemini_llm.py (rotacao de 42 chaves + modelos).
"""
import sys
import os

# Garante que o bin do projeto esta no path pra importar gemini_llm
BIN = r"D:\hipercool-videos\bin"
if BIN not in sys.path:
    sys.path.insert(0, BIN)
os.chdir(r"D:\hipercool-videos")

def main():
    if len(sys.argv) < 2:
        print("", end="")
        return 1
    path = sys.argv[1]
    if not os.path.isfile(path):
        print("", end="")
        return 1
    try:
        with open(path, "rb") as f:
            audio = f.read()
    except Exception:
        print("", end="")
        return 1
    if len(audio) < 1000:   # audio vazio/silencio
        print("", end="")
        return 0
    ext = os.path.splitext(path)[1].lower()
    mime = {"wav": "audio/wav", "mp3": "audio/mp3", "ogg": "audio/ogg",
            "m4a": "audio/mp4", "flac": "audio/flac"}.get(ext.lstrip("."), "audio/wav")
    try:
        import gemini_llm
        txt = gemini_llm.transcribe_audio(audio, mime=mime, max_tokens=1024, temperature=0.2)
    except Exception as e:
        sys.stderr.write(f"erro: {e}\n")
        print("", end="")
        return 1
    if txt:
        # Uma linha, sem aspas nas pontas
        txt = txt.strip().strip('"').strip()
        sys.stdout.write(txt)
    return 0

if __name__ == "__main__":
    sys.exit(main())
