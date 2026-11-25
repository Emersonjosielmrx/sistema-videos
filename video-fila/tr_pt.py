import sys, types, subprocess, tempfile, pathlib
sys.modules["hp_common"] = types.SimpleNamespace(log=lambda *a, **k: None)
sys.path.insert(0, r"D:\hipercool-materiais\comum")
import groq_api
for f in sys.argv[1:]:
    t = pathlib.Path(tempfile.mkdtemp()) / "a.mp3"
    subprocess.run([r"D:\hipercool-materiais\bin\ffmpeg.exe", "-nostdin", "-loglevel", "error", "-y", "-i", f, "-vn",
                    "-ac", "1", "-ar", "16000", str(t)])
    j = groq_api.transcrever(str(t), idioma="pt", palavras=False) or {}
    print(pathlib.Path(f).name[:40], "|", j.get("text"), flush=True)
