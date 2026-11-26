# D:\video-fila\ronda_avisar.py  (copia mestre: /mnt/win-bootcamp/claude-central/ronda/ronda_avisar.py)
# Manda pelo Telegram (portao unico avisos.py, que ja tira repetidos) o texto de um arquivo.
# Uso: python ronda_avisar.py <arquivo.txt> [origem]
import sys
sys.path.insert(0, r"D:\video-fila")
import avisos
texto = open(sys.argv[1], encoding="utf-8").read().strip()
if texto:
    avisos.enviar(texto[:3500], sys.argv[2] if len(sys.argv) > 2 else "ronda-geral", importante=True)
