import sys
from pathlib import Path
import shutil

BASE = Path("D:/recapd-ambientes/producao/workspace/anime")

def audit_videos():
    analisados = 0
    apagados = 0
    
    for work_dir in BASE.iterdir():
        if not work_dir.is_dir(): continue
        analisados += 1
        
        # O video gerado final e o short. Se existem, significa que terminou 
        # o pipeline inteiro e renderizou algo.
        video_deitado = work_dir / "final_anime_deitado.mp4"
        video_short = work_dir / "final_anime_short.mp4"
        
        # A pasta tem só o vídeo original? (arquivos *.mp4 que nao sao os finais)
        all_mp4s = list(work_dir.glob("*.mp4"))
        
        # Se nao gerou os videos do sistema, isso significa que travou pela metade!
        # Isso gera pastas ocupando espaço que só tem o MP4 original, ou lixo.
        is_unfinished = not video_deitado.exists() and not video_short.exists()
        
        if is_unfinished:
            # Não tem vídeo final nosso. A pasta ficou parada e é lixo ocupando os 300 megas.
            print(f"LIXO DETECTADO (Processo abortou/só tem vídeos originais): {work_dir.name}")
            shutil.rmtree(work_dir)
            apagados += 1
        else:
            # Tem os videos do sistema. Outro cenario (mais raro): só ter o deitado
            # mas nao ter apagado o original se o roteiro travou parcial. 
            # O _cleanup_workspace já deve apagar. Se existirem mp4s sobrando aqui, é pq cleanup falhou.()
            sobras = [v for v in all_mp4s if v.name not in ["final_anime_deitado.mp4", "final_anime_short.mp4"]]
            if sobras:
               print(f"Pasta {work_dir.name} possui sobras do original! Apagando as sobras...")
               for sobra in sobras:
                   sobra.unlink()
                   
    print(f"\nAuditoria concluída! Analisei {analisados} pastas.")
    print(f"Apaguei permanentemente {apagados} pastas inacabadas/travadas liberando o espaço.")

if __name__ == "__main__":
    audit_videos()
