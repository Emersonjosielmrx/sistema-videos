import subprocess
import time

while True:
    try:
        print("Rodando checkup de postagem de shorts de animes(recapd-e-animes)...")
        subprocess.run(["python", "/d/recapd-ambientes/producao/bin/postar_animes.py"])
        # Espera 1 hora e 10 min
        time.sleep(4200)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Erro no auto post: {e}")
        time.sleep(600)
