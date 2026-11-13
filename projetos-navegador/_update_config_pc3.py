"""Update PC3 config to likes-only mode and check live stats."""
import paramiko
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

def run(cmd, timeout=30):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode("utf-8", errors="replace").strip()

# Read current config
print("=== Current config ===")
out = run('powershell.exe -Command "Get-Content C:/projetos-navegador/engage_config.json"')
print(out)

# Update to likes mode with better settings
config = {
    "workers": 2,
    "sleep_min": 3,
    "sleep_max": 10,
    "batch": 500,
    "mode": "likes",
    "active_hours": [0, 23],
    "max_per_account_day": 200,
    "max_per_channel_day": 80,
    "randomize_order": True,
    "paused": False,
    "watch_time": [10, 30],
    "subscribe": False,
    "fingerprint": True,
    "organic_mode": True,
    "priority": "",
    "blacklist_channels": [],
    "blacklist_videos": [],
    "proxies": [],
    "comments_extra": []
}

sftp = ssh.open_sftp()
config_json = json.dumps(config, indent=2, ensure_ascii=False).encode("utf-8")
with sftp.open("C:/projetos-navegador/engage_config.json", "wb") as f:
    f.write(config_json)
stat = sftp.stat("C:/projetos-navegador/engage_config.json")
print(f"\nConfig updated: {stat.st_size} bytes")
sftp.close()

# Read back
out = run('powershell.exe -Command "Get-Content C:/projetos-navegador/engage_config.json"')
print(f"\n=== New config ===\n{out}")

# Stats from log
print("\n=== Stats ===")
out = run('powershell.exe -Command "(Select-String -Path C:/projetos-navegador/mega_engage_log.txt -Pattern \'OK \\[L\\]\' -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"Likes OK: {out}")

out = run('powershell.exe -Command "(Get-Content C:/projetos-navegador/mega_engage_log.txt -ErrorAction SilentlyContinue | Measure-Object -Line).Lines"')
print(f"Total log lines: {out}")

# Last 10 lines
print("\n=== Last 10 lines ===")
out = run('powershell.exe -Command "Get-Content C:/projetos-navegador/mega_engage_log.txt -Tail 10 -ErrorAction SilentlyContinue"')
print(out)

# Check progress file
print("\n=== mega_engage_progress.json exists? ===")
out = run('powershell.exe -Command "if (Test-Path C:/projetos-navegador/mega_engage_progress.json) { (Get-Item C:/projetos-navegador/mega_engage_progress.json).Length } else { \'not found\' }"')
print(f"Progress file: {out}")

ssh.close()
print("\nDone.")
