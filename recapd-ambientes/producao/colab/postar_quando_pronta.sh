#!/usr/bin/env bash
# 12/11 dona: "Medieval 13 tem que postar já público e me avisar assim que postar". Espera a ficha da parte 13 aparecer
# pronta (na_nuvem/PReloN5HWSI*/nuvem.json) e posta NA HORA (--so, sem intervalo VIP e com 3 longos/dia liberados).
cd /d/recapd-ambientes/producao/colab
until ls "/d/hipercool-materiais/animes recap/na_nuvem/" | grep -q "^PReloN5HWSI"; do sleep 300; done
LONGOS_POR_DIA=9 /d/recapd-ambientes/producao/venv/Scripts/python.exe -X utf8 postar_longos.py --so PReloN5HWSI
