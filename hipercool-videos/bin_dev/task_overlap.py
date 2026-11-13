import subprocess
import os
import glob
import sys
import datetime

def find_next_cap():
    done_caps = set([1, 11]) # 1 and 11 are explicitly skipped as they are done
    
    # Check night_shift logs to see what's being processed
    try:
        with open("logs/night-shift.md", "r", encoding="utf-8") as f:
            log_content = f.read()
            for i in range(2, 89):
                if f"_CAP{i:02d}_" in log_content:
                    done_caps.add(i)
    except:
        pass
        
    for i in range(2, 89):
        if i not in done_caps:
            return i
    return None

def main():
    print(f"[{datetime.datetime.now()}] Iniciando task overlap.")
    
    # 1: CHECAGEM DO GARGALO GEMINI (PIPELINE DE IA)
    tasklist = subprocess.run(["wmic", "process", "where", "commandline like '%hiper-pipeline.py%'", "get", "commandline"], capture_output=True, text=True)
    if "hiper-pipeline.py" in tasklist.stdout and tasklist.stdout.count("hiper-pipeline.py") > 1:
        # > 1 because this script itself might trigger a match if it were checking broadly, but let's be safe:
        # if any hiper-pipeline is running, abort to protect Gemini
        print("Pipeline hiper-pipeline.py ja esta rodando! Abortando ciclo.")
        with open("logs/night-shift.md", "a", encoding="utf-8") as f:
            f.write(f"\n- [{datetime.datetime.now()}] Pipeline IA hiper-pipeline.py rodando. Aguardando próximo ciclo.\n")
        return

    # 2: FILA - Achar o menor CAPNN que falta
    next_cap = find_next_cap()
    if not next_cap:
        print("Nenhum capítulo pendente encontrado!")
        return
        
    cap_str = f"{next_cap:02d}"
    print(f"Capítulo alvo: {cap_str}")
    
    # 3: GERAÇÃO
    cmd = (
        f"set PYTHONUTF8=1 && "
        f"set TTS_ENGINE=gemini && "
        f"set PANEL_FX=1 && "
        f"set GEMINI_TTS_PROXY_ENABLED=1 && "
        f"set CENSURA_BRANCO_VAR=B2 && "
        f"\"D:\\hipercool-videos\\venv\\Scripts\\python.exe\" bin/hiper-pipeline.py "
        f"--panels-dir workspace/panels/regressed-warriors-cap{cap_str} "
        f"--titulo \"O Guerreiro Regressou — Capitulo {next_cap}\" "
        f"--narrator-gender M --max-panels 120 --subtitles --karaoke --censura --skip-notify "
        f"--output-suffix _CAP{cap_str} > logs/warrior_cap{cap_str}_producao.log 2>&1"
    )
    
    # Disparar background task
    print(f"Disparando: {cmd}")
    subprocess.Popen(cmd, shell=True)
    
    # 4: REGISTRO
    with open("logs/night-shift.md", "a", encoding="utf-8") as f:
        f.write(f"\n- [{datetime.datetime.now()}] Iniciada geração do _CAP{cap_str}_ (pipeline de voz/ia ativo em lote paralelo com qualquer ffmpeg renderizando).\n")

if __name__ == "__main__":
    main()
