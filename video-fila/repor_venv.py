r"""repor_venv.py — repõe no Python central (hipercool-materiais\python\venv) só os arquivos que FALTAM segundo o
RECORD de cada pacote, copiando de outro venv quando o sha256 bate. Sem --aplicar só mostra.
(21/10: pillow e bcrypt sem arquivos depois do venv ir pro Drive e voltar; ManhwaReact-Lote falhou.)"""
import base64, csv, glob, hashlib, os, shutil, sys
ALVO = r"D:\hipercool-materiais\python\venv\Lib\site-packages"
FONTES = [r"D:\veo\venv\Lib\site-packages", r"D:\hipercool-videos\venv\Lib\site-packages",
          r"D:\recapd-ambientes\producao\venv\Lib\site-packages",
          r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\Lib\site-packages"]
FONTES += glob.glob(r"D:\*\venv\Lib\site-packages") + glob.glob(r"D:\*\.venv\Lib\site-packages")
aplicar = "--aplicar" in sys.argv
def h(p):
    return "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(open(p, "rb").read()).digest()).rstrip(b"=").decode()
os.chdir(ALVO)
ok = sem = 0
for rec in glob.glob("*.dist-info/RECORD"):
    for r in csv.reader(open(rec, encoding="utf-8")):
        if not r or r[0].startswith("..") or "__pycache__" in r[0] or os.path.exists(r[0]):
            continue
        achou = None
        for f in dict.fromkeys(FONTES):
            c = os.path.join(f, r[0])
            if os.path.normcase(os.path.realpath(f)) != os.path.normcase(os.path.realpath(ALVO)) and os.path.isfile(c) \
                    and (not r[1] or h(c) == r[1]):
                achou = c
                break
        if achou:
            ok += 1
            print(("COPIEI " if aplicar else "copiaria ") + r[0] + "  <- " + achou)
            if aplicar:
                os.makedirs(os.path.dirname(r[0]) or ".", exist_ok=True)
                shutil.copy2(achou, r[0])
        else:
            sem += 1
            print("SEM FONTE " + r[0])
print(f"repostos: {ok} | sem fonte: {sem}")
