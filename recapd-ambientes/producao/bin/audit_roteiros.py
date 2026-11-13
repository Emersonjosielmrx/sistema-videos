import sys
from pathlib import Path
import shutil

BASE = Path("D:/recapd-ambientes/producao/workspace/anime")

# Palavras que a IA usa quando recusa fazer o roteiro ou quando a transcrição estava vazia
SINAIS_DE_RECUSA = [
    "transcrição enviada está incompleta",
    "contém apenas ruído",
    "por favor, envie",
    "esqueceu de incluir",
    "cole o texto",
    "[erro: lixo]",
    "não há texto",
    "parece que a transcrição",
    "não posso criar",
    "não posso gerar"
]

def audit():
    apagados = 0
    analisados = 0
    for work_dir in BASE.iterdir():
        if not work_dir.is_dir(): continue
        
        roteiro_file = work_dir / "roteiro.txt"
        if not roteiro_file.exists(): continue
        
        analisados += 1
        try:
            texto = roteiro_file.read_text(encoding="utf-8").lower()
            
            # Se a IA recusou
            if any(sinal in texto for sinal in SINAIS_DE_RECUSA):
                print(f"LIXO DETECTADO (Recusa da IA): {work_dir.name}")
                print(f"   -> Trecho: {texto[:100].replace(chr(10), ' ')}...")
                
                # Apagar a pasta inteira
                shutil.rmtree(work_dir)
                apagados += 1
                
        except Exception as e:
            print(f"Erro ao ler {roteiro_file}: {e}")

    print(f"\nAuditoria concluída! Analisei {analisados} roteiros.")
    print(f"Apaguei {apagados} pastas corrompidas e liberei o espaço.")

if __name__ == "__main__":
    audit()
