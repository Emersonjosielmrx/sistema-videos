"""Lanca os Chromes CDP de forma persistente (desacoplado do processo pai)"""
import subprocess, os

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILES = {
    9222: "canalalucinaai",
    9271: "jornalcomia",
}
FLAGS = "--no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1280,800 --window-position=-2000,0"

for port, profile in PROFILES.items():
    cmd = f'"{CHROME}" --remote-debugging-port={port} --user-data-dir="D:\logins-google\chrome-profiles\{profile}" {FLAGS} about:blank'
    subprocess.Popen(
        cmd,
        shell=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print(f"Launched {profile} on port {port}")
