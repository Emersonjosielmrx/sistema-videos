# -*- coding: utf-8 -*-
"""Prova D30 (imagem): UMA imagem do Flow gerada por HTTP numa máquina remota pelo caminho do gera_imagem.
Uso: python teste_flow_http_imagem.py <maquina> <sessao> <saida.png>"""
import json
import sys
import time

sys.path.insert(0, r"D:\flow-imagens")
sys.path.insert(0, r"D:\veo\beta")
sys.path.insert(0, r"D:\postador-de-videos\bin")
import gera_imagem  # noqa: E402
import maquina_remota as mr  # noqa: E402

maq, sessao, saida = sys.argv[1:4]
prompt = "Vertical realistic photo of a small solar-powered lantern on a wooden table at dusk, warm light, no text, no logos"
t0 = time.time()
ordem = mr.tentativas([maq], sessao, log_fn=lambda m: print(m, flush=True))
try:
    for rem in ordem:
        if rem is None:
            print("NENHUMA maquina livre", flush=True)
            break
        r = gera_imagem._gerar_http_remoto(rem, sessao, prompt, [saida], [], "9:16", "Nano Banana 2.1", lambda m: print(m, flush=True))
        print("RESULTADO", json.dumps([str(x) for x in (r or [])]), flush=True)
        break
finally:
    ordem.close()
print(f"fim em {round(time.time() - t0)} s", flush=True)
