# -*- coding: utf-8 -*-
# Roda no PC1 (somente leitura): testa se o filtro de palavrao da postagem (postar_longos.py) pega
# o NOME dos memes novos, que o anime-pipeline escreve no pipeline.log.
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ARQ = Path(r"D:\recapd-ambientes\producao\colab\postar_longos.py")
linhas = ARQ.read_text(encoding="utf-8").splitlines()
ini = next(i for i, l in enumerate(linhas) if l.startswith("_PALAVRAO = re.compile("))
fim, aberto = ini, 0
while True:
    aberto += linhas[fim].count("(") - linhas[fim].count(")")
    if aberto <= 0:
        break
    fim += 1
bloco = "\n".join(linhas[ini:fim + 1])
print(f"regex em postar_longos.py:{ini + 1}-{fim + 1}")
ns = {"re": re}
exec(bloco, ns)  # so a atribuicao do _PALAVRAO
rx = ns["_PALAVRAO"]

nomes = ["21_ai_que_delicia_cara", "22_ai_ai_ai_nada_eu_curto", "23_xaropinho_rapaz", "24_que_deselegante",
         "25_receba", "26_que_ota", "27_meu_deus_do_ceu_nao_sobrou_nada", "28_socorro",
         "29_ta_tranquilo_ta_favoravel", "30_nao_entendi_foi_nada", "31_mas_que_porra_e_essa",
         "32_e_o_pix_nada", "33_ai_papai_devagar_pai", "34_meu_deus_so_besteira", "35_som_boom_dramatico",
         "36_som_explosao", "37_som_game_over"]
ruins = 0
for n in nomes:
    linha = f"[longo] 9 meme(s) visual(is) em tela cheia: frase 18: {n}.mp4, frase 40: 01_ah_agora_eu_entendi.mp4"
    achou = sorted({m.group(0).lower() for m in rx.finditer(linha)})
    if achou:
        ruins += 1
    print(f"{n:42} {'PEGA: ' + str(achou) if achou else 'ok'}")
print("controle (deve pegar):", sorted({m.group(0).lower() for m in rx.finditer('ele disse: que porra e essa')}))
print("nomes que o filtro pegaria:", ruins)
