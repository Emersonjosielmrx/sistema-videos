# -*- coding: utf-8 -*-
"""Runner autonomo da Fabrica Viral - roda em background, loga tudo."""
import sys, os, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.makedirs('logs', exist_ok=True)

LOG = open('logs/fabrica_viral.log', 'a', encoding='utf-8', buffering=1)

def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    LOG.write(line + '\n')

log('=== FABRICA VIRAL LOOP INICIADO ===')

from orquestrador import gerar_um
from db_local import get_stats
from painel import start_painel

# Inicia painel web
start_painel(background=True)
log('Painel web rodando na porta 8800')

MAX_ERROS_SEQ = 5
erros_seq = 0
INTERVALO = 120  # 2min entre geracoes

while True:
    try:
        stats = get_stats()
        log(f'Stats: done={stats[done]} pending={stats[pending]} errors={stats[errors]}')
        result = gerar_um()
        if result:
            log(f'SUCESSO: {result[titulo][:60]} -> {result[video_path]}')
            erros_seq = 0
        else:
            log('Falha nesta iteracao')
            erros_seq += 1
    except Exception as e:
        log(f'ERRO: {e}')
        traceback.print_exc(file=LOG)
        erros_seq += 1

    if erros_seq >= MAX_ERROS_SEQ:
        log(f'PAUSA: {MAX_ERROS_SEQ} erros seguidos, esperando 10min')
        time.sleep(600)
        erros_seq = 0
    else:
        log(f'Aguardando {INTERVALO}s...')
        time.sleep(INTERVALO)
