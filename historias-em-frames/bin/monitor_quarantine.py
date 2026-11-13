import os
import json
from pathlib import Path
from datetime import datetime

def main():
    from hp_common import QUARANTINE_DIR
    quarantine_dir = QUARANTINE_DIR  # em hipercool-materiais
    if not quarantine_dir.exists():
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        print("Quarantine dir created.")
        return

    files = list(quarantine_dir.glob("*.mp4"))
    log_file = Path(r"D:\historias-em-frames\logs\quarantine_report.md")
    
    report = [f"## Relatório de Quarentena - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    report.append(f"Total de vídeos em quarentena: {len(files)}")
    
    if files:
        report.append("\n**Vídeos recentes:**")
        # Mostrar os 5 mais recentes
        files.sort(key=os.path.getmtime, reverse=True)
        for f in files[:5]:
            size_mb = f.stat().st_size / (1024 * 1024)
            time_str = datetime.fromtimestamp(f.stat().st_mtime).strftime('%H:%M:%S')
            report.append(f"- {f.name} ({size_mb:.1f} MB, modificado às {time_str})")
            
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n\n")

    print(f"Quarantine checked: {len(files)} files found.")

if __name__ == "__main__":
    main()
