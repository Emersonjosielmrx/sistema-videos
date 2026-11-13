import sys
from pathlib import Path

BASE = Path("D:/recapd-ambientes/producao/workspace/anime")

def scan():
    arquivos_analisados = 0
    erros = {
        "filler_IA": [],
        "formatacao_roteiro": [],
        "vazio": [],
        "muito_curto": [],
    }

    for work_dir in BASE.iterdir():
        if not work_dir.is_dir(): continue
        
        roteiro_file = work_dir / "roteiro.txt"
        if not roteiro_file.exists(): continue
        
        arquivos_analisados += 1
        texto = roteiro_file.read_text(encoding="utf-8")
        linhas = texto.splitlines()
        
        if not linhas or len(texto.strip()) == 0:
            erros["vazio"].append(work_dir.name)
            continue
            
        if len(linhas) < 3:
            erros["muito_curto"].append((work_dir.name, len(linhas)))
            
        texto_lower = texto.lower()
        
        # 1. Filler de IA (introdução ou conclusão da IA)
        fillers = ["aqui está", "espero que goste", "roteiro reescrito", "claro, aqui", "com certeza!", "aqui vai"]
        for f in fillers:
            if f in texto_lower[:200] or f in texto_lower[-200:]:
                erros["filler_IA"].append(work_dir.name)
                break
                
        # 2. Formatação de roteiro (tags da IA como [Música], Narrador:, Cena:)
        if "[música" in texto_lower or "[risos" in texto_lower or "[" in texto_lower:
            # muitas vezes usa colchetes pra efeitos sonoros
            erros["formatacao_roteiro"].append(work_dir.name)
        elif "narrador:" in texto_lower or "narração:" in texto_lower or "cena:" in texto_lower:
            erros["formatacao_roteiro"].append(work_dir.name)

    print(f"Analisados {arquivos_analisados} roteiros.")
    print("\n=== VAZIOS ===")
    for e in erros["vazio"]: print(f" - {e}")
    print("\n=== MUITO CURTOS (< 3 linhas) ===")
    for e, num in erros["muito_curto"]: print(f" - {e} ({num} linhas)")
    print("\n=== FILLER DE IA ===")
    for e in erros["filler_IA"]: print(f" - {e}")
    print("\n=== FORMATACAO INDESEJADA ([tags], Narrador:) ===")
    for e in set(erros["formatacao_roteiro"]): print(f" - {e}")

if __name__ == "__main__":
    scan()
