"""Varre os perfis do cofre e diz em quais o FACEBOOK já está logado (cookie c_user), SEM abrir Chrome nem internet:
lê o banco de cookies de cada perfil no disco. Para montar a lista de contas de FB que já existem.
    python fb_varrer_logados.py
"""
import glob, json, os, sqlite3, sys, tempfile, shutil
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZES = [r"D:\logins-google\cofre\perfis", r"D:\logins-google\chrome-profiles"]


def c_user(cookie_db):
    """Lê c_user do Cookies sqlite (cópia, porque o Chrome trava o arquivo)."""
    tmp = Path(tempfile.gettempdir()) / f"ck_{os.getpid()}_{os.path.basename(os.path.dirname(cookie_db))}.db"
    try:
        shutil.copy2(cookie_db, tmp)
        con = sqlite3.connect(str(tmp))
        # o valor vem criptografado (encrypted_value); basta existir o c_user com conteúdo = está/esteve logado
        row = con.execute("SELECT length(encrypted_value) FROM cookies WHERE host_key LIKE '%facebook.com' "
                          "AND name='c_user' LIMIT 1").fetchone()
        con.close()
        return "logado" if row and row[0] and row[0] > 3 else None
    except Exception:
        return None
    finally:
        tmp.unlink(missing_ok=True)


achados = []
for raiz in RAIZES:
    for ckdb in glob.glob(os.path.join(raiz, "*", "Default", "Network", "Cookies")) + \
            glob.glob(os.path.join(raiz, "*", "Default", "Cookies")):
        perfil = Path(ckdb).parts[len(Path(raiz).parts)]
        uid = c_user(ckdb)
        if uid:
            achados.append((perfil, uid))
print(f"{len(achados)} perfis com Facebook logado:")
for perfil, uid in sorted(achados):
    print(f"  {perfil:30} c_user {uid}")
