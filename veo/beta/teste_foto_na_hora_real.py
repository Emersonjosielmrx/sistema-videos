r"""Prova real da foto na hora (0 credito no Nano Banana 2.1): as maquinas vem da CADEIA de verdade, como o cron faz
(PC1 so entra sem pausa de carga e com RAM; notebook so sem telao; desktop so ocioso). Nao gera video, nao posta.
Uso: D:\veo\venv\Scripts\python.exe -X utf8 teste_foto_na_hora_real.py  (24/10)"""
import json, sys, time
sys.path.insert(0, r"D:\veo\beta")
import cadeia_veo
import foto_na_hora as fh

import cron_gerar_video_llm as cron
import recursos
carga = bool(cron.sistema_pausado() and cron._pausa_por_carga())
ram = recursos.slots_por_recurso() >= 1
print("estado real do PC1: pausa de carga =", carga, "| RAM p/ Chrome =", ram, "|", recursos.resumo())
etapas, fora = cadeia_veo.cadeia(pausa_carga=carga, pc1_tem_ram=ram)
print("[cadeia]", cadeia_veo.resumo(etapas, fora))
maqs = list(dict.fromkeys(m for _n, ms in etapas for m in ms)) if etapas else []
print("maquinas passadas a foto:", maqs)
if not maqs:
    print("nenhuma maquina livre agora - o cron nem montaria o prompt; fim do teste")
    sys.exit()
t0 = time.time()
r = fh.gerar("rooftop of a city at sunset, warm golden light, skyline behind",
             "The person in the frame smiles and talks directly to camera on a rooftop at sunset, 9:16 vertical portrait.",
             tag="teste_maquinas", maquinas=maqs)
print("RESULTADO:", r, f"({time.time() - t0:.0f} s)")
regs = [json.loads(l) for l in open(fh.REGISTRO, encoding="utf-8") if '"teste_maquinas"' in l]
for x in regs[-3:]:
    print({k: x.get(k) for k in ("tentativa", "arquivo", "aprovada", "nota", "motivo", "erro", "maquinas", "refs", "s")})
