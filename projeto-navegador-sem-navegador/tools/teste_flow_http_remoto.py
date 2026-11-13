# -*- coding: utf-8 -*-
"""Prova D30: UM vídeo do Veo gerado por HTTP numa máquina remota, Chrome só para o token.
Uso: python teste_flow_http_remoto.py <maquina> <perfil> <saida.mp4>"""
import json
import sys
import time

sys.path.insert(0, r"D:\postador-de-videos\bin")
import maquina_remota as mr  # noqa: E402

maq, perfil, saida = sys.argv[1:4]
proj = json.load(open(r"D:\veo\beta\logs\flow_projetos.json", encoding="utf-8"))[perfil]
prompt = ("A friendly robot made of solar panels waves at the camera on a sunny rooftop in Brazil, cinematic, "
          "vertical 9:16, 8 seconds, include ambient sound")
print(f"maquina={maq} perfil={perfil} projeto={proj}", flush=True)
t0 = time.time()
ordem = mr.tentativas([maq], perfil, log_fn=lambda m: print(m, flush=True))
try:
    for rem in ordem:
        if rem is None:
            print("NENHUMA maquina livre", flush=True)
            break
        print(f"Chrome de {perfil} pronto no {rem.nome} em {round(time.time() - t0)} s", flush=True)
        r = rem.nsn_flow_video(perfil, proj, prompt, saida, formato="9:16", modelo="Veo 3.1 - Fast",
                               fechar_chrome=True, timeout=1800, log_fn=lambda m: print(m, flush=True))
        print("RESULTADO", json.dumps(r, ensure_ascii=False), flush=True)
        break
finally:
    ordem.close()
print(f"fim em {round(time.time() - t0)} s", flush=True)
