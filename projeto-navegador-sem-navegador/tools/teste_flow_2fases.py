# -*- coding: utf-8 -*-
"""Prova do vídeo do Veo em 2 fases numa máquina (D31): pede (Chrome ~40 s), solta a vez, baixa sem Chrome.
Uso: python tools\teste_flow_2fases.py <maquina> <perfil> <saida.mp4>"""
import json
import sys
import time

sys.path.insert(0, r"D:\postador-de-videos\bin")
import maquina_remota as mr  # noqa: E402

maq, perfil, saida = sys.argv[1:4]
proj = json.load(open(r"D:\veo\beta\logs\flow_projetos.json", encoding="utf-8"))[perfil]
prompt = "A golden retriever puppy runs through autumn leaves in a park, slow motion, cinematic, vertical 9:16, 8 seconds"
t0 = time.time()
marcas = {}
ordem = mr.tentativas([maq], perfil, log_fn=lambda m: print(m, flush=True))
try:
    for rem in ordem:
        if rem is None:
            print("NENHUMA maquina livre", flush=True)
            break
        def soltar():
            marcas["solta_em"] = round(time.time() - t0)
            print(f"VEZ SOLTA em {marcas['solta_em']} s (Chrome fechado; máquina livre para outro trabalho)", flush=True)
        r = rem.nsn_flow_video_2fases(perfil, proj, prompt, saida, soltar=soltar, log_fn=lambda m: print(m, flush=True))
        print("RESULTADO", json.dumps(r, ensure_ascii=False), flush=True)
        break
finally:
    ordem.close()
print(f"fim em {round(time.time() - t0)} s; vez solta em {marcas.get('solta_em')} s", flush=True)
