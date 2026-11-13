"""Loop infinito que chama run() ate ser morto manualmente.
Use: python loop_cron.py
Para parar: Ctrl+C ou kill o processo.
"""
import sys, os, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cron_gerar_video_llm import run

if __name__ == "__main__":
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] loop_cron iniciado", flush=True)
    i = 0
    while True:
        i += 1
        try:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] === Ciclo {i} ===", flush=True)
            run()
        except KeyboardInterrupt:
            print("\n[loop_cron] Ctrl+C, parando", flush=True)
            break
        except Exception as e:
            print(f"[loop_cron] erro: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
        # Pausa entre ciclos (evita spam se run retornar rapido)
        time.sleep(30)
