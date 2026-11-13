"""Relança motor e bots_conversa como o vigia_geral faz (sem janela + fora do job)."""
import subprocess
for nome in ("melhoria_continua", "bots_conversa"):
    cmd = ["cmd.exe", "/c", rf"D:\veo\venv\Scripts\python.exe D:\video-fila\{nome}.py --rodar 39 >> "
           rf"D:\video-fila\logs\{nome}_saida.log 2>&1"]
    for flags in (0x08000000 | 0x01000000, 0x08000000):
        try:
            subprocess.Popen(cmd, creationflags=flags, close_fds=True)
            print(nome, "disparado", hex(flags))
            break
        except OSError as e:
            print(nome, "falhou", e)
