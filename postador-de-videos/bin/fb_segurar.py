"""Mantém o Chrome da conta aberto (pela saída fixa) por N minutos e fecha no fim. Para sessões de trabalho.
    python fb_segurar.py <conta> <minutos>"""
import sys, time
import fb_contas
porta, proc = fb_contas.abrir(sys.argv[1])
try:
    time.sleep(int(sys.argv[2]) * 60)
finally:
    fb_contas.fechar(proc)
