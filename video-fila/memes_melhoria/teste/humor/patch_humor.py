# -*- coding: utf-8 -*-
# PC1: liga humor_narrador.polir no roteiro LONGO novo (antes de gravar no cache). Backup, tudo-ou-nada, idempotente.
#   python patch_humor.py <anime_script.py>
import shutil, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
alvo = Path(sys.argv[1])
VELHO = '''    frases, tempos = _tirar_abertura_vazia(frases, tempos)
    logging.info(f"[script] roteiro longo com tempo: {len(frases)} frases ({sem_marca} bloco(s) sem marca, "'''
NOVO = '''    frases, tempos = _tirar_abertura_vazia(frases, tempos)
    # 26/11 dona ("elementos dos vídeos do Virjão/Momo que ainda não tem; analise e implemente"): o narrador REAGE ao
    # vivo (1ª pessoa, pergunta incrédula, interjeição, '!', piada de virada, piada recorrente), sem comentário repetido
    # e sem "nosso garoto" em toda frase. Só em roteiro NOVO (o do cache não muda). bin/humor_narrador.py;
    # HUMOR_POLIR=0 desliga tudo (chaves de cada passo no topo do arquivo).
    if os.environ.get("HUMOR_POLIR", "1") != "0":
        try:
            import humor_narrador
            frases, tempos = humor_narrador.polir(frases, tempos)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[script] passada de humor falhou ({type(e).__name__}: {e}) — roteiro segue sem ela")
    logging.info(f"[script] roteiro longo com tempo: {len(frases)} frases ({sem_marca} bloco(s) sem marca, "'''
dados = alvo.read_bytes(); crlf = b"\r\n" in dados
txt = dados.decode("utf-8").replace("\r\n", "\n")
if "humor_narrador.polir" in txt:
    print("ja aplicado"); sys.exit(0)
if txt.count(VELHO) != 1:
    print("ERRO ancora", txt.count(VELHO)); sys.exit(1)
if "\nimport os" not in txt:
    print("ERRO: anime_script sem import os"); sys.exit(1)
txt = txt.replace(VELHO, NOVO)
compile(txt, alvo.name, "exec")
bk = alvo.with_name(alvo.name + ".antes_humor_26nov")
if not bk.exists():
    shutil.copy2(alvo, bk)
alvo.write_bytes((txt.replace("\n", "\r\n") if crlf else txt).encode("utf-8"))
print("patch ok:", alvo, "| backup:", bk.name)
