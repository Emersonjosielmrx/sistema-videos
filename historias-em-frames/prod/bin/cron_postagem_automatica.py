import subprocess
import time

while True:
    try:
        print("Rodando checkup de postagem de curtas (historias-em-frames)...")
        subprocess.run(["python", "/d/historias-em-frames/bin/postar_historias.py"])
        # Espera 1 hora 
        time.sleep(3600)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Erro no auto post: {e}")
        time.sleep(600)
