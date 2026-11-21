"""Manda 'continue' no chat do Facebook (claude-d0) via o mesmo mecanismo do sentinela (Claude sem tela + SendMessage,
Gemini, não gasta Opus). Dona 21/11 ~03h: "crie crons às 3:50, 7:30 e 8:50 pra continuar após seus tokens acabarem".
Roda FORA do chat (tarefa do Windows), pra funcionar mesmo se o chat parou por falta de token.
    python fb_continuar_chat.py
"""
import sys
sys.path.insert(0, r"D:")
try:
    import sentinela_disparo as s
    nomes = ["claude-d0"]
    print("mandando continue para", nomes)
    s.enviar(nomes)
    print("ok")
except Exception as e:  # noqa: BLE001
    print("falhou:", repr(e))
