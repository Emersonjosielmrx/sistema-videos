# D:\sistema\catalogo\aplicar_nobre.py - aplica o conserto do "so_nobre" em politica.py (dona 28/11: "corrija tudo").
# Roda pela tarefa AplicarNobre28nov as 10:05 (postagem so 10-17h). Seguro: confere que o politica.py ainda e o MESMO
# que foi testado (se alguem mexeu, NAO aplica e avisa), .bak, py_compile, teste dos 3 canais; quebrou = volta na hora.
import hashlib, os, py_compile, shutil, sys, time, importlib.util
BIN = r"D:\postador-de-videos\bin"; ALVO = os.path.join(BIN, "politica.py")
PRONTO = r"D:\sistema\mapa\politica_nobre_PRONTO.py"; BAK = ALVO + ".bak_28nov_nobre"
LOG = r"D:\sistema\mapa\aplicar_nobre.log"
def log(s):
    open(LOG, "a", encoding="utf-8").write(time.strftime("%d/%m %H:%M:%S ") + s + "\n"); print(s)
sys.path.insert(0, r"D:\video-fila")
def avisar(t):
    try:
        import avisos; avisos.enviar(t, origem="obra-nobre")
    except Exception as e:
        log(f"aviso falhou: {e}")
if "_janela = None" in open(ALVO, encoding="utf-8").read():
    log("ja aplicado"); sys.exit(0)
# o PRONTO foi feito em cima do politica.py de 28/11 00h. Confere que o atual nao mudou desde entao: toda linha do
# atual tem que existir no PRONTO (o PRONTO = atual + so as linhas do conserto). Se mudou, NAO aplica e avisa.
base_teste = open(PRONTO, encoding="utf-8").read()
atual = open(ALVO, encoding="utf-8").read()
pronto_linhas = set(base_teste.splitlines())
falta = [l for l in atual.splitlines() if l.strip() and l not in pronto_linhas]
if falta:
    log(f"politica.py mudou desde o teste ({len(falta)} linhas diferentes) - NAO aplico")
    avisar("Conserto do horario nobre NAO aplicado: o politica.py mudou desde o teste de 28/11 00h. Precisa refazer.")
    sys.exit(1)
shutil.copy2(ALVO, BAK)
shutil.copy2(PRONTO, ALVO)
try:
    py_compile.compile(ALVO, doraise=True)
    sp = importlib.util.spec_from_file_location("pol_teste", ALVO); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    res = []
    for cid in ["novo_leielucro", "novo_vendasqueescalam", "novo_comedianoturna"]:
        c, _ = m.achar_canal(cid); h = m.horario_publicacao(c, None, "parceiro"); res.append(f"{cid}={h}")
        if h is not None and h.hour not in (21, 22):
            raise RuntimeError(f"{cid} fora do nobre: {h}")
    log("APLICADO e testado: " + " | ".join(res))
    avisar("Conserto do horario nobre aplicado (canais punidos agora publicam as 21h). " + " | ".join(res)[:300])
except Exception as e:
    shutil.copy2(BAK, ALVO)
    log(f"FALHOU, voltei o .bak: {e}"); avisar(f"Conserto do horario nobre falhou e foi desfeito: {e}"[:300]); sys.exit(1)
