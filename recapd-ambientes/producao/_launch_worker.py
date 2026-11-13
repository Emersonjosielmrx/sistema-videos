import subprocess, os
subprocess.Popen(
    [r"C:\recapd-e-animes\venv\Scripts\python.exe",
     r"C:\recapd-e-animes\bin\anime_worker_loop.py"],
    cwd=r"C:\recapd-e-animes",
    env={**os.environ, "PYTHONUTF8": "1"},
    stdout=open(r"C:\recapd-e-animes\workspace\loop_stdout.log", "a"),
    stderr=subprocess.STDOUT
)
