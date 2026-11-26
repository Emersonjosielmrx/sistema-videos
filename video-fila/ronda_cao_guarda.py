# D:\video-fila\ronda_cao_guarda.py  (copia mestre: /mnt/win-bootcamp/claude-central/ronda/ronda_cao_guarda.py)
# Cao de guarda da RONDA GERAL: a ronda roda na Omarchy de hora em hora e grava a batida
# D:\video-fila\estado\ronda_batida.txt. Se a batida tiver mais de 150 min, avisa no Telegram.
# Motivo (26/11): um chat parou os timers da Omarchy e a ronda ficou parada sem ninguem saber.
# Tarefa: RondaCaoGuarda (30 em 30 min). Sem print (roda em pythonw).
import os, sys, time
sys.path.insert(0, r"D:\video-fila")
BATIDA = r"D:\video-fila\estado\ronda_batida.txt"
LIMITE_MIN = 150
idade = (time.time() - os.path.getmtime(BATIDA)) / 60 if os.path.exists(BATIDA) else 99999
if idade > LIMITE_MIN:
    import avisos
    h = "nunca rodou" if idade > 99990 else f"parada ha {idade / 60:.1f} h"
    avisos.enviar(f"VIGIA: a ronda geral da Omarchy esta {h}. Ninguem esta acompanhando os projetos. "
                  "Ligue a Omarchy ou religue: systemctl --user start ronda-geral.timer",
                  "ronda-cao-guarda", importante=True, chave="<SEGREDO_REMOVIDO>")
