"""limpar_shots.py — faxina dos prints de logs\\yt_web (22/10, P06).

O youtube_web_poster tira ~3 prints por upload (1_detalhes/2_visibilidade/3_final) e mais os de falha/checagem;
ninguém apagava nada: em 22/10/2026 eram 2.269 arquivos / 393 MB. Regra:
  - print de SUCESSO (1_*/2_*/3_*) com mais de 10 dias: apaga;
  - print de falha_*/checar_* com mais de 30 dias: apaga (falha recente fica — é prova pra diagnóstico);
  - o resto (nome fora do padrão) fica.

    python bin/limpar_shots.py --simular   # só lista o que apagaria
    python bin/limpar_shots.py             # apaga e imprime o resumo

Standalone de propósito: nada chama isto automaticamente ainda (ligar no fim do limpar_usados.py quando a dona
quiser). Só mexe em logs\\yt_web; nunca em vídeo, config ou ledger.
"""
import sys
import time
from pathlib import Path

SHOTS = Path(__file__).resolve().parent.parent / "logs" / "yt_web"
DIAS_SUCESSO = 10
DIAS_FALHA = 30


def main():
    simular = "--simular" in sys.argv
    agora = time.time()
    apagar, total_mb = [], 0.0
    for p in SHOTS.glob("*.png"):
        idade_d = (agora - p.stat().st_mtime) / 86400
        nome = p.name.lower()
        sucesso = nome.split("_", 2)[-1].startswith(("1_", "2_", "3_")) or ("_1_" in nome or "_2_" in nome or "_3_" in nome)
        falha = nome.startswith(("falha_", "checar_")) or "_falha_" in nome or "_checar_" in nome
        if (sucesso and not falha and idade_d > DIAS_SUCESSO) or (falha and idade_d > DIAS_FALHA):
            apagar.append(p)
            total_mb += p.stat().st_size / 1e6
    print(f"{'[simulação] ' if simular else ''}{len(apagar)} print(s) / {total_mb:.0f} MB "
          f"(sucesso > {DIAS_SUCESSO} d, falha/checar > {DIAS_FALHA} d)")
    for p in apagar[:15]:
        print("  ", p.name)
    if len(apagar) > 15:
        print(f"   ... e mais {len(apagar) - 15}")
    if not simular:
        for p in apagar:
            try:
                p.unlink()
            except OSError:
                pass
        sobra = sum(1 for _ in SHOTS.glob("*.png"))
        print(f"apagados; sobraram {sobra} png(s)")


if __name__ == "__main__":
    main()
