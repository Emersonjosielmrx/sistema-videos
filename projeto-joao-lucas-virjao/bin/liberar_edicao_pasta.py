"""Dá permissão de EDITOR para 'qualquer pessoa com o link' na pasta do parceiro (o rclone link só dá leitura).
Usa o token OAuth do remoto manhwa-drive do rclone.conf (o rclone renova o token em todo comando).
    python liberar_edicao_pasta.py <id_da_pasta>"""
import configparser
import json
import sys
import urllib.request
from pathlib import Path

pasta_id = sys.argv[1]
cfg = configparser.ConfigParser()
cfg.read(Path.home() / "AppData" / "Roaming" / "rclone" / "rclone.conf", encoding="utf-8")
token = json.loads(cfg["manhwa-drive"]["token"])["access_token"]
req = urllib.request.Request(
    f"https://www.googleapis.com/drive/v3/files/{pasta_id}/permissions?supportsAllDrives=true",
    data=json.dumps({"type": "anyone", "role": "writer"}).encode(), method="POST",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
print(urllib.request.urlopen(req, timeout=60).read().decode())
