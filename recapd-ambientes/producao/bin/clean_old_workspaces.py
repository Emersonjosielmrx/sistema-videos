import sys
from pathlib import Path
import shutil

BASE = Path("D:/recapd-ambientes/producao/workspace/anime")
keep_files = {"final_anime_deitado.mp4", "final_anime_short.mp4", "roteiro.txt"}

def clean():
    count = 0
    size_freed = 0
    for work_dir in BASE.iterdir():
        if not work_dir.is_dir(): continue
        
        # Check if this directory has a final mp4
        has_final = (work_dir / "final_anime_deitado.mp4").exists() or (work_dir / "final_anime_short.mp4").exists()
        
        # Or if it's already finished but has junk left over
        if has_final:
            print(f"Limpando {work_dir.name}...")
            for item in work_dir.iterdir():
                if item.name not in keep_files:
                    # accumulate size
                    try:
                        if item.is_file():
                            size_freed += item.stat().st_size
                            item.unlink()
                        elif item.is_dir():
                            dir_size = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                            size_freed += dir_size
                            shutil.rmtree(item)
                    except Exception as e:
                        pass
            count += 1
            
    print(f"\nLimpos {count} diretórios. Espaço liberado: {size_freed / (1024*1024):.2f} MB")

if __name__ == "__main__":
    clean()
